import { Router } from 'express';
import { z } from 'zod';
import { prisma } from '../prisma.js';
import { authRequired } from '../middleware/auth.js';
import { requireRoles } from '../middleware/rbac.js';
import { writeAuditLog } from '../services/audit.js';

const createPaymentSchema = z.object({
  studentId: z.string(),
  amount: z.number().positive(),
  paidAt: z.coerce.date(),
  type: z.enum(['CASH', 'CARD', 'TRANSFER', 'OTHER']).default('CASH'),
  note: z.string().optional(),
});

export const paymentsRouter = Router();
paymentsRouter.use(authRequired);

paymentsRouter.get('/payments', async (_req, res) => {
  const data = await prisma.payment.findMany({ include: { student: true, createdBy: true }, orderBy: { paidAt: 'desc' } });
  res.json(data);
});

paymentsRouter.post('/payments', requireRoles('SUPER_ADMIN', 'OFFICER'), async (req, res) => {
  const payload = createPaymentSchema.parse(req.body);

  const payment = await prisma.$transaction(async (tx) => {
    const created = await tx.payment.create({ data: { ...payload, createdById: req.user!.id } });
    await tx.student.update({ where: { id: payload.studentId }, data: { paidAmount: { increment: payload.amount } } });
    return created;
  });

  await writeAuditLog({ action: 'tolov_ozgartirildi', entity: 'payment', entityId: payment.id, newValue: payload, userId: req.user!.id });

  res.status(201).json(payment);
});
