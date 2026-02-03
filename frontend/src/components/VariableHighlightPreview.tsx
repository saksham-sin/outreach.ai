interface VariableHighlightPreviewProps {
  readonly htmlContent: string;
}

/**
 * Renders HTML with template variables highlighted in blue with tooltips
 * Preserves original HTML formatting (bold/italic/lists/etc.)
 */
export function VariableHighlightPreview({
  htmlContent,
}: VariableHighlightPreviewProps) {
  const highlightedHtml = htmlContent.replaceAll(/{{[^}]+}}/g, (match) => {
    return `<span class="vhp-var" title="This variable will be replaced by lead information">${match}</span>`;
  });

  return (
    <div className="prose prose-sm max-w-none vhp-preview">
      <style>{`
        .vhp-preview ul { list-style: disc; padding-left: 1.25rem; }
        .vhp-preview ol { list-style: decimal; padding-left: 1.25rem; }
        .vhp-preview li { margin: 0.25rem 0; }
        .vhp-var { background: #dbeafe; color: #1e40af; padding: 0 4px; border-radius: 3px; cursor: help; }
      `}</style>
      <div dangerouslySetInnerHTML={{ __html: highlightedHtml }} />
    </div>
  );
}
