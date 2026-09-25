import jwt from 'jsonwebtoken';
import type { AuthUser } from '../types.js';

const ACCESS_SECRET = process.env.JWT_ACCESS_SECRET ?? 'dev-access-secret';
const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET ?? 'dev-refresh-secret';

export function signAccessToken(user: AuthUser) {
  return jwt.sign(user, ACCESS_SECRET, { expiresIn: '1h' });
}

export function signRefreshToken(user: AuthUser) {
  return jwt.sign(user, REFRESH_SECRET, { expiresIn: '7d' });
}

export function verifyAccessToken(token: string): AuthUser {
  return jwt.verify(token, ACCESS_SECRET) as AuthUser;
}
