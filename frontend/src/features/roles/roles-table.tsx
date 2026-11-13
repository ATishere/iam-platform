"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { adminApi, type Role } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";

interface RolesTableProps {
  roles: Role[] | undefined;
  isLoading: boolean;
  canManage: boolean;
  onEdit: (role: Role) => void;
}

export function RolesTable({
  roles,
  isLoading,
  canManage,
  onEdit,
}: RolesTableProps) {
  const queryClient = useQueryClient();
  const [deleting, setDeleting] = useState<Role | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (role: Role) => adminApi.roles.remove(role.id),
    onSuccess: () => {
      toast.success("Role deleted");
      queryClient.invalidateQueries({ queryKey: ["admin", "roles"] });
      setDeleting(null);
    },
    onError: (error) =>
      toast.error(error instanceof ApiError ? error.detail : "Delete failed"),
  });

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!roles || roles.length === 0) {
    return (
      <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">
        No roles found.
      </div>
    );
  }

  return (
    <>
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Permissions</TableHead>
              <TableHead>Type</TableHead>
              {canManage ? <TableHead>Actions</TableHead> : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {roles.map((role) => (
              <TableRow key={role.id}>
                <TableCell className="font-medium">{role.name}</TableCell>
                <TableCell>{role.description ?? "—"}</TableCell>
                <TableCell>
                  <span className="text-muted-foreground">
                    {role.permission_codes.length}
                  </span>
                </TableCell>
                <TableCell>
                  {role.is_system ? (
                    <span className="text-xs text-muted-foreground">System</span>
                  ) : (
                    <span className="text-xs text-muted-foreground">Custom</span>
                  )}
                </TableCell>
                {canManage ? (
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onEdit(role)}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        disabled={role.is_system}
                        title={
                          role.is_system
                            ? "System roles cannot be deleted"
                            : undefined
                        }
                        onClick={() => setDeleting(role)}
                      >
                        Delete
                      </Button>
                    </div>
                  </TableCell>
                ) : null}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => {
          if (!open) setDeleting(null);
        }}
        title="Delete role"
        description={`Delete the role "${deleting?.name ?? ""}"? Users assigned to it will lose these permissions.`}
        confirmLabel="Delete"
        onConfirm={() => {
          if (deleting) deleteMutation.mutate(deleting);
        }}
        isPending={deleteMutation.isPending}
      />
    </>
  );
}
