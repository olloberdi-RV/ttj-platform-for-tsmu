# TTJ Platform for TSMU

Talabalar turar joyi boshqaruv tizimi (React + TypeScript + Tailwind + Node.js + Express + PostgreSQL + Prisma).

## 1) Loyihani o‘rnatish
```bash
npm --prefix backend install
npm --prefix frontend install
```

## 2) Database yaratish
PostgreSQL’da `ttj_platform` bazasini yarating va `backend/.env` fayliga `DATABASE_URL` yozing.

## 3) Environment variables
- `backend/.env.example` dan `backend/.env` yarating
- `frontend/.env.example` dan `frontend/.env` yarating

## 4) Backend ishga tushirish
```bash
cd backend
npx prisma migrate dev --name init
npx prisma generate
npm run seed
npm run dev
```

## 5) Frontend ishga tushirish
```bash
cd frontend
npm run dev
```

## 6) Demo login
- Login: `admin`
- Parol: `Admin123!@#`

## 7) Production deployment
- Backend: `npm --prefix backend run build && npm --prefix backend run start`
- Frontend: `npm --prefix frontend run build`
- Nginx bilan frontend static fayllar, backend reverse-proxy orqali.

## 8) Database backup
PostgreSQL backup:
```bash
pg_dump -Fc --dbname="$DATABASE_URL" > backup.dump
pg_restore --clean --if-exists --dbname="$DATABASE_URL" backup.dump
```

## 9) DOCX import formati
DOCX ichida satrlar `|` bilan ajratilgan bo‘lishi kerak:

`fullName | pinfl | faculty | course | roomNumber | sport | privilege | totalPayment | paidAmount`

## 10) XLSX/CSV import formati
Ustunlar:
- `fullName`
- `pinfl`
- `faculty`
- `course`
- `roomNumber`
- `sport`
- `privilege`
- `totalPayment`
- `paidAmount`

## Arxitektura
- `frontend/`: komponentlar, sahifalar, API xizmatlari
- `backend/`: route, middleware, auth, validator, service
- `database/`: DB bilan bog‘liq materiallar uchun
- `docs/`: API va schema hujjatlari

## Xavfsizlik
- JWT auth + RBAC
- bcrypt hash
- rate limiting
- helmet
- input validation (zod)
- import fayllar uchun MIME/size tekshiruvlari
- audit loglar
