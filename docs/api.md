# API hujjati

Asosiy prefiks: `/api`

## Auth
- `POST /api/auth/login`

## TTJ tuzilmasi
- `GET /api/buildings`
- `GET /api/blocks?buildingId=...`
- `GET /api/floors?blockId=...`
- `GET /api/rooms?floorId=...`
- `GET /api/rooms/:id`

## Talabalar
- `GET /api/students?q=...`
- `POST /api/students`
- `PUT /api/students/:id`
- `POST /api/students/:id/move`
- `POST /api/students/:id/discharge`
- `GET /api/students/:id/history`

## To‘lovlar
- `GET /api/payments`
- `POST /api/payments`

## Import
- `GET /api/import/template`
- `POST /api/import/docx?preview=true`
- `POST /api/import/xlsx?preview=true`
- `GET /api/imports`

## Audit va dashboard
- `GET /api/audit-logs`
- `GET /api/dashboard/stats`
