import { Router } from 'express';
import bcrypt from 'bcrypt';
import { prisma } from '../prisma.js';
import { signAccessToken, signRefreshToken } from '../auth/jwt.js';

export const authRouter = Router();

authRouter.post('/login', async (req, res) => {
  const { username, password } = req.body as { username: string; password: string };

  const user = await prisma.user.findUnique({ where: { username }, include: { role: true } });
  if (!user) return res.status(401).json({ message: 'Login yoki parol xato' });

  const ok = await bcrypt.compare(password, user.passwordHash);
  if (!ok) return res.status(401).json({ message: 'Login yoki parol xato' });

  const payload = { id: user.id, username: user.username, role: user.role.name as 'SUPER_ADMIN' | 'OFFICER' | 'OBSERVER' };
  const accessToken = signAccessToken(payload);
  const refreshToken = signRefreshToken(payload);

  return res.json({
    accessToken,
    refreshToken,
    user: {
      id: user.id,
      fullName: user.fullName,
      username: user.username,
      role: user.role.name,
    },
  });
});
