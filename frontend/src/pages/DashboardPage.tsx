import { Pie, PieChart, ResponsiveContainer, Tooltip, Cell } from 'recharts';
import type { DashboardStats } from '../types';

const COLORS = ['#ef4444', '#22c55e'];

export function DashboardPage({ stats }: { stats: DashboardStats | null }) {
  if (!stats) return <div className="rounded border bg-white p-4">Yuklanmoqda...</div>;

  const chartData = [
    { name: 'Band', value: stats.occupied },
    { name: 'Bo‘sh', value: stats.empty },
  ];

  return (
    <section className="space-y-4">
      <div className="grid gap-3 md:grid-cols-4">
        <Stat title="Jami talabalar" value={stats.students} />
        <Stat title="Jami o‘rin" value={stats.beds} />
        <Stat title="Band" value={stats.occupied} />
        <Stat title="Bo‘sh" value={stats.empty} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border bg-white p-4">
          <h3 className="mb-2 font-semibold">TTJ bandlik darajasi</h3>
          <div className="h-56">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={chartData} dataKey="value" cx="50%" cy="50%" outerRadius={80} label>
                  {chartData.map((entry) => <Cell key={entry.name} fill={COLORS[chartData.indexOf(entry)]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-xl border bg-white p-4 text-sm">
          <h3 className="mb-2 font-semibold">Qarzdorlik</h3>
          <p>Umumiy: {stats.totalPayment.toLocaleString('uz-UZ')} so‘m</p>
          <p>To‘langan: {stats.paidPayment.toLocaleString('uz-UZ')} so‘m</p>
          <p>Qarzdorlik: {stats.debt.toLocaleString('uz-UZ')} so‘m</p>
          <p>Qarzdor talabalar: {stats.debtors}</p>
        </div>
      </div>
    </section>
  );
}

function Stat({ title, value }: { title: string; value: number }) {
  return (
    <div className="rounded-xl border bg-white p-4">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="text-2xl font-semibold">{value.toLocaleString('uz-UZ')}</p>
    </div>
  );
}
