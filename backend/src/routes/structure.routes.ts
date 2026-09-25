import { Router } from 'express';
import { prisma } from '../prisma.js';
import { authRequired } from '../middleware/auth.js';

export const structureRouter = Router();

structureRouter.use(authRequired);

structureRouter.get('/buildings', async (_req, res) => {
  const data = await prisma.building.findMany({ where: { deletedAt: null }, orderBy: { number: 'asc' } });
  res.json(data);
});

structureRouter.get('/blocks', async (req, res) => {
  const buildingId = req.query.buildingId as string | undefined;
  const data = await prisma.block.findMany({ where: { deletedAt: null, ...(buildingId ? { buildingId } : {}) }, orderBy: { number: 'asc' } });
  res.json(data);
});

structureRouter.get('/floors', async (req, res) => {
  const blockId = req.query.blockId as string | undefined;
  const data = await prisma.floor.findMany({ where: { deletedAt: null, ...(blockId ? { blockId } : {}) }, orderBy: { floorNumber: 'asc' } });
  res.json(data);
});

structureRouter.get('/rooms', async (req, res) => {
  const floorId = req.query.floorId as string | undefined;
  const data = await prisma.room.findMany({
    where: { deletedAt: null, ...(floorId ? { floorId } : {}) },
    include: { beds: true, block: true, floor: true },
    orderBy: { roomNumber: 'asc' },
  });

  const mapped = data.map((room) => {
    const occupied = room.beds.filter((b) => b.status === 'OCCUPIED').length;
    const empty = room.beds.filter((b) => b.status === 'EMPTY').length;
    return {
      ...room,
      occupiedBeds: occupied,
      emptyBeds: empty,
      occupancyPercent: room.capacity ? Math.round((occupied / room.capacity) * 100) : 0,
    };
  });

  res.json(mapped);
});

structureRouter.get('/rooms/:id', async (req, res) => {
  const room = await prisma.room.findUnique({
    where: { id: req.params.id },
    include: {
      building: true,
      block: true,
      floor: true,
      beds: {
        include: {
          accommodation: {
            where: { isCurrent: true },
            include: { student: true },
          },
        },
        orderBy: { bedNumber: 'asc' },
      },
    },
  });

  if (!room || room.deletedAt) return res.status(404).json({ message: 'Xona topilmadi' });
  res.json(room);
});
