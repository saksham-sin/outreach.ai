import { useState } from 'react';

interface TagInputProps {
  label?: string;
  tags: string[];
  onTagsChange: (tags: string[]) => void;
  placeholder?: string;
  maxTags?: number;
}

export function TagInput({
  label,
  tags,
  onTagsChange,
  placeholder = 'Add tags and press Enter',
  maxTags = 10,
}: TagInputProps) {
  const [input, setInput] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const tag = input.trim();

      if (tag && !tags.includes(tag) && tags.length < maxTags) {
        onTagsChange([...tags, tag]);
        setInput('');
      }
    }
  };

  const handleRemoveTag = (index: number) => {
    onTagsChange(tags.filter((_, i) => i !== index));
  };

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <div className="space-y-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={tags.length >= maxTags}
          className={`
            w-full px-3 py-2 border rounded-lg shadow-sm
            placeholder-gray-400
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            disabled:bg-gray-100 disabled:cursor-not-allowed
            border-gray-300
          `}
        />
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {tags.map((tag, index) => (
              <div
                key={index}
                className="flex items-center gap-1 bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
              >
                <span>{tag}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveTag(index)}
                  className="hover:text-blue-900 font-bold leading-none"
                  aria-label={`Remove tag ${tag}`}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
        {tags.length >= maxTags && (
          <p className="text-sm text-gray-500">Maximum {maxTags} tags reached</p>
        )}
      </div>
    </div>
  );
}
