"use client";

import { memo, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy } from "lucide-react";

interface MarkdownContentProps {
  content: string;
}

function CodeBlock({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLElement> & { inline?: boolean }) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || "");
  const language = match ? match[1] : "";
  const codeString = String(children).replace(/\n$/, "");

  // If inline code
  if (!match && !String(children).includes("\n")) {
    return (
      <code
        className="rounded bg-surface-elevated px-1.5 py-0.5 font-mono text-xs font-medium text-accent"
        {...props}
      >
        {children}
      </code>
    );
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore copy error
    }
  };

  return (
    <div className="group relative my-3 overflow-hidden rounded-lg border border-border-subtle bg-surface-base font-mono text-xs">
      {/* Code Header Bar */}
      <div className="flex h-8 items-center justify-between border-b border-border-subtle bg-surface-raised px-3 text-text-tertiary">
        <span className="text-[11px] font-semibold uppercase tracking-wider">
          {language || "code"}
        </span>
        <button
          onClick={handleCopy}
          aria-label={copied ? "Copied code" : "Copy code"}
          className="flex items-center gap-1.5 rounded px-1.5 py-0.5 text-[11px] transition-colors hover:bg-surface-elevated hover:text-text-primary"
        >
          {copied ? (
            <>
              <Check size={13} className="text-success" />
              <span className="text-success">Copied</span>
            </>
          ) : (
            <>
              <Copy size={13} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Body */}
      <div className="overflow-x-auto p-3 text-text-primary">
        <code className={className} {...props}>
          {children}
        </code>
      </div>
    </div>
  );
}

export const MarkdownContent = memo(function MarkdownContent({
  content,
}: MarkdownContentProps) {
  return (
    <div className="markdown-prose text-sm leading-relaxed text-text-primary space-y-2.5">
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h1 className="mt-4 mb-2 text-lg font-bold tracking-tight text-text-primary">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="mt-3 mb-1.5 text-base font-semibold text-text-primary">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mt-2.5 mb-1 text-sm font-semibold text-text-primary">
              {children}
            </h3>
          ),
          // Paragraphs & Lists
          p: ({ children }) => (
            <p className="mb-2 leading-relaxed last:mb-0">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="mb-2 list-disc pl-5 space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-2 list-decimal pl-5 space-y-1">{children}</ol>
          ),
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          // Links (safe external links)
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent underline underline-offset-2 hover:text-accent-hover"
            >
              {children}
            </a>
          ),
          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-accent pl-3 italic text-text-secondary my-2">
              {children}
            </blockquote>
          ),
          // Tables
          table: ({ children }) => (
            <div className="my-3 overflow-x-auto rounded-lg border border-border-subtle">
              <table className="w-full text-left text-xs border-collapse">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="border-b border-border-subtle bg-surface-raised font-semibold text-text-primary">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-border-subtle bg-surface-base">
              {children}
            </tbody>
          ),
          tr: ({ children }) => <tr>{children}</tr>,
          th: ({ children }) => <th className="p-2.5">{children}</th>,
          td: ({ children }) => <td className="p-2.5 text-text-secondary">{children}</td>,
          // Code
          code: CodeBlock,
        }}
      >
        {content}
      </Markdown>
    </div>
  );
});
