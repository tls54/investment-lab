export const validateSymbol = (symbol: string): { valid: boolean; error?: string } => {
  if (!symbol || symbol.trim().length === 0) {
    return { valid: false, error: 'Symbol is required' };
  }

  if (symbol.length > 10) {
    return { valid: false, error: 'Symbol too long (max 10 characters)' };
  }

  if (!/^[A-Z0-9-]+$/i.test(symbol)) {
    return { valid: false, error: 'Invalid characters (use A-Z, 0-9, -)' };
  }

  return { valid: true };
};

export const validateDateRange = (
  startDate?: string,
  endDate?: string
): { valid: boolean; error?: string } => {
  if (!startDate || !endDate) {
    return { valid: true };
  }

  const start = new Date(startDate);
  const end = new Date(endDate);

  if (isNaN(start.getTime())) {
    return { valid: false, error: 'Invalid start date' };
  }

  if (isNaN(end.getTime())) {
    return { valid: false, error: 'Invalid end date' };
  }

  if (start > end) {
    return { valid: false, error: 'Start date must be before end date' };
  }

  const diffDays = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (diffDays > 365) {
    return { valid: false, error: 'Date range too large (max 365 days)' };
  }

  return { valid: true };
};

export const validateHorizon = (days: number): { valid: boolean; error?: string } => {
  if (days < 1) {
    return { valid: false, error: 'Horizon must be at least 1 day' };
  }
  if (days > 365) {
    return { valid: false, error: 'Horizon cannot exceed 365 days' };
  }
  return { valid: true };
};
