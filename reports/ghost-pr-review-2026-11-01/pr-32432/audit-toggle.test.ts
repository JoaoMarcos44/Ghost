import {expect, test} from 'vitest';
import {JSDOM} from 'jsdom';
import {DEFAULT_NODES} from '@tryghost/kg-default-nodes';
import {htmlToLexical} from '@tryghost/kg-html-to-lexical';
import {LexicalHTMLRenderer} from '@tryghost/kg-lexical-html-renderer';

const isHead = process.env.TOGGLE_AUDIT_PHASE === 'head';

function card(heading: string, content: string) {
    return `<div class="kg-card kg-toggle-card"><h4 class="kg-toggle-heading-text">${heading}</h4><div class="kg-toggle-content">${content}</div></div>`;
}

async function convertAndRender(html: string) {
    const state = htmlToLexical(html);
    const dom = new JSDOM();
    try {
        const renderer = new LexicalHTMLRenderer({dom, nodes: DEFAULT_NODES});
        const web = await renderer.render(state);
        const email = await renderer.render(state, {target: 'email'});
        return {state, web, email};
    } finally {
        dom.window.close();
    }
}

function documentFor(html: string) {
    return new JSDOM(html);
}

test('rich content survives the real web converter and renderer at head', async () => {
    const {state, web} = await convertAndRender(card('Read <em>more</em>', '<p>Read <a href="https://example.com/doc">documentation</a></p><p>Second paragraph</p>'));
    const node = state.root.children[0] as any;
    expect(node.type).toBe('toggle');
    expect(node.heading).toBe(isHead ? 'Read <em>more</em>' : 'Read more');
    expect(node.content).toBe(isHead ? '<p>Read <a href="https://example.com/doc">documentation</a></p><p>Second paragraph</p>' : 'Read documentationSecond paragraph');
    const dom = documentFor(web);
    try {
        expect(dom.window.document.querySelectorAll('.kg-toggle-content p').length).toBe(isHead ? 2 : 0);
    } finally {
        dom.window.close();
    }
});

test('adjacent formatted words retain web spacing but lose email spacing at head', async () => {
    const input = card('<strong>Heading</strong> <em>words</em>', '<p><strong>Hello</strong> <em>world</em></p>');
    const {state, web, email} = await convertAndRender(input);
    const webDom = documentFor(web);
    const emailDom = documentFor(email);
    try {
        const webContent = webDom.window.document.querySelector('.kg-toggle-content')!;
        const emailContent = emailDom.window.document.querySelector('.kg-toggle-content')!;
        const emailHeading = emailDom.window.document.querySelector('.kg-toggle-heading h4')!;
        expect(webContent.textContent!.trim()).toBe('Hello world');
        expect(emailContent.textContent!.trim()).toBe(isHead ? 'Helloworld' : 'Hello world');
        expect(emailHeading.textContent!.trim()).toBe(isHead ? 'Headingwords' : 'Heading words');
        console.log(`OBS phase=${isHead ? 'head' : 'base'} web=${JSON.stringify(webContent.textContent!.trim())} email=${JSON.stringify(emailContent.textContent!.trim())} heading=${JSON.stringify(emailHeading.textContent!.trim())} content=${JSON.stringify((state.root.children[0] as any).content)}`);
    } finally {
        webDom.window.close();
        emailDom.window.close();
    }
});

test('escaped markup stays text at head', async () => {
    const {web} = await convertAndRender(card('Fish &amp; &lt;chips&gt;', 'Example: &lt;em&gt;not emphasis&lt;/em&gt; &amp; text'));
    const dom = documentFor(web);
    try {
        const content = dom.window.document.querySelector('.kg-toggle-content')!;
        expect(content.querySelector('em') === null).toBe(isHead);
        if (isHead) {
            expect(content.textContent).toBe('Example: <em>not emphasis</em> & text');
        }
    } finally {
        dom.window.close();
    }
});

test('active attributes now survive a toggle import; an HTML card already retained them', async () => {
    const image = '<img src="x" onerror="auditMarker()">';
    const toggle = await convertAndRender(card('Heading', image + 'body'));
    const dom = documentFor(toggle.web);
    try {
        const img = dom.window.document.querySelector('.kg-toggle-content img');
        expect(img?.getAttribute('onerror') ?? null).toBe(isHead ? 'auditMarker()' : null);
    } finally {
        dom.window.close();
    }
    const explicitHtml = await convertAndRender(`<!--kg-card-begin: html-->${image}<!--kg-card-end: html-->`);
    expect(explicitHtml.state.root.children[0].type).toBe('html');
    expect(explicitHtml.web).toContain('onerror="auditMarker()"');
});

test('missing toggle fields default to empty at both revisions', async () => {
    const {state} = await convertAndRender('<div class="kg-card kg-toggle-card"><span>Unrelated</span></div>');
    const node = state.root.children[0] as any;
    expect(node.type).toBe('toggle');
    expect(node.heading).toBe('');
    expect(node.content).toBe('');
});

test('email-table markup imports as an HTML card at both revisions', async () => {
    const {email} = await convertAndRender(card('Heading', '<p>Content</p>'));
    expect(htmlToLexical(email).root.children[0].type).toBe('html');
});
