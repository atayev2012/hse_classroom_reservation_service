import { LogIn, MoveLeft } from 'lucide-react';
import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import AuthLayout from '../components/AuthLayout.jsx';
import { authApi } from '../utils/api.js';
import { getPendingUserId, setStoredUser } from '../utils/storage.js';
import { decodeTokenPayload, normalizeRole } from '../utils/access.js';

export default function VerificationPage() {
  const [digits, setDigits] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const inputsRef = useRef([]);
  const navigate = useNavigate();

  function updateDigit(index, value) {
    const nextValue = value.replace(/\D/g, '').slice(-1);
    const next = [...digits];
    next[index] = nextValue;
    setDigits(next);
    if (nextValue && index < 5) inputsRef.current[index + 1]?.focus();
  }

  async function submit(event) {
    event.preventDefault();
    const code = digits.join('');
    if (code.length !== 6) return;
    setError('');
    try {
      const userId = getPendingUserId();
      const response = await authApi.verify(userId, code);
      setStoredUser({ id: userId });
      if (!response.success) {
        setError(response.status || 'Был введен неправильный код');
        return;
      }
      const payload = decodeTokenPayload(response.access_token);
      const currentUser = await authApi.me().catch(() => null);
      setStoredUser({
        id: currentUser?.id || payload?.user_id || userId,
        email: currentUser?.email || payload?.email,
        type: normalizeRole(currentUser?.role || currentUser?.type || payload?.role || payload?.user_type || payload?.type) || 'student'
      });
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Был введен неправильный код');
    }
  }

  return (
    <AuthLayout title="Верификация" subtitle="Введите шестизначный код полученный по электронной почте">
      <form className="verify-form" onSubmit={submit}>
        <div className="code-inputs">
          {digits.map((digit, index) => (
            <input
              aria-label={`Цифра ${index + 1}`}
              key={index}
              maxLength={1}
              ref={(element) => { inputsRef.current[index] = element; }}
              value={digit}
              onChange={(event) => updateDigit(index, event.target.value)}
            />
          ))}
        </div>
        <div className={`auth-hint ${error ? 'auth-hint--error' : ''}`}>
          {error || 'Код действует только 15 минут'}
        </div>
        <button className="auth-submit" type="submit" disabled={digits.join('').length !== 6}>
          <LogIn size={18} />
          Войти
        </button>
        <button className="back-link" type="button" onClick={() => navigate('/login')}>
          <MoveLeft size={18} />
          Назад
        </button>
      </form>
    </AuthLayout>
  );
}
