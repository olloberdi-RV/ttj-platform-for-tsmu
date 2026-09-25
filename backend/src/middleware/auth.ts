import type { NextFunction, Request, Response } from 'express';
import { verifyAccessToken } from '../auth/jwt.js';

export function authRequired(req: Request, res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (!header || (!header.startsWith('Bearer ') && !header.startsWith('JWT '))) {
    return res.status(401).json({ message: 'Autentifikatsiya talab qilinadi' });
  }

  try {
    const token = header.startsWith('Bearer ') ? header.slice(7) : header.slice(4);
    req.user = verifyAccessToken(token);
    next();
  } catch {
    return res.status(401).json({ message: 'Token yaroqsiz' });
  }
}
