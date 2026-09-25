import { z } from 'zod';

export const studentCreateSchema = z.object({
  fullName: z.string().min(3),
  pinfl: z.string().regex(/^\d{14}$/),
  faculty: z.string().min(2),
  course: z.number().int().min(1).max(7),
  phone: z.string().regex(/^\+998\d{9}$/),
  email: z.string().email().optional().or(z.literal('')),
  gender: z.string().min(2),
  birthDate: z.coerce.date(),
  buildingId: z.string().min(1),
  blockId: z.string().min(1),
  floorId: z.string().min(1),
  roomId: z.string().min(1),
  bedId: z.string().min(1),
  privilege: z.string().optional(),
  interest: z.string().optional(),
  totalPayment: z.number().nonnegative(),
  paidAmount: z.number().nonnegative(),
  sportId: z.string().optional(),
});

export const moveStudentSchema = z.object({
  buildingId: z.string().min(1),
  blockId: z.string().min(1),
  floorId: z.string().min(1),
  roomId: z.string().min(1),
  bedId: z.string().min(1),
  reason: z.string().optional(),
});
