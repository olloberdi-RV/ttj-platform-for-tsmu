# Database sxema (Prisma/PostgreSQL)

Asosiy jadvallar:
- users
- roles
- buildings
- blocks
- floors
- rooms
- room_beds
- students
- student_accommodation
- payments
- sports
- audit_logs
- imports
- import_errors

Soft delete uchun `deletedAt` va biznes holatlar uchun `status` maydonlari qo‘llangan.

Model tafsilotlari: `backend/prisma/schema.prisma`.
