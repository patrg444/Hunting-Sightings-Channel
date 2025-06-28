import { useState } from 'react';
import { X, Mail, Lock, Loader2, AlertCircle } from 'lucide-react';
import { authService } from '../../services/auth';
import { useStore } from '../../store/store';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'signup' | 'magic-link'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const setUser = useStore(state => state.setUser);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (mode === 'login') {
        const { user } = await authService.login({ email, password });
        if (user) {
          setUser({
            id: user.id,
            email: user.email!,
            created_at: user.created_at,
          });
          onClose();
        }
      } else if (mode === 'signup') {
        const { user } = await authService.signup({ email, password });
        if (user) {
          setSuccess(true);
          setTimeout(() => {
            setMode('login');
            setSuccess(false);
          }, 3000);
        }
      } else if (mode === 'magic-link') {
        await authService.sendMagicLink(email);
        setSuccess(true);
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setError(null);
    setSuccess(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {mode === 'login' ? 'Sign In' : mode === 'signup' ? 'Create Account' : 'Magic Link'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {success ? (
          <div className="text-center py-8">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
              <Mail className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              {mode === 'signup' ? 'Account Created!' : 'Check Your Email'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              {mode === 'signup' 
                ? 'You can now sign in with your email and password.'
                : 'We sent you a magic link to sign in.'}
            </p>
          </div>
        ) : (
          <>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  <Mail className="w-4 h-4 inline mr-1" />
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              </div>

              {mode !== 'magic-link' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    <Lock className="w-4 h-4 inline mr-1" />
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    required={mode !== 'magic-link'}
                    minLength={6}
                  />
                  {mode === 'signup' && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Password must be at least 6 characters
                    </p>
                  )}
                </div>
              )}

              {error && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start">
                  <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0" />
                  <span className="text-sm text-red-700 dark:text-red-300">{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {mode === 'login' ? 'Signing in...' : mode === 'signup' ? 'Creating account...' : 'Sending link...'}
                  </>
                ) : (
                  <>
                    {mode === 'login' ? 'Sign In' : mode === 'signup' ? 'Create Account' : 'Send Magic Link'}
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 space-y-3">
              {mode === 'login' && (
                <>
                  <button
                    onClick={() => {
                      setMode('magic-link');
                      resetForm();
                    }}
                    className="w-full text-center text-sm text-green-600 hover:text-green-700"
                  >
                    Sign in with Magic Link
                  </button>
                  <button
                    onClick={() => {
                      setMode('signup');
                      resetForm();
                    }}
                    className="w-full text-center text-sm text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    Don't have an account? <span className="text-green-600">Create one</span>
                  </button>
                </>
              )}

              {mode === 'signup' && (
                <button
                  onClick={() => {
                    setMode('login');
                    resetForm();
                  }}
                  className="w-full text-center text-sm text-gray-600 hover:text-gray-700"
                >
                  Already have an account? <span className="text-green-600">Sign in</span>
                </button>
              )}

              {mode === 'magic-link' && (
                <button
                  onClick={() => {
                    setMode('login');
                    resetForm();
                  }}
                  className="w-full text-center text-sm text-gray-600 hover:text-gray-700"
                >
                  Back to email & password login
                </button>
              )}
            </div>

            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <p className="text-center text-sm text-gray-500 dark:text-gray-400">
                Google login is coming soon
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}