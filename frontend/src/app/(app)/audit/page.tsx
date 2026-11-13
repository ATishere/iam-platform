"use client";

import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import type { AuditFilters as AuditParams } from "@/lib/api/audit";
import { isUuid } from "@/lib/utils";
import {
  AuditFilters,
  type AuditFilterValues,
} from "@/features/audit/audit-filters";
import { AuditTable } from "@/features/audit/audit-table";

const EMPTY_FILTERS: AuditFilterValues = {
  action: "",
  actor_id: "",
  outcome: "",
  from_date: "",
  to_date: "",
};

export default function AuditPage() {
  const [filters, setFilters] = useState<AuditFilterValues>(EMPTY_FILTERS);
  const [debounced, setDebounced] =
    useState<AuditFilterValues>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebounced(filters);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [filters]);

  const actorId = debounced.actor_id.trim();
  const actorValid = actorId === "" || isUuid(actorId);

  const params: AuditParams = {
    action: debounced.action.trim() || undefined,
    actor_id: actorValid && actorId ? actorId : undefined,
    outcome: debounced.outcome || undefined,
    from_date: debounced.from_date || undefined,
    to_date: debounced.to_date || undefined,
    page,
    page_size: 20,
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Audit log</h1>
        <p className="text-sm text-muted-foreground">
          Query activity across your organization. Date ranges are limited to
          90 days.
        </p>
      </div>

      <AuditFilters
        filters={filters}
        onChange={(patch) => setFilters((prev) => ({ ...prev, ...patch }))}
        onReset={() => setFilters(EMPTY_FILTERS)}
      />

      {!actorValid ? (
        <Alert>
          <AlertDescription>
            Actor ID must be a valid UUID. The actor filter is ignored until
            it is corrected.
          </AlertDescription>
        </Alert>
      ) : null}

      <AuditTable mode="audit" params={params} onPageChange={setPage} />
    </div>
  );
}
