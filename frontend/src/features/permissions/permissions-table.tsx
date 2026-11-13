"use client";

import { useQuery } from "@tanstack/react-query";

import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { adminApi } from "@/lib/api/admin";

export function PermissionsTable() {
  const query = useQuery({
    queryKey: ["admin", "permissions"],
    queryFn: adminApi.permissions.list,
    staleTime: 300_000,
  });

  if (query.isPending) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (query.error) {
    return (
      <div className="rounded-lg border p-6 text-sm text-destructive">
        {query.error instanceof Error
          ? query.error.message
          : "Could not load permissions."}
      </div>
    );
  }

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Code</TableHead>
            <TableHead>Description</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(query.data?.items ?? []).map((permission) => (
            <TableRow key={permission.id}>
              <TableCell className="font-mono text-xs">
                {permission.code}
              </TableCell>
              <TableCell>{permission.description ?? "—"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
