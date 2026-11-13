"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Can } from "@/components/can";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { adminApi, type UserAdmin } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

interface UserActionsCardProps {
  user: UserAdmin;
}

export function UserActionsCard({ user }: UserActionsCardProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const currentUserId = useAuthStore((state) => state.user?.id);
  const [revokeOpen, setRevokeOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const revokeMutation = useMutation({
    mutationFn: () => adminApi.users.revokeSessions(user.id),
    onSuccess: () => {
      toast.success("Sessions revoked");
      setRevokeOpen(false);
    },
    onError: (error) =>
      toast.error(
        error instanceof ApiError ? error.detail : "Revoke failed",
      ),
  });

  const deleteMutation = useMutation({
    mutationFn: () => adminApi.users.remove(user.id),
    onSuccess: () => {
      toast.success("User deleted");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "stats"] });
      setDeleteOpen(false);
      router.push("/users");
    },
    onError: (error) =>
      toast.error(error instanceof ApiError ? error.detail : "Delete failed"),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Can allOf={["users:update", "sessions:revoke"]}>
          <Button
            variant="outline"
            onClick={() => setRevokeOpen(true)}
            disabled={revokeMutation.isPending}
          >
            Revoke all sessions
          </Button>
        </Can>
        <Can permission="users:delete">
          {user.id !== currentUserId ? (
            <Button
              variant="destructive"
              onClick={() => setDeleteOpen(true)}
              disabled={deleteMutation.isPending}
            >
              Delete user
            </Button>
          ) : null}
        </Can>
      </CardContent>

      <ConfirmDialog
        open={revokeOpen}
        onOpenChange={setRevokeOpen}
        title="Revoke sessions"
        description="All active sessions for this user will be signed out."
        confirmLabel="Revoke"
        onConfirm={() => revokeMutation.mutate()}
        isPending={revokeMutation.isPending}
      />

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete user"
        description="This permanently deletes the user and revokes their sessions."
        confirmLabel="Delete"
        onConfirm={() => deleteMutation.mutate()}
        isPending={deleteMutation.isPending}
      />
    </Card>
  );
}
