import { useNavigate } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';
import { Button } from '../components/common';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-9xl font-bold text-dark-600">404</h1>
      <h2 className="text-2xl font-semibold text-text-primary mt-4">
        Page Not Found
      </h2>
      <p className="text-text-muted mt-2 max-w-md">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div className="flex gap-4 mt-8">
        <Button variant="secondary" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Go Back
        </Button>
        <Button onClick={() => navigate('/')}>
          <Home className="w-4 h-4 mr-2" />
          Home
        </Button>
      </div>
    </div>
  );
}
