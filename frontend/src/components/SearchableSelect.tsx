import { useState, useRef, useEffect } from 'react';

interface SearchableSelectProps {
  readonly options: string[];
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly placeholder?: string;
  readonly label?: string;
  readonly allLabel?: string;
}

export function SearchableSelect({
  options,
  value,
  onChange,
  placeholder = 'Search...',
  label,
  allLabel = 'All',
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus input when dropdown opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const filteredOptions = options.filter((option) =>
    option.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const displayValue = value === 'all' ? allLabel : value;

  return (
    <div className="relative" ref={dropdownRef}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
      )}
      
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="relative w-full bg-white border border-gray-300 rounded-lg shadow-sm pl-3 pr-10 py-2 text-left cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      >
        <span className="block truncate">{displayValue}</span>
        <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
          <svg
            className={`h-5 w-5 text-gray-400 transition-transform ${
              isOpen ? 'transform rotate-180' : ''
            }`}
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </span>
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-lg py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
          {/* Search Input */}
          <div className="sticky top-0 bg-white px-2 py-2 border-b border-gray-200">
            <input
              ref={inputRef}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder={placeholder}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Options List */}
          <div className="py-1">
            {/* "All" option */}
            <button
              onClick={() => {
                onChange('all');
                setIsOpen(false);
                setSearchQuery('');
              }}
              className={`w-full text-left px-3 py-2 hover:bg-gray-100 transition-colors ${
                value === 'all' ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-900'
              }`}
            >
              {allLabel}
            </button>

            {/* Filtered options */}
            {filteredOptions.length > 0 ? (
              filteredOptions.map((option) => (
                <button
                  key={option}
                  onClick={() => {
                    onChange(option);
                    setIsOpen(false);
                    setSearchQuery('');
                  }}
                  className={`w-full text-left px-3 py-2 hover:bg-gray-100 transition-colors ${
                    value === option ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-900'
                  }`}
                >
                  {option}
                </button>
              ))
            ) : (
              <div className="px-3 py-2 text-gray-500 text-sm">No results found</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default SearchableSelect;
