import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
}

const sizeStyles = {
  sm: 'w-5 h-5',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

export function LoadingSpinner({ size = 'md', message }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader2 className={`${sizeStyles[size]} animate-spin text-accent-blue`} />
      {message && (
        <p className="mt-4 text-sm text-text-secondary">{message}</p>
      )}
    </div>
  );
}

export function LoadingSkeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse bg-dark-600 rounded ${className}`}
    />
  );
}
