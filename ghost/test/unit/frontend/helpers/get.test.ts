import assert from 'node:assert/strict';
import sinon from 'sinon';
import type { SinonSpy, SinonStub } from 'sinon';
// @ts-expect-error This module lacks type definitions.
import { SafeString } from '../../../../core/frontend/services/handlebars';
import configUtils from '../../../utils/config-utils';
import loggingLib from '@tryghost/logging';

// Stuff we are testing
// @ts-expect-error This module lacks type definitions.
import get from '../../../../core/frontend/helpers/get';
const { querySimplePath } = get;
// @ts-expect-error This module lacks type definitions.
import { endpoints as api } from '../../../../core/server/api';

describe('{{#get}} helper', function () {
  beforeAll(async function () {
    await require('../../../../core/server/services/posts-public').default.init();
  });

  let fn: SinonSpy;
  let inverse: SinonSpy;
  let locals: {
    root: { _locals?: { degradedRender?: boolean } };
    globalProp?: { foo: string };
    member?: { uuid: string };
    _queryCache?: Map<string, Promise<unknown>>;
  } = { root: {} };
  let logging: { error: SinonStub; warn: SinonStub };

  beforeEach(function () {
    fn = sinon.spy();
    inverse = sinon.spy();

    locals = { root: {}, globalProp: { foo: 'bar' } };

    // We're testing how the browse stub is called, not the response.
    // Each get call errors since the posts resource is not populated.
    logging = {
      error: sinon.stub(loggingLib, 'error'),
      warn: sinon.stub(loggingLib, 'warn'),
    };
  });

  afterEach(async function () {
    sinon.restore();
    await configUtils.restore();
  });

  describe('pagination with excluded post IDs', function () {
    const postId = (index: number) => 'a'.repeat(23) + index.toString(16);
    const posts = Array.from({ length: 10 }, (_, index) => ({
      id: postId(index + 1),
      slug: `post${index + 1}`,
      title: `Post ${index + 1}`,
      url: `/post${index + 1}/`,
      visibility: index < 9 ? 'public' : 'members',
    }));
    let browseStub: SinonStub;

    beforeEach(function () {
      browseStub = sinon
        .stub()
        .callsFake(
          async (options: {
            filter?: string;
            fields?: string;
            limit?: string | number;
            page?: string | number;
          }) => {
            const filter = String(options.filter || '');
            const excludedId = /(?:^|\+)id:-([a-f0-9]{24}|null)/i.exec(filter)?.[1];
            const selected = posts.filter(
              (post) =>
                post.id !== excludedId &&
                (!filter.includes('visibility:public') || post.visibility === 'public'),
            );
            const page = Number(options.page || 1);
            const limit = Number(options.limit || 15);
            const pages = Math.ceil(selected.length / limit) || 1;
            const paged = selected.slice((page - 1) * limit, page * limit);
            const fields = options.fields?.split(',');
            const result = fields
              ? paged.map((post) =>
                  Object.fromEntries(
                    fields.map((field) => [field, post[field as keyof typeof post]]),
                  ),
                )
              : paged;

            return {
              posts: result,
              meta: {
                pagination: {
                  page,
                  limit,
                  pages,
                  total: selected.length,
                  next: page < pages ? page + 1 : null,
                  prev: page > 1 ? page - 1 : null,
                },
              },
            };
          },
        );
      sinon.stub(api, 'postsPublic').get(() => ({ browse: browseStub }));
    });

    for (const { page, expectedSlugs } of [
      { page: undefined, expectedSlugs: ['post1', 'post2', 'post3'] },
      { page: 1, expectedSlugs: ['post1', 'post2', 'post3'] },
      { page: 2, expectedSlugs: ['post4', 'post5', 'post6'] },
      { page: 3, expectedSlugs: ['post7', 'post8', 'post9'] },
    ]) {
      it(`returns the filtered posts and pagination for page ${page ?? 'default'}`, async function () {
        await get.call({}, 'posts', {
          hash: { filter: `id:-${postId(10)}`, limit: 3, ...(page ? { page } : {}) },
          data: locals,
          fn,
          inverse,
        });

        sinon.assert.notCalled(inverse);
        const response = fn.firstCall.args[0];
        assert.deepEqual(
          response.posts.map((post: { slug: string }) => post.slug),
          expectedSlugs,
        );
        assert.deepEqual(response.meta.pagination, {
          page: page || 1,
          limit: 3,
          pages: 3,
          total: 9,
          next: (page || 1) < 3 ? (page || 1) + 1 : null,
          prev: (page || 1) > 1 ? (page || 1) - 1 : null,
        });
        assert.deepEqual(fn.firstCall.args[1].blockParams[1], response.meta.pagination);
      });
    }

    it('reports the page count for the filtered total and requested limit', async function () {
      await get.call({}, 'posts', {
        hash: { filter: `id:-${postId(10)}`, limit: 2 },
        data: locals,
        fn,
        inverse,
      });

      assert.equal(fn.firstCall.args[0].meta.pagination.total, 9);
      assert.equal(fn.firstCall.args[0].meta.pagination.pages, 5);
      assert.equal(fn.firstCall.args[0].meta.pagination.limit, 2);
    });

    it('does not subtract an excluded ID outside the rest of the filter', async function () {
      await get.call({}, 'posts', {
        hash: { filter: `id:-${postId(10)}+visibility:public`, limit: 3, page: 2 },
        data: locals,
        fn,
        inverse,
      });

      const response = fn.firstCall.args[0];
      assert.deepEqual(
        response.posts.map((post: { slug: string }) => post.slug),
        ['post4', 'post5', 'post6'],
      );
      assert.equal(response.meta.pagination.total, 9);
      assert.equal(response.meta.pagination.pages, 3);
    });

    it('excludes the post even when the requested fields omit its ID', async function () {
      await get.call({}, 'posts', {
        hash: { filter: `id:-${postId(1)}`, fields: 'title,slug', limit: 3 },
        data: locals,
        fn,
        inverse,
      });

      const response = fn.firstCall.args[0];
      assert.deepEqual(
        response.posts.map((post: { slug: string }) => post.slug),
        ['post2', 'post3', 'post4'],
      );
      assert(response.posts.every((post: { id?: string }) => post.id === undefined));
      assert.equal(response.meta.pagination.total, 9);
    });

    it('accepts a SafeString filter containing an excluded ID', async function () {
      const filter = `id:-${postId(5)}`;
      await get.call({}, 'posts', {
        hash: { filter: new SafeString(filter), limit: 3, page: 2 },
        data: locals,
        fn,
        inverse,
      });

      assert.equal(browseStub.firstCall.args[0].filter, filter);
      assert.deepEqual(
        fn.firstCall.args[0].posts.map((post: { slug: string }) => post.slug),
        ['post4', 'post6', 'post7'],
      );
      assert.equal(fn.firstCall.args[0].meta.pagination.total, 9);
    });

    it('deduplicates identical queries without mixing different pages or exclusions', async function () {
      locals = { root: {}, _queryCache: new Map() };
      for (const hash of [
        { filter: `id:-${postId(10)}`, limit: 3, page: 1 },
        { filter: `id:-${postId(10)}`, limit: 3, page: 1 },
        { filter: `id:-${postId(10)}`, limit: 3, page: 2 },
        { filter: `id:-${postId(1)}`, limit: 3, page: 1 },
      ]) {
        await get.call({}, 'posts', { hash, data: locals, fn, inverse });
      }

      assert.equal(browseStub.callCount, 3);
      assert.deepEqual(
        fn.getCall(1).args[0].posts.map((post: { slug: string }) => post.slug),
        ['post1', 'post2', 'post3'],
      );
      assert.deepEqual(
        fn.getCall(2).args[0].posts.map((post: { slug: string }) => post.slug),
        ['post4', 'post5', 'post6'],
      );
      assert.deepEqual(
        fn.getCall(3).args[0].posts.map((post: { slug: string }) => post.slug),
        ['post2', 'post3', 'post4'],
      );
    });
  });

  describe('context preparation', function () {
    const meta = { pagination: {} };

    beforeEach(function () {
      locals = { root: { _locals: {} } };

      sinon.stub(api, 'postsPublic').get(() => {
        return {
          browse: sinon
            .stub()
            .resolves({ posts: [{ feature_image_caption: '<a href="#">A link</a>' }], meta: meta }),
        };
      });
    });

    it('converts html strings to SafeString', async function () {
      await get.call({}, 'posts', { hash: {}, data: locals, fn: fn, inverse: inverse });
      sinon.assert.called(fn);
      const args = fn.firstCall.args[0];
      assert(args && typeof args === 'object');
      assert('posts' in args);

      assert(fn.firstCall.args[0].posts[0].feature_image_caption instanceof SafeString);
    });
  });

  describe('authors', function () {
    const meta = { pagination: {} };

    beforeEach(function () {
      locals = { root: { _locals: {} } };

      sinon.stub(api, 'authorsPublic').get(() => {
        return {
          browse: sinon.stub().resolves({ authors: [], meta: meta }),
        };
      });
    });

    it('browse authors', async function () {
      await get.call({}, 'authors', { hash: {}, data: locals, fn: fn, inverse: inverse });
      sinon.assert.called(fn);
      const args = fn.firstCall.args[0];
      assert(args && typeof args === 'object');
      assert('authors' in args);
      assert.deepEqual(fn.firstCall.args[0].authors, []);
      sinon.assert.notCalled(inverse);
    });
  });

  describe('newsletters', function () {
    const meta = { pagination: {} };

    beforeEach(function () {
      locals = { root: { _locals: {} } };

      sinon.stub(api, 'newslettersPublic').get(() => {
        return {
          browse: sinon.stub().resolves({ newsletters: [], meta: meta }),
        };
      });
    });

    it('browse newsletters', async function () {
      await get.call({}, 'newsletters', { hash: {}, data: locals, fn: fn, inverse: inverse });
      sinon.assert.called(fn);
      const args = fn.firstCall.args[0];
      assert(args && typeof args === 'object');
      assert('newsletters' in args);
      assert.deepEqual(fn.firstCall.args[0].newsletters, []);
      sinon.assert.notCalled(inverse);
    });
  });

  describe('general error handling', function () {
    it('should return an error for an unknown resource', async function () {
      await get.call({}, 'magic', { hash: {}, data: locals, fn: fn, inverse: inverse });
      sinon.assert.notCalled(fn);
      sinon.assert.calledOnce(inverse);
      const args = inverse.firstCall.args[1];
      assert(args && typeof args === 'object');
      assert('data' in args);
      const data = args.data;
      assert(data && typeof data === 'object');
      assert('error' in data);
      assert.equal(data.error, 'Invalid "magic" resource given to get helper');
    });

    it('should handle error from the API', async function () {
      await get.call({}, 'posts', {
        hash: { slug: 'thing!' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      sinon.assert.notCalled(fn);
      sinon.assert.calledOnce(inverse);
      const args = inverse.firstCall.args[1];
      assert(args && typeof args === 'object');
      assert('data' in args);
      const data = args.data;
      assert(data && typeof data === 'object');
      assert('error' in data);
      assert.match(data.error, /^Validation/);
    });

    it('should show warning for call without any options', async function () {
      await get.call({}, 'posts', { data: locals });
      sinon.assert.notCalled(fn);
      sinon.assert.notCalled(inverse);
    });
  });

  describe('path resolution', function () {
    let browseStub: SinonStub;
    let readStub: SinonStub;
    const pubDate = new Date();

    const resource = {
      post: {
        id: 3,
        title: 'Test 3',
        author: { slug: 'cameron' },
        tags: [{ slug: 'test' }, { slug: 'magic' }],
        published_at: pubDate,
      },
    };

    beforeEach(function () {
      browseStub = sinon.stub().resolves();
      readStub = sinon.stub().resolves();
      sinon.stub(api, 'postsPublic').get(() => {
        return {
          browse: browseStub,
          read: readStub,
        };
      });
    });

    it('appends url to narrowed fields so {{url}} keeps working on the results', async function () {
      await get.call(resource, 'posts', {
        hash: { fields: 'title,slug' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert.equal(browseStub.firstCall.args[0].fields, 'title,slug,url');
    });

    it('appends url to narrowed fields for tags', async function () {
      const tagBrowseStub = sinon.stub().resolves();
      sinon.stub(api, 'tagsPublic').get(() => {
        return { browse: tagBrowseStub };
      });

      await get.call(resource, 'tags', {
        hash: { fields: 'name,slug' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert.equal(tagBrowseStub.firstCall.args[0].fields, 'name,slug,url');
    });

    it('leaves fields alone when url is already requested', async function () {
      await get.call(resource, 'posts', {
        hash: { fields: 'title,url' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert.equal(browseStub.firstCall.args[0].fields, 'title,url');
    });

    it('does not add a fields option when none was given', async function () {
      await get.call(resource, 'posts', { hash: {}, data: locals, fn: fn, inverse: inverse });
      assert.equal(browseStub.firstCall.args[0].fields, undefined);
    });

    it('should resolve post.tags alias', async function () {
      await get.call(resource, 'posts', {
        hash: { filter: 'tags:[{{post.tags}}]' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert(Array.isArray(browseStub.firstCall.args));
      assert.equal(browseStub.firstCall.args.length, 1);
      const options = browseStub.firstCall.args[0];
      assert(options && typeof options === 'object');
      assert('filter' in options);
      assert.equal(options.filter, 'tags:[test,magic]');
    });

    it('should resolve post.author alias', async function () {
      await get.call(resource, 'posts', {
        hash: { filter: 'author:{{post.author}}' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert(Array.isArray(browseStub.firstCall.args));
      assert.equal(browseStub.firstCall.args.length, 1);
      const options = browseStub.firstCall.args[0];
      assert(options && typeof options === 'object');
      assert('filter' in options);
      assert.equal(options.filter, 'author:cameron');
    });

    it('should resolve basic path', async function () {
      await get.call(resource, 'posts', {
        hash: { filter: 'id:-{{post.id}}' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert(Array.isArray(browseStub.firstCall.args));
      assert.equal(browseStub.firstCall.args.length, 1);
      const options = browseStub.firstCall.args[0];
      assert(options && typeof options === 'object');
      assert('filter' in options);
      assert.equal(options.filter, 'id:-3');
    });

    it('should handle arrays the same as handlebars', async function () {
      await get.call(resource, 'posts', {
        hash: { filter: 'tags:{{post.tags.[0].slug}}' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert(Array.isArray(browseStub.firstCall.args));
      assert.equal(browseStub.firstCall.args.length, 1);
      const options = browseStub.firstCall.args[0];
      assert(options && typeof options === 'object');
      assert('filter' in options);
      assert.equal(options.filter, 'tags:test');
    });

    it('should handle dates', async function () {
      await get.call(resource, 'posts', {
        hash: { filter: "published_at:<='{{post.published_at}}'" },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert(Array.isArray(browseStub.firstCall.args));
      assert.equal(browseStub.firstCall.args.length, 1);
      const options = browseStub.firstCall.args[0];
      assert(options && typeof options === 'object');
      assert('filter' in options);
      assert.equal(options.filter, `published_at:<='${pubDate.toISOString()}'`);
    });

    it('should output nothing if path does not resolve', async function () {
      await get.call(resource, 'posts', {
        hash: { filter: 'id:{{post.thing}}' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert(Array.isArray(browseStub.firstCall.args));
      assert.equal(browseStub.firstCall.args.length, 1);
      const options = browseStub.firstCall.args[0];
      assert(options && typeof options === 'object');
      assert('filter' in options);
      assert.equal(options.filter, 'id:');
    });

    it('should resolve global props', async function () {
      await get.call(resource, 'posts', {
        hash: { filter: 'slug:{{@globalProp.foo}}' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert(Array.isArray(browseStub.firstCall.args));
      assert.equal(browseStub.firstCall.args.length, 1);
      const options = browseStub.firstCall.args[0];
      assert(options && typeof options === 'object');
      assert('filter' in options);
      assert.equal(options.filter, 'slug:bar');
    });
  });

  describe('querySimplePath', function () {
    const data = {
      post: {
        id: 3,
        title: 'Test',
        author: { slug: 'cameron' },
        tags: [{ slug: 'test' }, { slug: 'magic' }],
        published_at: new Date('2024-01-15'),
      },
    };

    it('resolves simple dot-notation path', function () {
      assert.deepEqual(querySimplePath(data, 'post.id'), [3]);
    });

    it('resolves nested dot-notation path', function () {
      assert.deepEqual(querySimplePath(data, 'post.author.slug'), ['cameron']);
    });

    it('resolves array wildcard', function () {
      assert.deepEqual(querySimplePath(data, 'post.tags[*].slug'), ['test', 'magic']);
    });

    it('resolves numeric array index', function () {
      assert.deepEqual(querySimplePath(data, 'post.tags[0].slug'), ['test']);
      assert.deepEqual(querySimplePath(data, 'post.tags[1].slug'), ['magic']);
    });

    it('returns empty array for non-existent path', function () {
      assert.deepEqual(querySimplePath(data, 'post.nonexistent'), []);
    });

    it('returns empty array for non-existent nested path', function () {
      assert.deepEqual(querySimplePath(data, 'post.foo.bar.baz'), []);
    });

    it('returns empty array when wildcard applied to non-array', function () {
      assert.deepEqual(querySimplePath(data, 'post.title[*].slug'), []);
    });

    it('returns empty array for out-of-bounds index', function () {
      assert.deepEqual(querySimplePath(data, 'post.tags[5].slug'), []);
    });

    it('handles null in path gracefully', function () {
      assert.deepEqual(querySimplePath({ a: null }, 'a.b'), []);
    });

    it('handles Date values', function () {
      const result = querySimplePath(data, 'post.published_at');
      assert.equal(result.length, 1);
      assert(result[0] instanceof Date);
    });

    it('throws on recursive descent syntax', function () {
      assert.throws(() => querySimplePath(data, 'post..tags'), {
        message: /unsupported path segment ""/,
      });
    });

    it('throws on filter expression syntax', function () {
      assert.throws(() => querySimplePath(data, 'post.tags[?(@.slug)]'), {
        message: /unsupported path segment "tags\[\?\(@"/,
      });
    });

    it('throws on unclosed bracket', function () {
      assert.throws(() => querySimplePath(data, 'post.tags[0'), {
        message: /unsupported path segment "tags\[0"/,
      });
    });

    it('throws on non-numeric bracket content', function () {
      assert.throws(() => querySimplePath(data, 'post.tags[foo]'), {
        message: /unsupported path segment "tags\[foo\]"/,
      });
    });
  });

  describe('limit capping', function () {
    let browseStub: SinonStub;

    beforeEach(function () {
      browseStub = sinon.stub().resolves();

      sinon.stub(api, 'postsPublic').get(() => {
        return {
          browse: browseStub,
        };
      });
    });

    it('caps "all" to maxLimit (100 by default)', async function () {
      locals = { root: { _locals: {} } };
      await get.call({}, 'posts', {
        hash: { limit: 'all' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert.equal(browseStub.firstCall.args[0].limit, 100);
    });

    it('allows "all" when allowLimitAll is true', async function () {
      configUtils.set('optimization:allowLimitAll', true);

      locals = { root: { _locals: {} } };
      await get.call({}, 'posts', {
        hash: { limit: 'all' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert.equal(browseStub.firstCall.args[0].limit, 'all');
    });

    it('caps numeric limits exceeding maxLimit', async function () {
      locals = { root: { _locals: {} } };
      await get.call({}, 'posts', { hash: { limit: 150 }, data: locals, fn: fn, inverse: inverse });
      assert.equal(browseStub.firstCall.args[0].limit, 100);
    });

    it('leaves numeric limits below maxLimit unchanged', async function () {
      locals = { root: { _locals: {} } };
      await get.call({}, 'posts', { hash: { limit: 50 }, data: locals, fn: fn, inverse: inverse });
      assert.equal(browseStub.firstCall.args[0].limit, 50);
    });

    it('uses custom maxLimit when configured', async function () {
      configUtils.set('optimization:maxLimit', 50);

      locals = { root: { _locals: {} } };
      await get.call({}, 'posts', {
        hash: { limit: 'all' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert.equal(browseStub.firstCall.args[0].limit, 50);
    });

    it('caps invalid string limits to maxLimit', async function () {
      locals = { root: { _locals: {} } };
      await get.call({}, 'posts', {
        hash: { limit: 'invalid' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      assert.equal(browseStub.firstCall.args[0].limit, 100);
    });
  });

  describe('auth', function () {
    let browseStub: SinonStub;
    let member: { uuid: string };

    beforeEach(function () {
      browseStub = sinon.stub().resolves();
      member = { uuid: 'test' };

      sinon.stub(api, 'postsPublic').get(() => {
        return {
          browse: browseStub,
        };
      });
    });

    it('should pass the member context', async function () {
      locals = { root: { _locals: {} }, member };
      await get.call({}, 'posts', { hash: {}, data: locals, fn: fn, inverse: inverse });
      assert.equal(browseStub.firstCall.args[0].context.member, member);
    });
  });

  describe('optimization', function () {
    beforeEach(function () {
      sinon.stub(api, 'postsPublic').get(() => {
        return {
          browse: () => {
            return new Promise((resolve) => {
              setTimeout(() => {
                resolve({ posts: [{ id: 'abcd1234' }] });
              }, 5);
            });
          },
        };
      });
    });
    afterEach(async function () {
      await configUtils.restore();
    });

    it('should log a warning if it hits the notify threshold', async function () {
      configUtils.set('optimization:getHelper:notify:threshold', 1);

      await get.call({}, 'posts', { hash: {}, data: locals, fn: fn, inverse: inverse });

      // A log message will be output
      sinon.assert.calledOnce(logging.warn);
      // The get helper will return as per usual
      sinon.assert.calledOnce(fn);
      const args = fn.firstCall.args[0];
      assert(args && typeof args === 'object');
      assert('posts' in args);
      assert(Array.isArray(args.posts));
      assert.equal(args.posts.length, 1);
    });

    it('should log an error and return safely if it hits the timeout threshold', async function () {
      const clock = sinon.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
      try {
        configUtils.set('optimization:getHelper:timeout:threshold', 1);
        locals = { root: { _locals: {} } };

        const resultPromise = get.call({}, 'posts', {
          hash: {},
          data: locals,
          fn: fn,
          inverse: inverse,
        });
        // 2 > threshold (1), < stub's 5 — fires only the helper's timer.
        await clock.tickAsync(2);
        const result = await resultPromise;

        assert(result.toString().includes('data-aborted-get-helper'));
        assert.equal(locals.root._locals?.degradedRender, true);
        sinon.assert.calledOnce(logging.error);
        sinon.assert.calledOnce(fn);
        const args = fn.firstCall.args[0];
        assert(args && typeof args === 'object');
        assert('posts' in args);
        assert.deepEqual(args.posts, []);
        assert(!('@@ABORTED_GET_HELPER@@' in args));
      } finally {
        clock.restore();
      }
    });

    it('should return safely on timeout when _locals is not available', async function () {
      const clock = sinon.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
      try {
        configUtils.set('optimization:getHelper:timeout:threshold', 1);
        locals = { root: {} };

        const resultPromise = get.call({}, 'posts', {
          hash: {},
          data: locals,
          fn: fn,
          inverse: inverse,
        });
        await clock.tickAsync(2);
        const result = await resultPromise;

        assert(result.toString().includes('data-aborted-get-helper'));
      } finally {
        clock.restore();
      }
    });
  });

  describe('per-request deduplication', function () {
    let browseStub: SinonStub;
    const meta = { pagination: {} };

    beforeEach(function () {
      browseStub = sinon
        .stub()
        .resolves({ posts: [{ id: 'post1', title: 'Test Post' }], meta: meta });
      sinon.stub(api, 'postsPublic').get(() => {
        return {
          browse: browseStub,
        };
      });
    });

    afterEach(async function () {
      await configUtils.restore();
    });

    it('should make duplicate API calls when deduplication is disabled', async function () {
      // Deduplication disabled by default
      locals = { root: { _locals: {} } };

      // First call
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Second call with same query
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Should make two API calls since deduplication is disabled
      sinon.assert.calledTwice(browseStub);
    });

    it('should deduplicate identical queries when enabled', async function () {
      locals = { root: { _locals: {} }, _queryCache: new Map() };

      // First call
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Second call with same query
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Should only make one API call
      sinon.assert.calledOnce(browseStub);
      // But both calls should have rendered
      sinon.assert.calledTwice(fn);
    });

    it('should make separate API calls for different queries when enabled', async function () {
      locals = { root: { _locals: {} }, _queryCache: new Map() };

      // First call
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Second call with different filter
      await get.call({}, 'posts', {
        hash: { filter: 'featured:false' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Should make two API calls for different queries
      sinon.assert.calledTwice(browseStub);
    });

    it('should include member uuid in cache key', async function () {
      // Call with member A
      const localsA = {
        root: { _locals: {} },
        _queryCache: new Map(),
        member: { uuid: 'member-a' },
      };
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: localsA,
        fn: fn,
        inverse: inverse,
      });

      // Call with member B (same query but different member)
      const localsB = {
        root: { _locals: {} },
        _queryCache: localsA._queryCache,
        member: { uuid: 'member-b' },
      };
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: localsB,
        fn: fn,
        inverse: inverse,
      });

      // Should make two API calls because member context is different
      sinon.assert.calledTwice(browseStub);
    });

    it('should not cache failed API requests', async function () {
      locals = { root: { _locals: {} }, _queryCache: new Map() };

      // Set up stub to fail first, then succeed
      browseStub.onFirstCall().rejects(new Error('API Error'));
      browseStub.onSecondCall().resolves({ posts: [{ id: 'post1' }], meta: meta });

      // First call - should fail
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Second call with same query - should retry since first failed
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Should make two API calls because first one failed
      sinon.assert.calledTwice(browseStub);
    });

    it('should work without _queryCache in data', async function () {
      // No _queryCache in locals
      locals = { root: { _locals: {} } };

      // Should not throw and should make API call
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      sinon.assert.calledOnce(browseStub);
      sinon.assert.calledOnce(fn);
    });

    it('should deduplicate queries with same parameters in different order', async function () {
      locals = { root: { _locals: {} }, _queryCache: new Map() };

      // First call
      await get.call({}, 'posts', {
        hash: { filter: 'featured:true', limit: 5 },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Second call with equivalent params in different insertion order
      await get.call({}, 'posts', {
        hash: { limit: 5, filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Should only make one API call
      sinon.assert.calledOnce(browseStub);
    });

    it('should handle concurrent identical requests', async function () {
      locals = { root: { _locals: {} }, _queryCache: new Map() };

      let resolveBrowse:
        | ((value: { posts: Array<{ id: string }>; meta: typeof meta }) => void)
        | undefined;
      browseStub.callsFake(() => {
        return new Promise((resolve) => {
          resolveBrowse = resolve;
        });
      });

      const firstCall = get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });
      const secondCall = get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      // Verify deduplication while both calls are in-flight.
      sinon.assert.calledOnce(browseStub);
      assert.equal(typeof resolveBrowse, 'function');

      if (!resolveBrowse) {
        throw new Error('Expected browse resolver to be set');
      }
      resolveBrowse({ posts: [{ id: 'post1' }], meta: meta });
      await Promise.all([firstCall, secondCall]);

      // Should only make one API call even for concurrent requests
      sinon.assert.calledOnce(browseStub);
      // Both should have rendered
      sinon.assert.calledTwice(fn);
    });

    it('should not reuse the same response object instance across renders', async function () {
      locals = { root: { _locals: {} }, _queryCache: new Map() };

      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      await get.call({}, 'posts', {
        hash: { filter: 'featured:true' },
        data: locals,
        fn: fn,
        inverse: inverse,
      });

      sinon.assert.calledOnce(browseStub);
      assert.notEqual(fn.firstCall.args[0], fn.secondCall.args[0]);
    });
  });
});
