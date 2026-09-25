import type { StudentCard as StudentCardType } from '../types';

export function StudentCard({ student }: { student: StudentCardType }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4">
      <h3 className="font-semibold">{student.fullName}</h3>
      <p className="text-sm text-slate-600">{student.faculty} • {student.course}-kurs</p>
      <p className="text-sm">Xona: {student.room ?? '-'} | O‘rin: {student.bed ?? '-'}</p>
      <p className="text-sm">To‘lov holati: {student.payment.status}</p>
      <p className="text-sm">To‘langan: {student.payment.paid.toLocaleString('uz-UZ')} so‘m</p>
      <p className="text-sm">Qolgan: {student.payment.remaining.toLocaleString('uz-UZ')} so‘m</p>
      <button className="mt-3 rounded border px-3 py-1 text-sm">Batafsil</button>
    </article>
  );
}
