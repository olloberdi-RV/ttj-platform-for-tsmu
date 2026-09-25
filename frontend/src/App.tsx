import { useEffect, useMemo, useState } from 'react';
import { DashboardPage } from './pages/DashboardPage';
import { RoomCard } from './components/RoomCard';
import { StudentCard } from './components/StudentCard';
import { LoginForm } from './components/LoginForm';
import { apiGet } from './services/api';
import type { DashboardStats, RoomItem, StudentCard as StudentCardType } from './types';

type Menu = 'dashboard' | 'rooms' | 'students';

function App() {
  const [menu, setMenu] = useState<Menu>('dashboard');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [rooms, setRooms] = useState<RoomItem[]>([]);
  const [students, setStudents] = useState<StudentCardType[]>([]);
  const [search, setSearch] = useState('');
  const [authReady, setAuthReady] = useState(Boolean(localStorage.getItem('ttj_access_token')));

  useEffect(() => {
    if (!authReady) return;
    apiGet<DashboardStats>('/dashboard/stats').then(setStats).catch(() => setStats(null));
    apiGet<RoomItem[]>('/rooms').then(setRooms).catch(() => setRooms([]));
    apiGet<StudentCardType[]>('/students').then(setStudents).catch(() => setStudents([]));
  }, [authReady]);

  const filteredStudents = useMemo(
    () => students.filter((s) => `${s.fullName} ${s.faculty} ${s.course} ${s.room ?? ''}`.toLowerCase().includes(search.toLowerCase())),
    [students, search],
  );

  if (!authReady) {
    return (
      <main className="min-h-screen bg-slate-50 p-4">
        <LoginForm onSuccess={() => setAuthReady(true)} />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <div className="mx-auto grid max-w-7xl gap-4 p-4 lg:grid-cols-[260px_1fr]">
        <aside className="rounded-xl border bg-white p-4">
          <h2 className="mb-4 text-lg font-bold">TTJ navigatsiya</h2>
          <nav className="space-y-2 text-sm">
            <MenuButton label="🏠 Dashboard" active={menu === 'dashboard'} onClick={() => setMenu('dashboard')} />
            <MenuButton label="🚪 Xonalar" active={menu === 'rooms'} onClick={() => setMenu('rooms')} />
            <MenuButton label="🎓 Talabalar" active={menu === 'students'} onClick={() => setMenu('students')} />
          </nav>
        </aside>

        <section className="space-y-4">
          <header className="rounded-xl border bg-white p-4">
            <h1 className="text-2xl font-bold">Talabalar Turar Joyi boshqaruv tizimi</h1>
            <p className="text-sm text-slate-600">Bino → Blok → Qavat → Xona → O‘rin → Talaba</p>
          </header>

          {menu === 'dashboard' && <DashboardPage stats={stats} />}

          {menu === 'rooms' && (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {rooms.map((room) => <RoomCard key={room.id} room={room} />)}
            </div>
          )}

          {menu === 'students' && (
            <>
              <div className="rounded-xl border bg-white p-4">
                <input
                  className="w-full rounded border px-3 py-2"
                  placeholder="F.I.O., JShShIR, fakultet, kurs, xona bo‘yicha qidiring"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {filteredStudents.map((student) => <StudentCard key={student.id} student={student} />)}
              </div>
            </>
          )}
        </section>
      </div>
    </main>
  );
}

function MenuButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} className={`w-full rounded px-3 py-2 text-left ${active ? 'bg-slate-900 text-white' : 'bg-slate-100'}`}>
      {label}
    </button>
  );
}

export default App;
