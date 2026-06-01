export type UserRole = 'OPERATOR' | 'SUPERVISOR' | 'ADMIN';

export interface AppUser {
  id: number;
  created_at: string;
  username: string;
  role: UserRole | string;
  active: boolean;
}

export interface CreateUserRequest {
  username: string;
  password: string;
  role: UserRole;
  active: boolean;
}

