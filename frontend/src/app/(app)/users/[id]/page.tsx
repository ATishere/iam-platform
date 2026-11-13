"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Can } from "@/components/can";
import { adminApi } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";
import { UserActionsCard } from "@/features/users/user-actions-card";
import { UserDetailCard } from "@/features/users/user-detail-card";
import { UserRolesCard } from "@/features/users/user-roles-card";

export default function UserDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const userQuery = useQuery({
    queryKey: ["admin", "user", id],
    queryFn: () => adminApi.users.get(id),
  });

  const rolesQuery = useQuery({
    queryKey: ["admin", "roles"],
    queryFn: adminApi.roles.list,
  });

  if (userQuery.isPending) {
    return <Skeleton className="h-96 w-full" />;
  }

  if (userQuery.error || !userQuery.data) {
    return (
      <div className="space-y-4">
        <Link
          href="/users"
          className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <ArrowLeft className="h-3 w-3" aria-hidden="true" />
          Back to users
        </Link>
        <Alert variant="destructive">
          <AlertDescription>
            {userQuery.error instanceof ApiError
              ? userQuery.error.detail
              : "Could not load this user."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const user = userQuery.data;

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/users"
          className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <ArrowLeft className="h-3 w-3" aria-hidden="true" />
          Back to users
        </Link>
        <div className="mt-2 flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">
            {user.full_name ?? user.email}
          </h1>
          {user.is_locked ? (
            <Badge variant="destructive">Locked</Badge>
          ) : user.is_active ? (
            <Badge variant="success">Active</Badge>
          ) : (
            <Badge variant="outline">Inactive</Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground">{user.email}</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <UserDetailCard user={user} />
        <div className="space-y-4">
          <Can permission="roles:read">
            <UserRolesCard user={user} roles={rolesQuery.data?.items ?? []} />
          </Can>
          <UserActionsCard user={user} />
        </div>
      </div>
    </div>
  );
}
