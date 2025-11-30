import { useState, useEffect, useCallback } from 'react';
import { Search, X } from 'lucide-react';
import { Input } from '../common';
import { validateSymbol, POPULAR_SYMBOLS } from '../../utils';

interface SymbolSearchProps {
  value: string;
  onChange: (symbol: string) => void;
  onSubmit?: (symbol: string) => void;
  placeholder?: string;
  label?: string;
  showSuggestions?: boolean;
}

export function SymbolSearch({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search symbol...',
  label,
  showSuggestions = true,
}: SymbolSearchProps) {
  const [inputValue, setInputValue] = useState(value);
  const [error, setError] = useState<string>();
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  const debouncedOnChange = useCallback(
    (() => {
      let timeoutId: ReturnType<typeof setTimeout>;
      return (newValue: string) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          const upperValue = newValue.toUpperCase();
          if (newValue) {
            const validation = validateSymbol(upperValue);
            if (!validation.valid) {
              setError(validation.error);
              return;
            }
          }
          setError(undefined);
          onChange(upperValue);
        }, 300);
      };
    })(),
    [onChange]
  );

  const handleChange = (newValue: string) => {
    const upperValue = newValue.toUpperCase();
    setInputValue(upperValue);
    debouncedOnChange(upperValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault(); // Prevent form submission

      // Smart behavior:
      // If suggestions dropdown is showing, auto-fill first suggestion
      if (focused && filteredSuggestions.length > 0) {
        handleSelectSuggestion(filteredSuggestions[0].symbol);
      } else if (inputValue && !error && onSubmit) {
        // Otherwise, execute action via onSubmit (if provided)
        onSubmit(inputValue);
      }
    }
  };

  const handleClear = () => {
    setInputValue('');
    setError(undefined);
    onChange('');
  };

  const handleSelectSuggestion = (symbol: string) => {
    setInputValue(symbol);
    onChange(symbol);
    onSubmit?.(symbol);
    setFocused(false);
  };

  const filteredSuggestions = POPULAR_SYMBOLS.filter(
    (item) =>
      item.symbol.includes(inputValue) || item.name.toLowerCase().includes(inputValue.toLowerCase())
  ).slice(0, 5);

  return (
    <div className="relative">
      <div className="relative">
        <Input
          label={label}
          value={inputValue}
          onChange={handleChange}
          placeholder={placeholder}
          error={error}
          icon={<Search className="w-5 h-5" />}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 200)}
          suffix={
            inputValue ? (
              <button onClick={handleClear} className="hover:text-text-primary">
                <X className="w-4 h-4" />
              </button>
            ) : undefined
          }
        />
      </div>

      {/* Suggestions dropdown */}
      {showSuggestions && focused && inputValue.length > 0 && filteredSuggestions.length > 0 && (
        <div className="absolute top-full mt-1 w-full bg-dark-700 border border-border rounded-lg shadow-lg z-50 overflow-hidden">
          {filteredSuggestions.map((item) => (
            <button
              key={item.symbol}
              onClick={() => handleSelectSuggestion(item.symbol)}
              className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-dark-600 transition-colors"
            >
              <span className="font-medium text-text-primary">{item.symbol}</span>
              <span className="text-sm text-text-muted">{item.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
