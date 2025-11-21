import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

const paddingStyles = {
  none: '',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6',
};

export function Card({
  children,
  title,
  subtitle,
  action,
  className = '',
  padding = 'md',
  hover = false,
}: CardProps) {
  return (
    <div
      className={`
        bg-dark-700 border border-border rounded-xl
        ${hover ? 'transition-all duration-200 hover:border-accent-blue/50 hover:shadow-glow cursor-pointer' : ''}
        ${className}
      `}
    >
      {(title || subtitle || action) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            {title && (
              <h3 className="text-base font-semibold text-text-primary">{title}</h3>
            )}
            {subtitle && (
              <p className="text-sm text-text-muted mt-0.5">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={paddingStyles[padding]}>{children}</div>
    </div>
  );
}
