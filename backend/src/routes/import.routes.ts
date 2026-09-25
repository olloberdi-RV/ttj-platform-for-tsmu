import { Router } from 'express';
import multer from 'multer';
import xlsx from 'xlsx';
import mammoth from 'mammoth';
import { parse as parseCsv } from 'csv-parse/sync';
import { authRequired } from '../middleware/auth.js';
import { requireRoles } from '../middleware/rbac.js';
import { prisma } from '../prisma.js';

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 },
});

const expectedFields = ['fullName', 'pinfl', 'faculty', 'course', 'roomNumber', 'sport', 'privilege', 'totalPayment', 'paidAmount'];

function validateRow(row: Record<string, string>, usedPinfls: Set<string>) {
  const errors: Array<{ field: string; message: string }> = [];
  if (!row.fullName) errors.push({ field: 'fullName', message: 'F.I.O majburiy' });
  if (!/^\d{14}$/.test(String(row.pinfl || ''))) errors.push({ field: 'pinfl', message: 'JShShIR 14 raqam bo‘lishi kerak' });
  if (usedPinfls.has(row.pinfl)) errors.push({ field: 'pinfl', message: 'Takroriy JShShIR' });
  if (!(Number(row.course) >= 1 && Number(row.course) <= 7)) errors.push({ field: 'course', message: 'Kurs noto‘g‘ri' });
  if (Number(row.totalPayment) < 0 || Number(row.paidAmount) < 0) errors.push({ field: 'payment', message: 'Summa musbat bo‘lishi kerak' });
  return errors;
}

export const importRouter = Router();
importRouter.use(authRequired, requireRoles('SUPER_ADMIN', 'OFFICER'));

importRouter.get('/import/template', (_req, res) => {
  res.json({ fields: expectedFields });
});

async function handleImport(rows: Array<Record<string, string>>, fileName: string, fileType: string, userId: string, preview: boolean) {
  const errors: Array<{ rowNumber: number; field: string; message: string }> = [];
  const usedPinfls = new Set<string>();

  for (const [i, row] of rows.entries()) {
    const rowErrors = validateRow(row, usedPinfls);
    usedPinfls.add(row.pinfl);

    const existing = await prisma.student.findFirst({ where: { pinfl: row.pinfl, status: 'ACTIVE', deletedAt: null } });
    if (existing) rowErrors.push({ field: 'pinfl', message: 'Bu JShShIR bo‘yicha faol talaba mavjud' });

    const room = await prisma.room.findFirst({ where: { roomNumber: row.roomNumber, deletedAt: null }, include: { beds: true } });
    if (!room) rowErrors.push({ field: 'roomNumber', message: 'Mavjud bo‘lmagan xona' });
    if (room && room.beds.every((b) => b.status !== 'EMPTY')) rowErrors.push({ field: 'roomNumber', message: 'Xona sig‘imi to‘lgan' });

    for (const e of rowErrors) errors.push({ rowNumber: i + 2, field: e.field, message: e.message });
  }

  if (preview) {
    return {
      totalRows: rows.length,
      successRows: rows.length - errors.length,
      failedRows: errors.length,
      errors,
    };
  }

  const importJob = await prisma.importJob.create({
    data: {
      fileName,
      fileType,
      totalRows: rows.length,
      successRows: rows.length - errors.length,
      failedRows: errors.length,
      uploadedById: userId,
    },
  });

  if (errors.length > 0) {
    await prisma.importError.createMany({
      data: errors.map((e) => ({ importJobId: importJob.id, rowNumber: e.rowNumber, field: e.field, message: e.message })),
    });
    return { importJobId: importJob.id, stopped: true, ...importJob };
  }

  for (const row of rows) {
    const room = await prisma.room.findFirst({ where: { roomNumber: row.roomNumber, deletedAt: null }, include: { beds: true } });
    if (!room) continue;
    const bed = room.beds.find((b) => b.status === 'EMPTY');
    if (!bed) continue;

    const student = await prisma.student.create({
      data: {
        fullName: row.fullName,
        pinfl: row.pinfl,
        faculty: row.faculty,
        course: Number(row.course),
        phone: '+998900000000',
        gender: 'Noma’lum',
        birthDate: new Date('2000-01-01'),
        privilege: row.privilege,
        totalPayment: Number(row.totalPayment),
        paidAmount: Number(row.paidAmount),
        interest: null,
      },
    });

    await prisma.studentAccommodation.create({
      data: { studentId: student.id, roomId: room.id, bedId: bed.id, movedInAt: new Date(), isCurrent: true },
    });

    await prisma.roomBed.update({ where: { id: bed.id }, data: { status: 'OCCUPIED' } });
  }

  return { importJobId: importJob.id, stopped: false };
}

importRouter.post('/import/xlsx', upload.single('file'), async (req, res) => {
  if (!req.file) return res.status(400).json({ message: 'Fayl topilmadi' });
  const allowed = ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv'];
  if (!allowed.includes(req.file.mimetype)) return res.status(400).json({ message: 'Noto‘g‘ri MIME turi' });

  let rows: Array<Record<string, string>> = [];
  if (req.file.mimetype === 'text/csv') {
    rows = parseCsv(req.file.buffer.toString('utf8'), { columns: true, skip_empty_lines: true });
  } else {
    const wb = xlsx.read(req.file.buffer, { type: 'buffer' });
    const ws = wb.Sheets[wb.SheetNames[0]];
    rows = xlsx.utils.sheet_to_json(ws);
  }

  const preview = req.query.preview === 'true';
  const result = await handleImport(rows, req.file.originalname, req.file.mimetype, req.user!.id, preview);
  res.json(result);
});

importRouter.post('/import/docx', upload.single('file'), async (req, res) => {
  if (!req.file) return res.status(400).json({ message: 'Fayl topilmadi' });
  if (req.file.mimetype !== 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    return res.status(400).json({ message: 'Faqat DOCX format ruxsat etiladi' });
  }

  const text = (await mammoth.extractRawText({ buffer: req.file.buffer })).value;
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
  if (lines.length < 2) return res.status(400).json({ message: 'DOCX formati bo‘sh' });

  const headers = lines[0].split('|').map((v) => v.trim());
  const rows = lines.slice(1).map((line) => {
    const values = line.split('|').map((v) => v.trim());
    return Object.fromEntries(headers.map((h, i) => [h, values[i] ?? '']));
  }) as Array<Record<string, string>>;

  const preview = req.query.preview === 'true';
  const result = await handleImport(rows, req.file.originalname, req.file.mimetype, req.user!.id, preview);
  res.json(result);
});

importRouter.get('/imports', async (_req, res) => {
  const jobs = await prisma.importJob.findMany({ include: { errors: true, uploadedBy: true }, orderBy: { createdAt: 'desc' } });
  res.json(jobs);
});
