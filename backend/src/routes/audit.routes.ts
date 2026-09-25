import { Router } from 'express';
import { prisma } from '../prisma.js';
import { authRequired } from '../middleware/auth.js';
import { requireRoles } from '../middleware/rbac.js';

export const auditRouter = Router();
auditRouter.use(authRequired, requireRoles('SUPER_ADMIN', 'OFFICER'));

auditRouter.get('/audit-logs', async (_req, res) => {
  const logs = await prisma.auditLog.findMany({ include: { user: true }, orderBy: { createdAt: 'desc' }, take: 500 });
  res.json(logs);
});
