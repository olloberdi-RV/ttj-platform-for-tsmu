import type { NextFunction, Request, Response } from 'express';
import type { AppRole } from '../types.js';

export function requireRoles(...roles: AppRole[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) return res.status(401).json({ message: 'Kirish kerak' });
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ message: 'Sizda bu amal uchun ruxsat yo‘q' });
    }
    return next();
  };
}
