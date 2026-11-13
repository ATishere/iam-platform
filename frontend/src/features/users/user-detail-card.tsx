"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { adminApi, type UserAdmin } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";

interface UserDetailCardProps {
  user: UserAdmin;
}

export function UserDetailCard({ user }: UserDetailCardProps) {
  const queryClient = useQueryClient();
  const [fullName, setFullName] = useState(user.full_name ?? "");
  const [isActive, setIsActive] = useState(user.is_active);

  const mutation = useMutation({
    mutationFn: () =>
      adminApi.users.update(user.id, { full_name: fullName, is_active: isActive }),
    onSuccess: () => {
      toast.success("User updated");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "user", user.id] });
    },
    onError: (error) =>
      toast.error(error instanceof ApiError ? error.detail : "Update failed"),
  });

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Details</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="space-y-1">
            <Label htmlFor="detail-email">Email</Label>
            <Input id="detail-email" value={user.email} disabled />
          </div>
          <div className="space-y-1">
            <Label htmlFor="detail-name">Full name</Label>
            <Input
              id="detail-name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 accent-primary"
            />
            Account is active
          </label>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Saving..." : "Save changes"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
