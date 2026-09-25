const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:4000/api';

function authHeaders() {
  const token = localStorage.getItem('ttj_access_token');
  return token ? { Authorization: `JWT ${token}` } : {};
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error('So‘rovda xatolik');
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error((await res.json()).message ?? 'So‘rovda xatolik');
  return res.json() as Promise<T>;
}
