import { marked } from 'marked';
import hljs from 'highlight.js';
import 'highlight.js/styles/github.css';

const renderer = new marked.Renderer();

renderer.code = function ({ text, lang }: { text: string; lang?: string }): string {
  const language = lang || '';
  const highlighted = language && hljs.getLanguage(language)
    ? hljs.highlight(text, { language }).value
    : hljs.highlightAuto(text).value;
  return `<div class="md-code-block"><pre class="md-code-pre"><code class="hljs">${highlighted}</code></pre></div>`;
};

marked.setOptions({
  gfm: true,
  breaks: false,
  renderer,
});

interface MarkdownRendererProps {
  content: string;
  thinking?: string;
}

export default function MarkdownRenderer({ content, thinking }: MarkdownRendererProps) {
  const html = marked.parse(content || '\u00A0') as string;
  const thinkingHtml = thinking ? (marked.parse(thinking) as string) : '';

  return (
    <div className="message-markdown">
      {thinking ? (
        <details className="md-thinking" open>
          <summary className="md-thinking-toggle">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
            <span>Thinking...</span>
          </summary>
          <div className="md-thinking-body" dangerouslySetInnerHTML={{ __html: thinkingHtml }} />
        </details>
      ) : null}
      <div dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
