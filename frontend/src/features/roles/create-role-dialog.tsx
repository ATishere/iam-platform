"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { adminApi } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";

import { PermissionsChecklist } from "./permissions-checklist";

interface CreateRoleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateRoleDialog({ open, onOpenChange }: CreateRoleDialogProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [codes, setCodes] = useState<string[]>([]);

  const permissionsQuery = useQuery({
    queryKey: ["admin", "permissions"],
    queryFn: adminApi.permissions.list,
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: () =>
      adminApi.roles.create({
        name,
        description: description || undefined,
        permission_codes: codes,
      }),
    onSuccess: () => {
      toast.success("Role created");
      queryClient.invalidateQueries({ queryKey: ["admin", "roles"] });
      setName("");
      setDescription("");
      setCodes([]);
      onOpenChange(false);
    },
    onError: (error) =>
      toast.error(error instanceof ApiError ? error.detail : "Create failed"),
  });

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Create role"
      description="Role names are uppercase identifiers, e.g. SUPPORT_AGENT."
    >
      <form onSubmit={onSubmit} className="space-y-3">
        {mutation.error instanceof ApiError ? (
          <p className="text-sm text-destructive">{mutation.error.detail}</p>
        ) : null}
        <div className="space-y-1">
          <Label htmlFor="role-name">Name</Label>
          <Input
            id="role-name"
            required
            minLength={2}
            maxLength={64}
            placeholder="SUPPORT_AGENT"
            value={name}
            onChange={(e) => setName(e.target.value.toUpperCase())}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="role-description">Description</Label>
          <Input
            id="role-description"
            maxLength={255}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label>Permissions</Label>
          {permissionsQuery.isPending ? (
            <p className="text-sm text-muted-foreground">
              Loading permissions…
            </p>
          ) : (
            <PermissionsChecklist
              permissions={permissionsQuery.data?.items ?? []}
              selected={codes}
              onChange={setCodes}
            />
          )}
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Creating..." : "Create role"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
