import { apiFetch } from "./client";

export interface AuditLogEntry {
  id: string;
  organization_id: string;
  actor_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  outcome: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface AuditListResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuditFilters {
  action?: string;
  actor_id?: string;
  outcome?: string;
  from_date?: string;
  to_date?: string;
  page: number;
  page_size?: number;
}

function auditQuery(params: AuditFilters): string {
  const qs = new URLSearchParams();
  if (params.action) qs.set("action", params.action);
  if (params.actor_id) qs.set("actor_id", params.actor_id);
  if (params.outcome) qs.set("outcome", params.outcome);
  if (params.from_date) qs.set("from_date", params.from_date);
  if (params.to_date) qs.set("to_date", params.to_date);
  qs.set("page", String(params.page));
  qs.set("page_size", String(params.page_size ?? 20));
  return qs.toString();
}

export const auditApi = {
  list: (params: AuditFilters) =>
    apiFetch<AuditListResponse>(`/admin/audit-logs?${auditQuery(params)}`),
  securityEvents: (params: AuditFilters) =>
    apiFetch<AuditListResponse>(
      `/admin/security-events?${auditQuery(params)}`,
    ),
};
