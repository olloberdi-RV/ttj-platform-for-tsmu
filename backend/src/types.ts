export type AppRole = 'SUPER_ADMIN' | 'OFFICER' | 'OBSERVER';

export interface AuthUser {
  id: string;
  username: string;
  role: AppRole;
}

declare global {
  namespace Express {
    interface Request {
      user?: AuthUser;
    }
  }
}
