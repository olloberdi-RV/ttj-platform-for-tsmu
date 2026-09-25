import type { RoomItem } from '../types';

const statusLabel = {
  EMPTY: 'Bo‘sh',
  OCCUPIED: 'Band',
  RESERVED: 'Rezerv',
  DISABLED: 'Foydalanilmaydi',
};

const statusColor = {
  EMPTY: '🟢',
  OCCUPIED: '🔴',
  RESERVED: '🟡',
  DISABLED: '⚪',
};

export function RoomCard({ room }: { room: RoomItem }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-lg font-semibold">XONA {room.roomNumber}</h3>
      <p className="text-sm text-slate-600">{room.floor.floorNumber}-qavat • {room.block.number} blok</p>
      <div className="my-3 flex flex-wrap gap-2 text-sm">
        {room.beds.map((bed) => (
          <span key={bed.id} className="rounded bg-slate-100 px-2 py-1">{bed.bedNumber} {statusColor[bed.status]} {statusLabel[bed.status]}</span>
        ))}
      </div>
      <div className="text-sm text-slate-700">
        <p>{room.occupiedBeds}/{room.capacity} o‘rin band</p>
        <p>{room.emptyBeds} ta bo‘sh joy</p>
      </div>
      <button className="mt-3 rounded bg-slate-900 px-3 py-2 text-sm text-white">Xonani ko‘rish</button>
    </article>
  );
}
