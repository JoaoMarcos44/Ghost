"""Read-only probe for PR 32434; runs its JS in a disposable Ghost sandbox.

Uses the checked-out source and installed dependencies without modifying them.
The member filter is an intentionally small SQL stand-in for Ghost's NQL
filter; the repository, member relation query, bulk plugin and serializer are
the actual checked-out modules. No HTTP server or MySQL is involved.
"""

from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(r"C:\Users\Nitro\Ghost\.worktrees\fix-member-label-removal-20261031")
PARENT = Path(r"C:\Users\Nitro\Ghost")
NODE = ROOT / "node_modules" / ".bin" / "node.exe"

JS = r"""
const assert = require('node:assert/strict');
const path = require('node:path');
const Module = require('node:module');
const root = process.env.PR_SOURCE;
const localRequire = Module.createRequire(path.join(root, 'ghost/package.json'));
localRequire('tsx/cjs/api').register();
const knex = localRequire('knex')({
  client: 'better-sqlite3',
  connection: {filename: ':memory:'},
  useNullAsDefault: true,
  pool: {min: 1, max: 1}
});
const source = p => path.join(root, ...p.split('/'));
const memberPath = source('ghost/core/server/models/member.js');
const repoPath = source('ghost/core/server/services/members/members-api/repositories/member-repository.js');
const serializerPath = source('ghost/core/server/api/endpoints/utils/serializers/output/members.js');

class BaseModel {}
BaseModel.extend = function (methods, statics) {
  class Model extends this {}
  Object.assign(Model.prototype, methods);
  Object.assign(Model, statics);
  return Model;
};
const shelf = {
  knex,
  Model: BaseModel,
  Collection: {extend: () => class Collection {}},
  model: (_name, model) => model,
  collection: (_name, collection) => collection
};
const originalLoad = Module._load;
Module._load = function (request, parent, ...rest) {
  if (parent?.filename === memberPath) {
    if (request === './base') return shelf;
    if (request.startsWith('../services/')) return {};
  }
  if (parent?.filename === repoPath && (
      request.startsWith('../../') || request === '../utils/has-active-offer' ||
      request === '@tryghost/logging' || request === '@tryghost/domain-events' ||
      request === '@tryghost/validator')) return {};
  if (parent?.filename === serializerPath &&
      (request.startsWith('./') || request.startsWith('../../'))) return {};
  return originalLoad.call(this, request, parent, ...rest);
};
require(source('ghost/core/server/models/base/plugins/bulk-operations.js'))(shelf);
const Member = require(memberPath).Member;
const MemberRepository = require(repoPath);
const serializer = require(serializerPath);
const Frame = require(source('packages/api-framework/src/frame.ts')).Frame;
const validator = require(source('packages/api-framework/src/validators/handle.ts'));
Module._load = originalLoad;
Member.transaction = callback => knex.transaction(callback);
let selectionCalls = 0;
Member.getFilteredCollectionQuery = options => {
  selectionCalls++;
  let query = knex('members');
  if (options.filter === 'has-alpha') {
    query = query.whereExists(knex('members_labels').select('id')
      .whereRaw('members_labels.member_id = members.id').where('label_id', ALPHA));
  }
  if (options.search) query = query.where('members.id', options.search);
  if (options.transacting) query = query.transacting(options.transacting);
  return query;
};
const repo = new MemberRepository({Member});
const ALPHA = 'a'.repeat(24), ZETA = 'b'.repeat(24), OTHER = 'c'.repeat(24);
const action = labels => ({action: 'removeLabels', meta: {labels: labels.map(id => ({id}))}});

async function reset() {
  await knex('members_labels').del();
  await knex('members').del();
  await knex('members').insert([{id: 'm1'}, {id: 'm2'}, {id: 'm3'}]);
  await knex('members_labels').insert([
    {id: 'r1', member_id: 'm1', label_id: ALPHA},
    {id: 'r2', member_id: 'm1', label_id: ZETA},
    {id: 'r3', member_id: 'm2', label_id: ALPHA},
    {id: 'r4', member_id: 'm2', label_id: ZETA},
    {id: 'r5', member_id: 'm3', label_id: ZETA},
    {id: 'r6', member_id: 'm3', label_id: OTHER}
  ]);
}

async function main() {
  await knex.schema.createTable('members', t => t.string('id').primary());
  await knex.schema.createTable('members_labels', t => {
    t.string('id').primary(); t.string('member_id'); t.string('label_id');
  });

  await reset();
  for (const id of [ALPHA, ZETA]) {
    await repo.bulkEdit({action: 'removeLabel', meta: {label: {id}}}, {filter: 'has-alpha'});
  }
  assert.equal((await knex('members_labels').whereIn('member_id', ['m1', 'm2'])).length, 2);
  console.log('PASS legacy two-request flow leaves two ZETA relations');

  await reset();
  selectionCalls = 0;
  const result = await repo.bulkEdit(action([ALPHA, ZETA]), {filter: 'has-alpha'});
  assert.equal(selectionCalls, 1);
  assert.equal(result.successful, 4);
  assert.deepEqual((await knex('members_labels').select('id').orderBy('id')).map(row => row.id), ['r5', 'r6']);
  console.log('PASS multi-label flow selects once; removes four relations; preserves other member');

  await assert.rejects(repo.bulkEdit(action([]), {all: true}), /valid list of label IDs/);
  await assert.rejects(repo.bulkEdit({action: 'removeLabels', meta: {labels: [{id: ALPHA}], label: {id: ZETA}}}, {all: true}), /valid list of label IDs/);
  const none = await repo.bulkEdit(action([ALPHA, ZETA]), {search: 'no-such-member'});
  assert.equal(none.successful, 0);
  console.log('PASS invalid, ambiguous, and empty-selection cases');

  await knex('members_labels').del();
  await knex('members').del();
  for (let i = 0; i < 51; i++) {
    const member = `m${String(i).padStart(3, '0')}`;
    await knex('members').insert({id: member});
    for (const [j, label] of [ALPHA, ZETA].entries()) {
      await knex('members_labels').insert({id: `r${String(i * 2 + j).padStart(3, '0')}`, member_id: member, label_id: label});
    }
  }
  await knex.raw("CREATE TRIGGER fail_second_chunk BEFORE DELETE ON members_labels WHEN old.id = 'r101' BEGIN SELECT RAISE(ABORT, 'injected delete failure'); END");
  await assert.rejects(repo.bulkEdit(action([ALPHA, ZETA]), {all: true}), /injected delete failure/);
  assert.equal((await knex('members_labels')).length, 102);
  await knex.raw('DROP TRIGGER fail_second_chunk');
  console.log('PASS injected second-chunk failure rolls back all 102 relations');

  const frame = new Frame({body: {bulk: {action: 'removeLabels', meta: {labels: [{id: ALPHA}, {id: ZETA}]}}}});
  frame.configure({data: ['action', 'meta']});
  serializer.bulkEdit({successful: 2, unsuccessful: 0, errors: [], unsuccessfulData: []}, {}, frame);
  const wire = JSON.parse(JSON.stringify(frame.response));
  assert.equal(Object.hasOwn(wire.bulk, 'action'), false);
  assert.equal(wire.bulk.meta.stats.successful, 2);
  console.log('PASS response probe: actual serialized JSON omits bulk.action');

  const invalidFrame = new Frame({body: {bulk: {action: 'invalid-action'}}});
  invalidFrame.configure({data: ['action', 'meta']});
  await validator.input({docName: 'members', method: 'bulkEdit', data: {action: {required: true, values: ['removeLabels']}}}, {}, invalidFrame);
  await assert.rejects(repo.bulkEdit(invalidFrame.data.bulk, {all: true}), /Unsupported bulk action/);
  console.log('PASS validation probe: shared bulkEdit validator accepts invalid action; repository rejects it');

  const opts = await knex.raw('PRAGMA compile_options');
  const maxOption = opts.map(row => row.compile_options).find(value => value.startsWith('MAX_VARIABLE_NUMBER='));
  const maxVariables = Number(maxOption?.split('=')[1] || 999);
  console.log(`SQLite ${maxOption || 'MAX_VARIABLE_NUMBER default 999'}`);
  if (maxVariables <= 40000) {
    const memberIds = Array(maxVariables - 1).fill('nonexistent');
    const legacy = await Member.getLabelRelations({labelId: ALPHA, memberIds});
    assert.equal(legacy.length, 0);
    let message;
    try {
      await Member.getLabelRelations({labelIds: [ALPHA, ZETA], memberIds});
    } catch (err) { message = err.message.slice(-250); }
    assert.match(message, /too many SQL variables/i);
    console.log(`PASS SQLite boundary: single label works at ${maxVariables} bindings; two fail at ${maxVariables + 1}: ${message}`);
  } else {
    console.log('SKIP SQLite variable boundary: compiled limit exceeds 40000');
  }
}
main().then(() => knex.destroy()).catch(async error => {
  console.error(error.stack || String(error));
  await knex.destroy();
  process.exitCode = 1;
});
"""


def main():
    sandbox = None
    try:
        with tempfile.TemporaryDirectory(prefix=".tmp-pr32434-audit-", dir=PARENT) as name:
            sandbox = Path(name).resolve()
            if sandbox.parent != PARENT.resolve() or not sandbox.name.startswith(".tmp-pr32434-audit-"):
                raise RuntimeError("unexpected sandbox path")
            script = sandbox / "probe.cjs"
            script.write_text(JS, encoding="utf-8")
            env = os.environ.copy()
            for key in ("TEMP", "TMP", "TMPDIR", "XDG_CACHE_HOME"):
                env[key] = str(sandbox)
            env.update(PR_SOURCE=str(ROOT), NODE_OPTIONS="--conditions=source --max-old-space-size=2048", UV_THREADPOOL_SIZE="1", TSX_DISABLE_CACHE="1")
            result = subprocess.run([str(NODE), str(script)], cwd=sandbox, env=env, timeout=90, check=False)
            print(f"PROBE_EXIT={result.returncode}", flush=True)
    finally:
        print(f"SANDBOX_REMOVED={sandbox is not None and not sandbox.exists()}", flush=True)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
