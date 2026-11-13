"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { adminApi, type Role } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";

interface EditRoleDialogProps {
  role: Role | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditRoleDialog({ role, open, onOpenChange }: EditRoleDialogProps) {
  const queryClient = useQueryClient();
  const [description, setDescription] = useState("");

  useEffect(() => {
    setDescription(role?.description ?? "");
  }, [role]);

  const mutation = useMutation({
    mutationFn: () => {
      if (!role) throw new Error("No role selected");
      return adminApi.roles.update(role.id, {
        description: description || undefined,
      });
    },
    onSuccess: () => {
      toast.success("Role updated");
      queryClient.invalidateQueries({ queryKey: ["admin", "roles"] });
      onOpenChange(false);
    },
    onError: (error) =>
      toast.error(error instanceof ApiError ? error.detail : "Update failed"),
  });

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={`Edit ${role?.name ?? "role"}`}
      description="Only the description can be edited."
    >
      <div className="space-y-3">
        {mutation.error instanceof ApiError ? (
          <p className="text-sm text-destructive">{mutation.error.detail}</p>
        ) : null}
        <div className="space-y-1">
          <Label htmlFor="edit-role-description">Description</Label>
          <Input
            id="edit-role-description"
            maxLength={255}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            {mutation.isPending ? "Saving..." : "Save changes"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
