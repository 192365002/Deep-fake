// ─── Auth Page (Supabase Auth: Sign In, Sign Up, Google OAuth, Password Reset) ───
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function AuthPage() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const { login, signUp, loginWithGoogle, resetPassword } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (isForgotPassword) {
      if (!email) {
        setError('Please enter your email address to receive reset instructions.');
        return;
      }
      setLoading(true);
      try {
        const res = await resetPassword(email);
        setSuccessMsg(res.message || 'Password reset link sent to your email inbox.');
      } catch (err) {
        setError(err?.message || 'Failed to send password reset email.');
      } finally {
        setLoading(false);
      }
      return;
    }

    if (!email || !password) {
      setError('Email and password are required.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    try {
      if (isSignUp) {
        const res = await signUp(email, password, fullName);
        if (res?.requiresEmailConfirmation) {
          setSuccessMsg(res.message);
          setLoading(false);
          return;
        }
      } else {
        await login(email, password);
      }
      navigate('/home');
    } catch (err) {
      let msg = err?.message || 'Authentication failed. Please verify credentials.';
      if (msg.includes('Invalid login credentials')) {
        msg = 'Invalid email or password. Please try again or reset your password.';
      } else if (msg.includes('Email not confirmed')) {
        msg = 'Please check your email and click the confirmation link before signing in.';
      } else if (msg.includes('User already registered')) {
        msg = 'An account with this email already exists. Please sign in instead.';
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError('');
    setSuccessMsg('');
    try {
      await loginWithGoogle();
      navigate('/home');
    } catch (err) {
      setError(err?.message || 'Google OAuth sign-in failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card animate-fade-up">
        {/* Logo */}
        <div className="auth-logo">
          <div className="logo-icon">🛡️</div>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700 }}>SocialShield</span>
        </div>

        <h1 style={{ textAlign: 'center', fontSize: 24, fontWeight: 800, marginBottom: 6 }}>
          {isForgotPassword ? 'Reset Password' : (isSignUp ? 'Create Account' : 'Welcome Back')}
        </h1>
        <p style={{ textAlign: 'center', color: 'rgba(255,255,255,0.45)', fontSize: 14, marginBottom: 24 }}>
          {isForgotPassword
            ? 'Enter your email to receive recovery instructions'
            : (isSignUp
              ? 'Join the fight against digital fraud with Supabase security'
              : 'Sign in to access your secure multi-device dashboard')}
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Full Name (Sign Up only) */}
          {isSignUp && (
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', fontSize: 16 }}>👤</span>
              <input
                id="full-name"
                type="text"
                className="input-field"
                placeholder="Full Name (optional)"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                style={{ paddingLeft: 40 }}
                autoComplete="name"
              />
            </div>
          )}

          {/* Email */}
          <div style={{ position: 'relative' }}>
            <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', fontSize: 16 }}>✉️</span>
            <input
              id="email"
              type="email"
              className="input-field"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{ paddingLeft: 40 }}
              autoComplete="email"
              required
            />
          </div>

          {/* Password (not needed for forgot password) */}
          {!isForgotPassword && (
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', fontSize: 16 }}>🔒</span>
              <input
                id="password"
                type={showPass ? 'text' : 'password'}
                className="input-field"
                placeholder="Password (min 6 characters)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ paddingLeft: 40, paddingRight: 44 }}
                autoComplete={isSignUp ? 'new-password' : 'current-password'}
                required
              />
              <button
                type="button"
                onClick={() => setShowPass((v) => !v)}
                style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 16 }}
                aria-label="Toggle password visibility"
              >
                {showPass ? '🙈' : '👁️'}
              </button>
            </div>
          )}

          {/* Forgot Password link */}
          {!isSignUp && !isForgotPassword && (
            <div style={{ textAlign: 'right', marginTop: -4 }}>
              <button
                type="button"
                onClick={() => { setIsForgotPassword(true); setError(''); setSuccessMsg(''); }}
                style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.45)', cursor: 'pointer', fontSize: 12 }}
              >
                Forgot password?
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div style={{ color: 'var(--risk-high)', fontSize: 13, textAlign: 'center', padding: '8px 12px', background: 'rgba(255,59,59,0.08)', borderRadius: 8, border: '1px solid rgba(255,59,59,0.2)' }}>
              {error}
            </div>
          )}

          {/* Success Message */}
          {successMsg && (
            <div style={{ color: '#06FFA5', fontSize: 13, textAlign: 'center', padding: '8px 12px', background: 'rgba(6,255,165,0.08)', borderRadius: 8, border: '1px solid rgba(6,255,165,0.2)' }}>
              {successMsg}
            </div>
          )}

          <button id="submit-btn" type="submit" className="btn-neon" style={{ width: '100%', marginTop: 4 }} disabled={loading}>
            {loading ? <span className="spinner" /> : (
              isForgotPassword ? 'Send Recovery Link' : (isSignUp ? 'Create Supabase Account' : 'Sign In')
            )}
          </button>
        </form>

        {/* Back to sign in button if on forgot password */}
        {isForgotPassword ? (
          <p style={{ textAlign: 'center', marginTop: 20, fontSize: 14, color: 'rgba(255,255,255,0.4)' }}>
            Remembered your credentials?{' '}
            <button
              style={{ background: 'none', border: 'none', color: 'var(--neon-blue)', cursor: 'pointer', fontWeight: 600, fontSize: 14 }}
              onClick={() => { setIsForgotPassword(false); setError(''); setSuccessMsg(''); }}
            >
              Sign In
            </button>
          </p>
        ) : (
          <>
            <div className="divider" style={{ margin: '20px 0' }}>or</div>

            <button
              id="google-signin-btn"
              className="btn-neon btn-outline"
              style={{ width: '100%' }}
              onClick={handleGoogleSignIn}
              disabled={loading}
            >
              <span style={{ fontSize: 18 }}>🇬</span> Continue with Google
            </button>

            <p style={{ textAlign: 'center', marginTop: 20, fontSize: 14, color: 'rgba(255,255,255,0.4)' }}>
              {isSignUp ? 'Already have an account?' : "Don't have an account?"}
              {' '}
              <button
                style={{ background: 'none', border: 'none', color: 'var(--neon-blue)', cursor: 'pointer', fontWeight: 600, fontSize: 14 }}
                onClick={() => { setIsSignUp((v) => !v); setError(''); setSuccessMsg(''); }}
              >
                {isSignUp ? 'Sign In' : 'Sign Up'}
              </button>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
