import { apiFetch } from "./client";

export interface UserAdmin {
  id: string;
  organization_id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_locked: boolean;
  failed_login_attempts: number;
  locked_until: string | null;
  last_login_at: string | null;
  created_at: string;
  roles: string[];
}

export interface PageMeta {
  total: number;
  page: number;
  page_size: number;
}

export interface UserAdminListResponse extends PageMeta {
  items: UserAdmin[];
}

export interface Role {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  is_system: boolean;
  created_at: string;
  permission_codes: string[];
}

export interface RoleListResponse {
  items: Role[];
  total: number;
}

export interface Permission {
  id: string;
  code: string;
  description: string | null;
}

export interface PermissionListResponse {
  items: Permission[];
  total: number;
}

export interface RecentSecurityEvent {
  id: string;
  action: string;
  actor_id: string | null;
  outcome: string;
  created_at: string;
}

export interface DashboardStats {
  users_total: number;
  users_active: number;
  users_locked: number;
  recent_logins_24h: number;
  failed_logins_24h: number;
  recent_security_events: RecentSecurityEvent[];
}

export interface ListUsersParams {
  q?: string;
  is_active?: boolean;
  page: number;
  page_size?: number;
}

export interface CreateUserPayload {
  email: string;
  password: string;
  full_name?: string | null;
  role_ids: string[];
  is_active?: boolean;
}

function userQuery(params: ListUsersParams): string {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.is_active !== undefined) {
    qs.set("is_active", String(params.is_active));
  }
  qs.set("page", String(params.page));
  qs.set("page_size", String(params.page_size ?? 20));
  return qs.toString();
}

export const adminApi = {
  users: {
    list: (params: ListUsersParams) =>
      apiFetch<UserAdminListResponse>(`/admin/users?${userQuery(params)}`),
    get: (id: string) => apiFetch<UserAdmin>(`/admin/users/${id}`),
    create: (body: CreateUserPayload) =>
      apiFetch<UserAdmin>("/admin/users", { method: "POST", body }),
    update: (id: string, body: { full_name?: string; is_active?: boolean }) =>
      apiFetch<UserAdmin>(`/admin/users/${id}`, {
        method: "PATCH",
        body,
      }),
    setRoles: (id: string, roleIds: string[]) =>
      apiFetch<UserAdmin>(`/admin/users/${id}/roles`, {
        method: "PUT",
        body: { role_ids: roleIds },
      }),
    revokeSessions: (id: string) =>
      apiFetch<void>(`/admin/users/${id}/sessions`, { method: "DELETE" }),
    remove: (id: string) =>
      apiFetch<void>(`/admin/users/${id}`, { method: "DELETE" }),
  },
  roles: {
    list: () => apiFetch<RoleListResponse>("/admin/roles"),
    create: (body: {
      name: string;
      description?: string;
      permission_codes: string[];
    }) => apiFetch<Role>("/admin/roles", { method: "POST", body }),
    update: (id: string, body: { description?: string }) =>
      apiFetch<Role>(`/admin/roles/${id}`, { method: "PATCH", body }),
    remove: (id: string) =>
      apiFetch<void>(`/admin/roles/${id}`, { method: "DELETE" }),
  },
  permissions: {
    list: () =>
      apiFetch<PermissionListResponse>("/admin/permissions"),
  },
  dashboard: {
    stats: () =>
      apiFetch<DashboardStats>("/admin/dashboard/stats"),
  },
};
