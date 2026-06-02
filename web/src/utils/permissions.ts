export type UserRole =
  | 'ADMIN'
  | 'SUPERVISOR'
  | 'OPERATOR';

export type Tab =
  | 'production'
  | 'training'
  | 'history'
  | 'system'
  | 'admin'
  | 'settings';

const permissions: Record<UserRole, Tab[]> = {
  ADMIN: [
    'production',
    'training',
    'history',
    'system',
    'admin',
    'settings',
  ],

  SUPERVISOR: [
    'production',
    'training',
    'history',
    'system',
    'settings',
  ],

  OPERATOR: [
    'production',
    'training',
    'history',
  ],
};

export function canAccess(
  role: string,
  tab: Tab
): boolean {
  return (
    permissions[role as UserRole]?.includes(tab) ?? false
  );
}