import { useState } from 'react';
import { Plus } from 'lucide-react';
import { DENOMINATIONS } from '../../utils';
import { Input } from '../common';

interface DenominationPickerProps {
  value: string;
  onChange: (denomination: string) => void;
}

export function DenominationPicker({ value, onChange }: DenominationPickerProps) {
  const [showCustom, setShowCustom] = useState(false);
  const [customValue, setCustomValue] = useState('');

  const handleAddCustom = () => {
    if (customValue.trim()) {
      onChange(customValue.toUpperCase());
      setShowCustom(false);
      setCustomValue('');
    }
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-text-secondary">
        Denomination
      </label>
      <div className="flex flex-wrap gap-2">
        {DENOMINATIONS.map((denom) => (
          <button
            key={denom.value}
            onClick={() => onChange(denom.value)}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
              ${value === denom.value
                ? 'bg-accent-blue text-white shadow-glow'
                : 'bg-dark-600 text-text-secondary border border-border hover:border-accent-blue/50 hover:text-text-primary'
              }
            `}
          >
            <span className="mr-1.5">{denom.symbol}</span>
            {denom.label}
          </button>
        ))}

        {/* Custom denomination button */}
        {!showCustom ? (
          <button
            onClick={() => setShowCustom(true)}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-dark-600 text-text-muted border border-dashed border-border hover:border-accent-blue/50 hover:text-text-primary transition-all duration-200 flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            Custom
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <Input
              value={customValue}
              onChange={setCustomValue}
              placeholder="e.g., GLD"
              size="sm"
              className="w-32"
              onKeyDown={(e) => e.key === 'Enter' && handleAddCustom()}
            />
            <button
              onClick={handleAddCustom}
              className="px-3 py-2 bg-accent-blue text-white text-sm font-medium rounded-lg hover:bg-accent-blue/90"
            >
              Add
            </button>
            <button
              onClick={() => setShowCustom(false)}
              className="px-3 py-2 text-text-muted text-sm hover:text-text-primary"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Show what the current selection means */}
      {value && value !== 'USD' && (
        <p className="text-xs text-text-muted">
          Prices will be shown in terms of {value}
        </p>
      )}
    </div>
  );
}
