export interface DashboardStats {
  buildings: number;
  blocks: number;
  rooms: number;
  beds: number;
  occupied: number;
  empty: number;
  occupancyPercent: number;
  students: number;
  debtors: number;
  totalPayment: number;
  paidPayment: number;
  debt: number;
}

export interface RoomItem {
  id: string;
  roomNumber: string;
  capacity: number;
  occupiedBeds: number;
  emptyBeds: number;
  occupancyPercent: number;
  floor: { floorNumber: number };
  block: { name: string; number: string };
  beds: Array<{ id: string; bedNumber: number; status: 'EMPTY' | 'OCCUPIED' | 'RESERVED' | 'DISABLED' }>;
}

export interface StudentCard {
  id: string;
  fullName: string;
  pinfl: string;
  faculty: string;
  course: number;
  phone: string;
  room?: string;
  bed?: number;
  payment: {
    total: number;
    paid: number;
    remaining: number;
    status: string;
  };
}
