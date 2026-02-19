import { useState } from 'react';
import { Calendar, ChevronDown } from 'lucide-react';
import { Button } from './Button';
import { Input } from './Input';

interface DateRangePickerProps {
  selectedDays: number;
  onDaysChange: (days: number) => void;
  onCustomRange?: (start: string, end: string) => void;
}

const presets = [
  { label: 'Today', days: 0 },
  { label: '24H', days: 1 },
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
];

export function DateRangePicker({
  selectedDays,
  onDaysChange,
  onCustomRange,
}: DateRangePickerProps) {
  const [showCustom, setShowCustom] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const handleApplyCustom = () => {
    if (startDate && endDate && onCustomRange) {
      onCustomRange(startDate, endDate);
      setShowCustom(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Preset buttons */}
      <div className="flex gap-1 bg-dark-600 p-1 rounded-lg">
        {presets.map((preset) => (
          <button
            key={preset.days}
            onClick={() => onDaysChange(preset.days)}
            className={`
              px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200
              ${selectedDays === preset.days
                ? 'bg-accent-blue text-white'
                : 'text-text-secondary hover:text-text-primary hover:bg-dark-500'
              }
            `}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Custom button */}
      <div className="relative">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setShowCustom(!showCustom)}
          icon={<Calendar className="w-4 h-4" />}
        >
          Custom
          <ChevronDown className={`w-4 h-4 transition-transform ${showCustom ? 'rotate-180' : ''}`} />
        </Button>

        {/* Custom dropdown */}
        {showCustom && (
          <div className="absolute top-full mt-2 right-0 bg-dark-700 border border-border rounded-lg p-4 shadow-lg z-50 min-w-[280px]">
            <div className="space-y-3">
              <Input
                label="Start Date"
                type="date"
                value={startDate}
                onChange={setStartDate}
                size="sm"
              />
              <Input
                label="End Date"
                type="date"
                value={endDate}
                onChange={setEndDate}
                size="sm"
              />
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setShowCustom(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleApplyCustom}
                  disabled={!startDate || !endDate}
                  className="flex-1"
                >
                  Apply
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
