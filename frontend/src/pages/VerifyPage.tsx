import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authApi } from '../api';
import { useAuth } from '../auth';
import { Spinner } from '../components';
import toast from 'react-hot-toast';

export function VerifyPage() {
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const verifyToken = async () => {
      // Extract token from URL hash (e.g., #/verify?token=xxx)
      const searchParams = new URLSearchParams(location.search);
      const token = searchParams.get('token');

      if (!token) {
        setError('No verification token provided');
        return;
      }

      try {
        const response = await authApi.verifyToken(token);
        await login(response.access_token);
        toast.success('Successfully signed in!');
        navigate('/', { replace: true });
      } catch {
        setError('Invalid or expired link. Please request a new one.');
      }
    };

    verifyToken();
  }, [location.search, login, navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full text-center">
          <div className="bg-white rounded-lg shadow-sm p-8">
            <div className="mx-auto h-12 w-12 text-red-500 mb-4">
              <svg
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Verification failed
            </h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <a
              href="#/login"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Back to login
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <Spinner size="lg" />
        <p className="mt-4 text-gray-600">Verifying your login...</p>
      </div>
    </div>
  );
}

export default VerifyPage;
