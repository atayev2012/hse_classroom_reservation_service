import { Mail } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import AuthLayout from '../components/AuthLayout.jsx';
import { authApi } from '../utils/api.js';
import { setPendingUserId, setStoredUser } from '../utils/storage.js';
import { normalizeRole } from '../utils/access.js';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const isCorporate = /@(hse\.ru|edu\.hse\.ru)$/i.test(email);

  useEffect(() => {
    let mounted = true;
    authApi.me()
      .then((user) => {
        if (!mounted) return;
        setStoredUser({
          id: user?.id || user?.user_id,
          email: user?.email,
          type: normalizeRole(user?.role || user?.type) || 'student'
        });
        navigate('/dashboard', { replace: true });
      })
      .catch(() => {});

    return () => { mounted = false; };
  }, [navigate]);

  async function submit(event) {
    event.preventDefault();
    setError('');
    if (!isCorporate) {
      setError('Почта только в доменах hse.ru и edu.hse.ru');
      return;
    }
    setLoading(true);
    try {
      const response = await authApi.login(email);
      setPendingUserId(response.user_id);
      navigate('/verify');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Вход в систему" subtitle="Сервис расписаний и бронирования аудиторий">
      <form className="auth-form" onSubmit={submit}>
        <label className={`auth-input ${error ? 'has-error' : ''} ${email ? 'is-filled' : ''}`}>
          <input
            type="email"
            placeholder="Электронная почта"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <Mail size={17} />
        </label>
        <div className={`auth-hint ${error ? 'auth-hint--error' : ''}`}>
          {error || 'Используйте только корпоративную почту'}
        </div>
        <button className="auth-submit" type="submit" disabled={loading || !email}>
          {loading ? 'Отправка...' : 'Далее'}
        </button>
      </form>
    </AuthLayout>
  );
}
