import { PrismaClient, BedStatus, StudentStatus } from '@prisma/client';
import bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  const [superAdminRole, officerRole, observerRole] = await Promise.all([
    prisma.role.upsert({ where: { name: 'SUPER_ADMIN' }, update: {}, create: { name: 'SUPER_ADMIN', description: 'To‘liq huquq' } }),
    prisma.role.upsert({ where: { name: 'OFFICER' }, update: {}, create: { name: 'OFFICER', description: 'TTJ mas’ul xodimi' } }),
    prisma.role.upsert({ where: { name: 'OBSERVER' }, update: {}, create: { name: 'OBSERVER', description: 'Faqat ko‘rish' } }),
  ]);

  const passwordHash = await bcrypt.hash('Admin123!@#', 12);
  await prisma.user.upsert({
    where: { username: 'admin' },
    update: {},
    create: { fullName: 'Super Admin', username: 'admin', passwordHash, roleId: superAdminRole.id },
  });

  for (let b = 1; b <= 3; b += 1) {
    const existingBuilding = await prisma.building.findFirst({ where: { number: `TTJ-${b}`, deletedAt: null } });
    const building = existingBuilding
      ?? (await prisma.building.create({ data: { name: `${b}-TTJ`, number: `TTJ-${b}`, address: `Manzil ${b}`, floorCount: 3 } }));

    for (const blockName of ['A', 'B']) {
      const existingBlock = await prisma.block.findFirst({ where: { buildingId: building.id, number: blockName, deletedAt: null } });
      const block = existingBlock ?? (await prisma.block.create({ data: { name: `${blockName} blok`, number: blockName, buildingId: building.id } }));

      for (let floorNo = 1; floorNo <= 3; floorNo += 1) {
        const existingFloor = await prisma.floor.findFirst({ where: { blockId: block.id, floorNumber: floorNo, deletedAt: null } });
        const floor = existingFloor ?? (await prisma.floor.create({ data: { floorNumber: floorNo, roomCount: 10, blockId: block.id } }));

        for (let roomNo = 1; roomNo <= 10; roomNo += 1) {
          const roomNumber = `${floorNo}${String(roomNo).padStart(2, '0')}`;
          const existingRoom = await prisma.room.findFirst({ where: { floorId: floor.id, roomNumber, deletedAt: null } });
          const room = existingRoom ?? (await prisma.room.create({
            data: {
              roomNumber,
              roomType: 'Oddiy',
              capacity: 4,
              buildingId: building.id,
              blockId: block.id,
              floorId: floor.id,
            },
          }));

          for (let bedNo = 1; bedNo <= 4; bedNo += 1) {
            const existingBed = await prisma.roomBed.findFirst({ where: { roomId: room.id, bedNumber: bedNo, deletedAt: null } });
            if (!existingBed) {
              await prisma.roomBed.create({ data: { roomId: room.id, bedNumber: bedNo, status: BedStatus.EMPTY } });
            }
          }
        }
      }
    }
  }

  const sports = await Promise.all([
    prisma.sport.upsert({ where: { name: 'Futbol' }, update: {}, create: { name: 'Futbol' } }),
    prisma.sport.upsert({ where: { name: 'Voleybol' }, update: {}, create: { name: 'Voleybol' } }),
    prisma.sport.upsert({ where: { name: 'Shaxmat' }, update: {}, create: { name: 'Shaxmat' } }),
  ]);

  const rooms = await prisma.room.findMany({ include: { beds: true }, take: 20 });
  for (let i = 1; i <= 50; i += 1) {
    const room = rooms[i % rooms.length];
    const bed = room.beds.find((b) => b.status === BedStatus.EMPTY);
    if (!bed) continue;

    const student = await prisma.student.create({
      data: {
        fullName: `Talaba ${i}`,
        pinfl: `1234567890${String(i).padStart(4, '0')}`,
        faculty: i % 2 === 0 ? 'Davolash' : 'Pediatriya',
        course: (i % 6) + 1,
        phone: `+99890${String(1000000 + i).slice(-7)}`,
        gender: i % 2 === 0 ? 'Erkak' : 'Ayol',
        birthDate: new Date('2003-01-01'),
        privilege: i % 3 === 0 ? 'Yetimlik maqomi' : null,
        interest: 'Kitob o‘qish',
        totalPayment: 2400000,
        paidAmount: 1600000,
        sportId: sports[i % sports.length].id,
        status: StudentStatus.ACTIVE,
      },
    });

    await prisma.studentAccommodation.create({
      data: {
        studentId: student.id,
        roomId: room.id,
        bedId: bed.id,
        movedInAt: new Date(),
        isCurrent: true,
      },
    });

    await prisma.roomBed.update({ where: { id: bed.id }, data: { status: BedStatus.OCCUPIED } });
  }

  console.log('Seed finished');
}

main().finally(() => prisma.$disconnect());
