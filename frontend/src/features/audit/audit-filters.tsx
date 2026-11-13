"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";

export interface AuditFilterValues {
  action: string;
  actor_id: string;
  outcome: string;
  from_date: string;
  to_date: string;
}

interface AuditFiltersProps {
  filters: AuditFilterValues;
  onChange: (patch: Partial<AuditFilterValues>) => void;
  onReset: () => void;
  showActor?: boolean;
  showOutcome?: boolean;
}

function toDateInput(value: string): string {
  return value ? value.slice(0, 10) : "";
}

export function AuditFilters({
  filters,
  onChange,
  onReset,
  showActor = true,
  showOutcome = true,
}: AuditFiltersProps) {
  const columns = 3 + (showActor ? 1 : 0) + (showOutcome ? 1 : 0);

  return (
    <div
      className={cn(
        "grid gap-3",
        columns === 5
          ? "md:grid-cols-5"
          : columns === 4
            ? "md:grid-cols-4"
            : "md:grid-cols-3",
      )}
    >
      <div className="space-y-1">
        <Label htmlFor="filter-action">Action</Label>
        <Input
          id="filter-action"
          placeholder="login.success"
          value={filters.action}
          onChange={(e) => onChange({ action: e.target.value })}
        />
      </div>
      {showActor ? (
        <div className="space-y-1">
          <Label htmlFor="filter-actor">Actor ID</Label>
          <Input
            id="filter-actor"
            placeholder="UUID"
            value={filters.actor_id}
            onChange={(e) => onChange({ actor_id: e.target.value })}
          />
        </div>
      ) : null}
      {showOutcome ? (
        <div className="space-y-1">
          <Label htmlFor="filter-outcome">Outcome</Label>
          <Select
            id="filter-outcome"
            value={filters.outcome}
            onChange={(e) => onChange({ outcome: e.target.value })}
          >
            <option value="">Any</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
          </Select>
        </div>
      ) : null}
      <div className="space-y-1">
        <Label htmlFor="filter-from">From</Label>
        <Input
          id="filter-from"
          type="date"
          value={toDateInput(filters.from_date)}
          onChange={(e) =>
            onChange({
              from_date: e.target.value
                ? new Date(`${e.target.value}T00:00:00Z`).toISOString()
                : "",
            })
          }
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="filter-to">To</Label>
        <Input
          id="filter-to"
          type="date"
          value={toDateInput(filters.to_date)}
          onChange={(e) =>
            onChange({
              to_date: e.target.value
                ? new Date(`${e.target.value}T23:59:59Z`).toISOString()
                : "",
            })
          }
        />
      </div>
      <div className="flex items-end">
        <Button variant="outline" onClick={onReset}>
          Reset
        </Button>
      </div>
    </div>
  );
}
