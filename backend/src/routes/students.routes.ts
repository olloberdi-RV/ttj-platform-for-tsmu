import { Router } from 'express';
import { Prisma } from '@prisma/client';
import { prisma } from '../prisma.js';
import { authRequired } from '../middleware/auth.js';
import { requireRoles } from '../middleware/rbac.js';
import { studentCreateSchema, moveStudentSchema } from '../validators/student.js';
import { maskPinfl, paymentStatus, remainingAmount } from '../utils/student.js';
import { writeAuditLog } from '../services/audit.js';

export const studentsRouter = Router();

studentsRouter.use(authRequired);

studentsRouter.get('/students', async (req, res) => {
  const q = (req.query.q as string | undefined)?.trim();
  const where: Prisma.StudentWhereInput = { deletedAt: null };

  if (q) {
    where.OR = [
      { fullName: { contains: q, mode: 'insensitive' } },
      { pinfl: { contains: q } },
      { faculty: { contains: q, mode: 'insensitive' } },
      { phone: { contains: q } },
    ];
  }

  const data = await prisma.student.findMany({
    where,
    include: {
      sport: true,
      accommodations: {
        where: { isCurrent: true },
        include: { room: { include: { block: true, floor: true, building: true } }, bed: true },
      },
    },
    orderBy: { createdAt: 'desc' },
  });

  res.json(
    data.map((s) => {
      const current = s.accommodations[0];
      const isSensitiveAllowed = req.user?.role !== 'OBSERVER';
      return {
        id: s.id,
        fullName: s.fullName,
        pinfl: isSensitiveAllowed ? s.pinfl : maskPinfl(s.pinfl),
        faculty: s.faculty,
        course: s.course,
        phone: isSensitiveAllowed ? s.phone : '*********',
        room: current?.room.roomNumber,
        bed: current?.bed.bedNumber,
        payment: {
          total: Number(s.totalPayment),
          paid: Number(s.paidAmount),
          remaining: remainingAmount(Number(s.totalPayment), Number(s.paidAmount)),
          status: paymentStatus(Number(s.totalPayment), Number(s.paidAmount)),
        },
      };
    }),
  );
});

studentsRouter.post('/students', requireRoles('SUPER_ADMIN', 'OFFICER'), async (req, res) => {
  const payload = studentCreateSchema.parse(req.body);

  const duplicate = await prisma.student.findFirst({ where: { pinfl: payload.pinfl, status: 'ACTIVE', deletedAt: null } });
  if (duplicate) {
    const current = await prisma.studentAccommodation.findFirst({ where: { studentId: duplicate.id, isCurrent: true }, include: { room: true } });
    return res.status(409).json({ message: 'Ushbu JShShIR bo‘yicha faol talaba allaqachon mavjud.', room: current?.room.roomNumber ?? null });
  }

  const bed = await prisma.roomBed.findFirst({ where: { id: payload.bedId, roomId: payload.roomId, status: 'EMPTY', deletedAt: null } });
  if (!bed) return res.status(400).json({ message: 'Tanlangan o‘rin bo‘sh emas yoki mavjud emas' });

  const result = await prisma.$transaction(async (tx) => {
    const student = await tx.student.create({
      data: {
        fullName: payload.fullName,
        pinfl: payload.pinfl,
        faculty: payload.faculty,
        course: payload.course,
        phone: payload.phone,
        email: payload.email || null,
        gender: payload.gender,
        birthDate: payload.birthDate,
        privilege: payload.privilege,
        interest: payload.interest,
        totalPayment: payload.totalPayment,
        paidAmount: payload.paidAmount,
        sportId: payload.sportId,
      },
    });

    await tx.studentAccommodation.create({
      data: {
        studentId: student.id,
        roomId: payload.roomId,
        bedId: payload.bedId,
        movedInAt: new Date(),
        isCurrent: true,
      },
    });

    await tx.roomBed.update({ where: { id: payload.bedId }, data: { status: 'OCCUPIED' } });

    return student;
  });

  await writeAuditLog({
    action: 'talaba_qoshildi',
    entity: 'student',
    entityId: result.id,
    newValue: payload,
    userId: req.user!.id,
  });

  return res.status(201).json(result);
});

