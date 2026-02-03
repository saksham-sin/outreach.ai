import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import TextAlign from '@tiptap/extension-text-align';
import Underline from '@tiptap/extension-underline';
import { useEffect } from 'react';

interface RichTextEditorProps {
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly height?: string;
  readonly onEditorReady?: (insertText: (text: string) => void) => void;
}

export function RichTextEditor({
  value,
  onChange,
  height = '300px',
  onEditorReady,
}: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        paragraph: {
          HTMLAttributes: {
            class: 'text-gray-900',
          },
        },
        heading: false, // Disable headings
        codeBlock: false, // Disable code blocks
        code: false, // Disable inline code
      }),
      Underline,
      TextAlign.configure({
        types: ['paragraph'],
      }),
    ],
    content: value,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none px-4 py-3 text-gray-900 focus:outline-none',
      },
    },
  });

  // Sync external value changes with editor
  useEffect(() => {
    if (editor && value !== editor.getHTML()) {
      editor.commands.setContent(value);
    }
  }, [value, editor]);

  // Expose insertText function when editor is ready
  useEffect(() => {
    if (editor && onEditorReady) {
      onEditorReady((text: string) => {
        editor.chain().focus().insertContent(text).run();
      });
    }
  }, [editor, onEditorReady]);

  if (!editor) {
    return <div>Loading editor...</div>;
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      <style>{`
        .tiptap {
          min-height: ${height};
          max-height: ${height};
          overflow-y: auto;
        }
        .tiptap p {
          margin: 0.5rem 0;
        }
        .tiptap em {
          font-style: italic;
        }
        .tiptap strong {
          font-weight: bold;
        }
        .tiptap u {
          text-decoration: underline;
        }
        .tiptap ul,
        .tiptap ol {
          margin: 0.5rem 0 0.5rem 1.5rem;
        }
        .tiptap li {
          margin: 0.25rem 0;
        }
        .tiptap a {
          color: #2563eb;
          text-decoration: underline;
          cursor: pointer;
        }
      `}</style>

      {/* Toolbar */}
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 flex flex-wrap gap-2">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          disabled={!editor.can().chain().focus().toggleBold().run()}
          className={`px-3 py-2 rounded font-medium text-sm transition ${
            editor.isActive('bold')
              ? 'bg-blue-500 text-white'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-100'
          }`}
          title="Bold (Ctrl+B)"
        >
          B
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          disabled={!editor.can().chain().focus().toggleItalic().run()}
          className={`px-3 py-2 rounded font-medium text-sm italic transition ${
            editor.isActive('italic')
              ? 'bg-blue-500 text-white'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-100'
          }`}
          title="Italic (Ctrl+I)"
        >
          I
        </button>
        <button
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          disabled={!editor.can().chain().focus().toggleUnderline().run()}
          className={`px-3 py-2 rounded font-medium text-sm underline transition ${
            editor.isActive('underline')
              ? 'bg-blue-500 text-white'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-100'
          }`}
          title="Underline (Ctrl+U)"
        >
          U
        </button>

        <div className="border-l border-gray-300 mx-1"></div>

        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`px-3 py-2 rounded text-sm transition ${
            editor.isActive('bulletList')
              ? 'bg-blue-500 text-white'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-100'
          }`}
          title="Bullet List"
        >
          • List
        </button>

        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`px-3 py-2 rounded text-sm transition ${
            editor.isActive('orderedList')
              ? 'bg-blue-500 text-white'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-100'
          }`}
          title="Numbered List"
        >
          1. List
        </button>

        <div className="border-l border-gray-300 mx-1"></div>

        <button
          onClick={() => editor.chain().focus().clearNodes().run()}
          className="px-3 py-2 rounded text-sm bg-white border border-gray-300 text-gray-700 hover:bg-gray-100 transition"
          title="Clear Formatting"
        >
          Clear
        </button>
      </div>

      {/* Editor */}
      <EditorContent editor={editor} />
    </div>
  );
}
