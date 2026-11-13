"use client";

import { useQuery } from "@tanstack/react-query";

import { Pagination } from "@/components/pagination";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { auditApi, type AuditFilters } from "@/lib/api/audit";
import { ApiError } from "@/lib/api/client";

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

interface AuditTableProps {
  mode: "audit" | "security";
  params: AuditFilters;
  onPageChange: (page: number) => void;
}

export function AuditTable({ mode, params, onPageChange }: AuditTableProps) {
  const query = useQuery({
    queryKey: ["audit", mode, params],
    queryFn: () =>
      mode === "audit"
        ? auditApi.list(params)
        : auditApi.securityEvents(params),
  });

  if (query.isPending) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (query.error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          {query.error instanceof ApiError
            ? query.error.detail
            : "Could not load events."}
        </AlertDescription>
      </Alert>
    );
  }

  const data = query.data;

  return (
    <div className="space-y-3">
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Resource</TableHead>
              <TableHead>Outcome</TableHead>
              <TableHead>IP</TableHead>
              <TableHead>Metadata</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(data?.items ?? []).map((entry) => (
              <TableRow key={entry.id}>
                <TableCell className="whitespace-nowrap">
                  {dateFormatter.format(new Date(entry.created_at))}
                </TableCell>
                <TableCell>
                  {entry.actor_id ? (
                    <span
                      className="font-mono text-xs"
                      title={entry.actor_id}
                    >
                      {entry.actor_id.slice(0, 8)}…
                    </span>
                  ) : (
                    <span className="text-muted-foreground">system</span>
                  )}
                </TableCell>
                <TableCell className="font-mono text-xs">
                  {entry.action}
                </TableCell>
                <TableCell>
                  {entry.resource_type ? (
                    <span className="text-xs">
                      {entry.resource_type}
                      {entry.resource_id ? `:${entry.resource_id}` : ""}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell>
                  <Badge
                    variant={
                      entry.outcome === "success" ? "success" : "destructive"
                    }
                  >
                    {entry.outcome}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs">
                  {entry.ip_address ?? "—"}
                </TableCell>
                <TableCell>
                  {Object.keys(entry.metadata).length === 0 ? (
                    <span className="text-muted-foreground">—</span>
                  ) : (
                    <details>
                      <summary className="cursor-pointer text-xs text-primary">
                        view
                      </summary>
                      <pre className="mt-1 max-w-xs overflow-auto rounded bg-muted p-2 text-xs">
                        {JSON.stringify(entry.metadata, null, 2)}
                      </pre>
                    </details>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {data && data.total === 0 ? (
        <p className="text-center text-sm text-muted-foreground">
          No events match these filters.
        </p>
      ) : null}

      <Pagination
        page={params.page}
        pageSize={params.page_size ?? 20}
        total={data?.total ?? 0}
        onChange={onPageChange}
      />
    </div>
  );
}
