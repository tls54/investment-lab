import type { InputHTMLAttributes, ReactNode } from 'react';

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'size'> {
  label?: string;
  error?: string;
  hint?: string;
  icon?: ReactNode;
  suffix?: ReactNode;
  size?: 'sm' | 'md' | 'lg';
  onChange?: (value: string) => void;
}

const sizeStyles = {
  sm: 'px-3 py-2 text-sm',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-4 py-3 text-base',
};

export function Input({
  label,
  error,
  hint,
  icon,
  suffix,
  size = 'md',
  onChange,
  className = '',
  ...props
}: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-text-secondary mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-muted">
            {icon}
          </div>
        )}
        <input
          className={`
            w-full bg-dark-600 border border-border rounded-lg
            text-text-primary placeholder-text-muted
            focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue
            disabled:bg-dark-700 disabled:cursor-not-allowed disabled:opacity-50
            transition-all duration-200
            ${icon ? 'pl-10' : ''}
            ${suffix ? 'pr-12' : ''}
            ${error ? 'border-loss focus:ring-loss/50 focus:border-loss' : ''}
            ${sizeStyles[size]}
            ${className}
          `}
          onChange={(e) => onChange?.(e.target.value)}
          {...props}
        />
        {suffix && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center text-text-muted">
            {suffix}
          </div>
        )}
      </div>
      {error && <p className="mt-1.5 text-sm text-loss">{error}</p>}
      {hint && !error && <p className="mt-1.5 text-sm text-text-muted">{hint}</p>}
    </div>
  );
}
