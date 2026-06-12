import { useState, useCallback, type ComponentPropsWithoutRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { coldarkDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

function CopyButton({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [code]);

  return (
    <button className="md-code-copy" onClick={handleCopy}>
      {copied ? (
        <>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          <span>Copied</span>
        </>
      ) : (
        <>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
          <span>Copy</span>
        </>
      )}
    </button>
  );
}

interface CodeBlockProps extends ComponentPropsWithoutRef<'code'> {
  inline?: boolean;
  className?: string;
}

function CodeBlock({ inline, className, children, ...props }: CodeBlockProps) {
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const codeString = String(children).replace(/\n$/, '');

  if (inline || !language) {
    return (
      <code className="md-inline-code" {...props}>
        {children}
      </code>
    );
  }

  return (
    <div className="md-code-block">
      <div className="md-code-header">
        <span className="md-code-lang">{language}</span>
        <CopyButton code={codeString} />
      </div>
      <SyntaxHighlighter
        style={coldarkDark}
        language={language}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: 0,
          fontSize: '13px',
          lineHeight: '1.6',
          padding: '16px 20px',
          background: 'transparent',
        }}
      >
        {codeString}
      </SyntaxHighlighter>
    </div>
  );
}

function ThinkingBlock({ thinking }: { thinking: string }) {
  const [open, setOpen] = useState(true);

  if (!thinking) return null;

  return (
    <div className="md-thinking">
      <button
        className="md-thinking-toggle"
        onClick={() => setOpen(!open)}
      >
        <svg
          width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          style={{ transform: open ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 150ms ease' }}
        >
          <polyline points="9 18 15 12 9 6"/>
        </svg>
        <span>Thinking...</span>
      </button>
      {open && (
        <div className="md-thinking-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {thinking}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}

interface MarkdownRendererProps {
  content: string;
  thinking?: string;
}

export default function MarkdownRenderer({ content, thinking }: MarkdownRendererProps) {
  return (
    <div className="message-markdown">
      <ThinkingBlock thinking={thinking || ''} />
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code: CodeBlock as never,
        }}
      >
        {content || '\u00A0'}
      </ReactMarkdown>
    </div>
  );
}
