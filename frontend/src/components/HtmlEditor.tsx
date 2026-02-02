import { useRef } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { html } from '@codemirror/lang-html';

interface HtmlEditorProps {
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly height?: string;
}

export function HtmlEditor({
  value,
  onChange,
  height = '300px',
}: HtmlEditorProps) {
  const editorRef = useRef<any>(null);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      <style>{`
        .cm-editor {
          font-family: 'Courier New', monospace;
          font-size: 13px;
        }
        .cm-line {
          padding-left: 4px;
        }
        /* Highlight template variables */
        .cm-overlay-variable {
          background-color: #dbeafe;
          color: #1e40af;
          padding: 2px 4px;
          border-radius: 3px;
        }
      `}</style>
      <CodeMirror
        ref={editorRef}
        value={value}
        onChange={onChange}
        extensions={[html()]}
        theme="dark"
        height={height}
        className="text-sm"
        basicSetup={{
          lineNumbers: true,
          highlightActiveLineGutter: true,
          foldGutter: true,
          dropCursor: true,
          allowMultipleSelections: true,
          indentOnInput: true,
          bracketMatching: true,
          closeBrackets: true,
          autocompletion: true,
          rectangularSelection: true,
          highlightSelectionMatches: true,
          searchKeymap: true,
        }}
      />
    </div>
  );
}
