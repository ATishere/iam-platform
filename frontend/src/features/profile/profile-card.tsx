"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, ShieldOff } from "lucide-react";
import { toast } from "sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { authApi } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import type { User } from "@/lib/api/types";
import { usersApi } from "@/lib/api/users";
import { formatDateTime } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";

import { useSignOut } from "@/features/auth/use-sign-out";

export function ProfileCard() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((state) => state.setUser);
  const { signOutLocal } = useSignOut();
  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState("");

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: usersApi.me,
  });

  useEffect(() => {
    if (meQuery.data) {
      setUser(meQuery.data);
      setFullName(meQuery.data.full_name ?? "");
    }
  }, [meQuery.data, setUser]);

  const updateMutation = useMutation({
    mutationFn: () =>
      usersApi.updateMe({ full_name: fullName.trim() ? fullName.trim() : null }),
    onSuccess: (updated: User) => {
      queryClient.setQueryData(["me"], updated);
      setUser(updated);
      setEditing(false);
      toast.success("Profile updated");
    },
  });

  const revokeAllMutation = useMutation({
    mutationFn: authApi.logoutAll,
    onSuccess: () => {
      toast.success("All sessions revoked");
      signOutLocal();
    },
  });

  if (meQuery.isPending) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-48" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </CardContent>
      </Card>
    );
  }

  if (meQuery.isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Could not load profile</AlertTitle>
        <AlertDescription>
          {meQuery.error instanceof ApiError
            ? meQuery.error.detail
            : "Please refresh the page and try again."}
        </AlertDescription>
      </Alert>
    );
  }

  const user = meQuery.data;
  const updateError =
    updateMutation.error instanceof ApiError
      ? updateMutation.error.detail
      : null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div className="space-y-1.5">
          <CardTitle>Profile</CardTitle>
          <CardDescription>Your personal account details</CardDescription>
        </div>
        {!editing ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setFullName(user.full_name ?? "");
              setEditing(true);
            }}
          >
            <Pencil className="h-3.5 w-3.5" />
            Edit
          </Button>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-4">
        {updateError ? (
          <Alert variant="destructive">
            <AlertTitle>Update failed</AlertTitle>
            <AlertDescription>{updateError}</AlertDescription>
          </Alert>
        ) : null}

        {editing ? (
          <div className="space-y-2">
            <Label htmlFor="full-name">Full name</Label>
            <div className="flex gap-2">
              <Input
                id="full-name"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Your name"
              />
              <Button
                size="sm"
                onClick={() => updateMutation.mutate()}
                disabled={updateMutation.isPending}
              >
                Save
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setEditing(false)}
                disabled={updateMutation.isPending}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : null}

        <dl className="grid gap-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Email</dt>
            <dd className="font-medium">{user.email}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Full name</dt>
            <dd className="font-medium">{user.full_name ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Status</dt>
            <dd className="flex gap-2 pt-1">
              <span
                className={
                  user.is_active
                    ? "rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800"
                    : "rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground"
                }
              >
                {user.is_active ? "Active" : "Inactive"}
              </span>
              <span
                className={
                  user.is_locked
                    ? "rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800"
                    : "rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800"
                }
              >
                {user.is_locked ? "Locked" : "Unlocked"}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Last login</dt>
            <dd className="font-medium">{formatDateTime(user.last_login_at)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Member since</dt>
            <dd className="font-medium">{formatDateTime(user.created_at)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Organization</dt>
            <dd className="break-all font-mono text-xs">{user.organization_id}</dd>
          </div>
        </dl>
      </CardContent>
      <CardFooter className="flex flex-col items-start gap-2 border-t pt-6">
        <Button
          variant="destructive"
          size="sm"
          disabled={revokeAllMutation.isPending}
          onClick={() => {
            if (
              window.confirm(
                "Revoke all sessions including this one? You will be signed out everywhere.",
              )
            ) {
              revokeAllMutation.mutate();
            }
          }}
        >
          <ShieldOff className="h-4 w-4" />
          Sign out all devices
        </Button>
        <p className="text-xs text-muted-foreground">
          Revokes every active refresh token for your account.
        </p>
      </CardFooter>
    </Card>
  );
}