studentsRouter.put('/students/:id', requireRoles('SUPER_ADMIN', 'OFFICER'), async (req, res) => {
  const id = req.params.id;
  const old = await prisma.student.findUnique({ where: { id } });
  if (!old || old.deletedAt) return res.status(404).json({ message: 'Talaba topilmadi' });

  const payload = studentCreateSchema.partial().parse(req.body);

  const updated = await prisma.student.update({
    where: { id },
    data: {
      ...payload,
      email: payload.email || undefined,
    },
  });

  await writeAuditLog({
    action: 'talaba_tahrirlandi',
    entity: 'student',
    entityId: id,
    oldValue: old,
    newValue: updated,
    userId: req.user!.id,
  });

  res.json(updated);
});

studentsRouter.post('/students/:id/move', requireRoles('SUPER_ADMIN', 'OFFICER'), async (req, res) => {
  const id = req.params.id;
  const payload = moveStudentSchema.parse(req.body);

  const current = await prisma.studentAccommodation.findFirst({ where: { studentId: id, isCurrent: true } });
  if (!current) return res.status(404).json({ message: 'Talabaning joriy joylashuvi topilmadi' });

  const newBed = await prisma.roomBed.findFirst({ where: { id: payload.bedId, roomId: payload.roomId, status: 'EMPTY', deletedAt: null } });
  if (!newBed) return res.status(400).json({ message: 'Yangi o‘rin bo‘sh emas' });

  await prisma.$transaction(async (tx) => {
    await tx.studentAccommodation.update({ where: { id: current.id }, data: { isCurrent: false, movedOutAt: new Date() } });
    await tx.roomBed.update({ where: { id: current.bedId }, data: { status: 'EMPTY' } });

    await tx.studentAccommodation.create({
      data: {
        studentId: id,
        roomId: payload.roomId,
        bedId: payload.bedId,
        movedInAt: new Date(),
        isCurrent: true,
        note: payload.reason,
      },
    });

    await tx.roomBed.update({ where: { id: payload.bedId }, data: { status: 'OCCUPIED' } });
  });

  await writeAuditLog({
    action: 'talaba_kochirildi',
    entity: 'student_accommodation',
    entityId: id,
    oldValue: { roomId: current.roomId, bedId: current.bedId },
    newValue: { roomId: payload.roomId, bedId: payload.bedId },
    reason: payload.reason,
    userId: req.user!.id,
  });

  res.json({ message: 'Talaba ko‘chirildi' });
});

studentsRouter.post('/students/:id/discharge', requireRoles('SUPER_ADMIN', 'OFFICER'), async (req, res) => {
  const id = req.params.id;
  const status = (req.body.status as string | undefined) ?? 'DISCHARGED';

  const current = await prisma.studentAccommodation.findFirst({ where: { studentId: id, isCurrent: true } });

  await prisma.$transaction(async (tx) => {
    await tx.student.update({ where: { id }, data: { status: status as never } });
    if (current) {
      await tx.studentAccommodation.update({ where: { id: current.id }, data: { isCurrent: false, movedOutAt: new Date() } });
      await tx.roomBed.update({ where: { id: current.bedId }, data: { status: 'EMPTY' } });
    }
  });

  await writeAuditLog({
    action: 'talaba_ttjdan_chiqarildi',
    entity: 'student',
    entityId: id,
    newValue: { status },
    userId: req.user!.id,
  });

  res.json({ message: 'Talaba TTJdan chiqarildi' });
});

studentsRouter.get('/students/:id/history', async (req, res) => {
  const logs = await prisma.auditLog.findMany({ where: { entityId: req.params.id }, orderBy: { createdAt: 'desc' }, include: { user: true } });
  res.json(logs);
});
