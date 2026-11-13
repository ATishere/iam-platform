"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { useSignOut } from "@/features/auth/use-sign-out";

export function ChangePasswordCard() {
  const { signOutLocal } = useSignOut();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      authApi.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      }),
    onSuccess: () => {
      toast.success("Password changed. Please sign in again.");
      signOutLocal();
    },
  });

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (newPassword !== confirm) {
      toast.error("Passwords do not match");
      return;
    }
    mutation.mutate();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Change password</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-3">
          {mutation.error instanceof ApiError ? (
            <Alert variant="destructive">
              <AlertDescription>{mutation.error.detail}</AlertDescription>
            </Alert>
          ) : null}
          <div className="space-y-1">
            <Label htmlFor="old-password">Current password</Label>
            <Input
              id="old-password"
              type="password"
              required
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="new-password">New password</Label>
            <Input
              id="new-password"
              type="password"
              required
              minLength={12}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              At least 12 characters.
            </p>
          </div>
          <div className="space-y-1">
            <Label htmlFor="confirm-password">Confirm new password</Label>
            <Input
              id="confirm-password"
              type="password"
              required
              minLength={12}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            Changing your password signs you out of all sessions.
          </p>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Changing..." : "Change password"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
