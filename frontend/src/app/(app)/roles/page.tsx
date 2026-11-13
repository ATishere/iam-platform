"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Can } from "@/components/can";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { adminApi, type Role } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";
import { usePermissions } from "@/hooks/use-permissions";
import { CreateRoleDialog } from "@/features/roles/create-role-dialog";
import { EditRoleDialog } from "@/features/roles/edit-role-dialog";
import { RolesTable } from "@/features/roles/roles-table";

export default function RolesPage() {
  const { has } = usePermissions();
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<Role | null>(null);

  const query = useQuery({
    queryKey: ["admin", "roles"],
    queryFn: adminApi.roles.list,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Roles</h1>
          <p className="text-sm text-muted-foreground">
            Roles bundle permissions and can be assigned to users.
          </p>
        </div>
        <Can permission="roles:manage">
          <Button onClick={() => setCreateOpen(true)}>Create role</Button>
        </Can>
      </div>

      {query.error ? (
        <Alert variant="destructive">
          <AlertDescription>
            {query.error instanceof ApiError
              ? query.error.detail
              : "Could not load roles."}
          </AlertDescription>
        </Alert>
      ) : (
        <RolesTable
          roles={query.data?.items}
          isLoading={query.isPending}
          canManage={has("roles:manage")}
          onEdit={setEditing}
        />
      )}

      <CreateRoleDialog open={createOpen} onOpenChange={setCreateOpen} />
      <EditRoleDialog
        role={editing}
        open={editing !== null}
        onOpenChange={(open) => {
          if (!open) setEditing(null);
        }}
      />
    </div>
  );
}
