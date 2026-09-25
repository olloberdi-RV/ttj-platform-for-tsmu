import { useState } from 'react';
import { apiPost } from '../services/api';

interface Props {
  onSuccess: () => void;
}

export function LoginForm({ onSuccess }: Props) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('Admin123!@#');
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');

  return (
    <form
      className="mx-auto mt-10 w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow"
      onSubmit={async (e) => {
        e.preventDefault();
        setError('');
        try {
          const data = await apiPost<{ accessToken: string; refreshToken: string }>('/auth/login', { username, password });
          localStorage.setItem('ttj_access_token', data.accessToken);
          if (remember) localStorage.setItem('ttj_refresh_token', data.refreshToken);
          onSuccess();
        } catch {
          setError('Login yoki parol noto‘g‘ri.');
        }
      }}
    >
      <h1 className="mb-1 text-xl font-semibold">TTJ boshqaruv tizimi</h1>
      <p className="mb-4 text-sm text-slate-600">Universitet/TTJ administratsiyasi kirish oynasi</p>
      <label className="mb-3 block text-sm">Login
        <input className="mt-1 w-full rounded border px-3 py-2" value={username} onChange={(e) => setUsername(e.target.value)} />
      </label>
      <label className="mb-3 block text-sm">Parol
        <input className="mt-1 w-full rounded border px-3 py-2" type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} />
      </label>
      <div className="mb-3 flex items-center justify-between text-sm">
        <label className="flex items-center gap-2"><input type="checkbox" checked={showPassword} onChange={(e) => setShowPassword(e.target.checked)} /> Parolni ko‘rsatish</label>
        <label className="flex items-center gap-2"><input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} /> Meni eslab qolish</label>
      </div>
      {error && <p className="mb-3 rounded bg-red-50 p-2 text-sm text-red-600">{error}</p>}
      <button className="w-full rounded bg-slate-900 px-4 py-2 text-white">Kirish</button>
      <button type="button" className="mt-2 w-full text-sm text-blue-700">Parolni tiklash</button>
    </form>
  );
}
