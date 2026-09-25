import { prisma } from '../prisma.js';

interface AuditParams {
  action: string;
  entity: string;
  entityId?: string;
  oldValue?: unknown;
  newValue?: unknown;
  reason?: string;
  userId: string;
}

export async function writeAuditLog(payload: AuditParams) {
  await prisma.auditLog.create({ data: payload });
}
