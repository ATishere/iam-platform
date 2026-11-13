"use client";

import { useEffect, useState } from "react";

import type { AuditFilters as AuditParams } from "@/lib/api/audit";
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

export default function SecurityPage() {
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

  const params: AuditParams = {
    action: debounced.action.trim() || undefined,
    from_date: debounced.from_date || undefined,
    to_date: debounced.to_date || undefined,
    page,
    page_size: 20,
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Security events
        </h1>
        <p className="text-sm text-muted-foreground">
          Authentication and account security activity. Date ranges are
          limited to 90 days.
        </p>
      </div>

      <AuditFilters
        filters={filters}
        onChange={(patch) => setFilters((prev) => ({ ...prev, ...patch }))}
        onReset={() => setFilters(EMPTY_FILTERS)}
        showActor={false}
        showOutcome={false}
      />

      <AuditTable mode="security" params={params} onPageChange={setPage} />
    </div>
  );
}
