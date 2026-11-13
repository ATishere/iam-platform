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

import { RoleSelect } from "./role-select";

interface CreateUserDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateUserDialog({ open, onOpenChange }: CreateUserDialogProps) {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [roleIds, setRoleIds] = useState<string[]>([]);

  const rolesQuery = useQuery({
    queryKey: ["admin", "roles"],
    queryFn: adminApi.roles.list,
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: () =>
      adminApi.users.create({
        email,
        password,
        full_name: fullName || undefined,
        role_ids: roleIds,
      }),
    onSuccess: () => {
      toast.success("User created");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "stats"] });
      setEmail("");
      setFullName("");
      setPassword("");
      setRoleIds([]);
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
      title="Create user"
      description="Add a new member to your organization."
    >
      <form onSubmit={onSubmit} className="space-y-3">
        {mutation.error instanceof ApiError ? (
          <p className="text-sm text-destructive">{mutation.error.detail}</p>
        ) : null}
        <div className="space-y-1">
          <Label htmlFor="new-email">Email</Label>
          <Input
            id="new-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="new-name">Full name</Label>
          <Input
            id="new-name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="new-password">Temporary password</Label>
          <Input
            id="new-password"
            type="password"
            required
            minLength={12}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">At least 12 characters.</p>
        </div>
        <div className="space-y-1">
          <Label>Roles</Label>
          {rolesQuery.isPending ? (
            <p className="text-sm text-muted-foreground">Loading roles…</p>
          ) : (
            <RoleSelect
              roles={rolesQuery.data?.items ?? []}
              selected={roleIds}
              onChange={setRoleIds}
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
            {mutation.isPending ? "Creating..." : "Create user"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
