import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface ErrorMessageProps {
  error: Error | string;
  title?: string;
  onRetry?: () => void;
}

export function ErrorMessage({
  error,
  title = 'Something went wrong',
  onRetry,
}: ErrorMessageProps) {
  const message = typeof error === 'string' ? error : error.message;

  return (
    <div className="rounded-lg bg-loss/10 border border-loss/20 p-4">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-loss mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-loss">{title}</h3>
          <p className="mt-1 text-sm text-text-secondary">{message}</p>
          {onRetry && (
            <div className="mt-3">
              <Button variant="secondary" size="sm" onClick={onRetry} icon={<RefreshCw className="w-4 h-4" />}>
                Try Again
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
