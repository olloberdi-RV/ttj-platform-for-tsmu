import { Router } from 'express';
import { prisma } from '../prisma.js';
import { authRequired } from '../middleware/auth.js';

export const dashboardRouter = Router();
dashboardRouter.use(authRequired);

dashboardRouter.get('/dashboard/stats', async (_req, res) => {
  const [buildings, blocks, rooms, beds, activeStudents, sumPayments, paidPayments, recentLogs, studentPayments] = await Promise.all([
    prisma.building.count({ where: { deletedAt: null } }),
    prisma.block.count({ where: { deletedAt: null } }),
    prisma.room.count({ where: { deletedAt: null } }),
    prisma.roomBed.count({ where: { deletedAt: null } }),
    prisma.student.count({ where: { deletedAt: null, status: 'ACTIVE' } }),
    prisma.student.aggregate({ _sum: { totalPayment: true }, where: { deletedAt: null } }),
    prisma.student.aggregate({ _sum: { paidAmount: true }, where: { deletedAt: null } }),
    prisma.auditLog.findMany({ take: 10, orderBy: { createdAt: 'desc' }, include: { user: true } }),
    prisma.student.findMany({ where: { deletedAt: null, status: 'ACTIVE' }, select: { totalPayment: true, paidAmount: true } }),
  ]);

  const occupied = await prisma.roomBed.count({ where: { status: 'OCCUPIED', deletedAt: null } });
  const empty = await prisma.roomBed.count({ where: { status: 'EMPTY', deletedAt: null } });

  const total = Number(sumPayments._sum.totalPayment ?? 0);
  const paid = Number(paidPayments._sum.paidAmount ?? 0);
  const debtors = studentPayments.filter((s) => Number(s.totalPayment) > Number(s.paidAmount)).length;

  res.json({
    buildings,
    blocks,
    rooms,
    beds,
    occupied,
    empty,
    occupancyPercent: beds ? Number(((occupied / beds) * 100).toFixed(2)) : 0,
    students: activeStudents,
    debtors,
    totalPayment: total,
    paidPayment: paid,
    debt: total - paid,
    recentLogs,
  });
});
