import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '@/core/auth/auth-context';

export function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [formState, setFormState] = useState({
    email: 'admin.demo@example.com',
    password: 'AdminPass123!',
  });
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setErrorMessage('');
    setIsSubmitting(true);

    try {
      await auth.login(formState);
      navigate('/', { replace: true });
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="login-shell">
      <section className="login-card">
        <div className="login-copy">
          <p className="eyebrow">Operations Access</p>
          <h1>Admin panel sign-in</h1>
          <p>
            Use an account with the `admin` role. The backend rejects generic marketplace accounts here.
          </p>
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={formState.email}
              onChange={(event) => setFormState((current) => ({ ...current, email: event.target.value }))}
              required
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={formState.password}
              onChange={(event) => setFormState((current) => ({ ...current, password: event.target.value }))}
              required
            />
          </label>

          {errorMessage ? <div className="form-error">{errorMessage}</div> : null}

          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
      </section>
    </div>
  );
}
