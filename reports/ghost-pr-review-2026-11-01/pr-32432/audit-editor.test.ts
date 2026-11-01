// @vitest-environment jsdom
import {expect, test} from 'vitest';
import {$generateHtmlFromNodes} from '@lexical/html';
import {createEditor, $createParagraphNode, $getRoot} from 'lexical';
import {cleanBasicHtml} from '@tryghost/kg-clean-basic-html';
import {htmlToLexical} from '@tryghost/kg-html-to-lexical';
import generateEditorState from './editor-helpers/generateEditorState';
import BASIC_NODES from './editor-helpers/BasicNodes';
import MINIMAL_NODES from './editor-helpers/MinimalNodes';

const isHead = process.env.TOGGLE_AUDIT_PHASE === 'head';

function importCard(heading: string, content: string) {
    const html = `<div class="kg-card kg-toggle-card"><h4 class="kg-toggle-heading-text">${heading}</h4><div class="kg-toggle-content">${content}</div></div>`;
    return htmlToLexical(html).root.children[0] as any;
}

function serializeNested(initialHtml: string, heading: boolean) {
    const editor = createEditor({nodes: heading ? MINIMAL_NODES : BASIC_NODES});
    editor.update(() => $getRoot().append($createParagraphNode()), {discrete: true});
    editor.setEditorState(generateEditorState({editor, initialHtml}));
    return editor.getEditorState().read(() => {
        const generatedHtml = $generateHtmlFromNodes(editor, null);
        return cleanBasicHtml(generatedHtml, {firstChildInnerContent: heading, allowBr: true});
    });
}

test('supported imported formatting survives the editor nested-state conversion', () => {
    const node = importCard('Read <em>more</em>', '<p>Read <a href="https://example.com/doc">documentation</a></p><p><strong>Second</strong> paragraph</p>');
    const heading = serializeNested(node.heading, true);
    const content = serializeNested(node.content, false);
    const headingDom = new DOMParser().parseFromString(heading, 'text/html');
    const contentDom = new DOMParser().parseFromString(content, 'text/html');
    expect(headingDom.querySelector('em')?.textContent ?? null).toBe(isHead ? 'more' : null);
    expect(contentDom.querySelector('a')?.getAttribute('href') ?? null).toBe(isHead ? 'https://example.com/doc' : null);
    expect(contentDom.querySelectorAll('p').length).toBe(isHead ? 2 : 1);
    expect(contentDom.querySelector('strong')?.textContent ?? null).toBe(isHead ? 'Second' : null);
});

test('an image newly carried by the parser is not supported by the nested editor', () => {
    const node = importCard('Heading', '<p>Text</p><img src="x" alt="example">');
    expect(node.content.includes('<img')).toBe(isHead);
    const content = serializeNested(node.content, false);
    const document = new DOMParser().parseFromString(content, 'text/html');
    expect(document.querySelector('img')).toBeNull();
    expect(document.body.textContent).toBe('Text');
});
