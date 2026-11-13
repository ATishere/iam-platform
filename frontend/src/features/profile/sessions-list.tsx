"use client";

import { useQuery } from "@tanstack/react-query";
import { Monitor } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { usersApi } from "@/lib/api/users";
import { formatDateTime } from "@/lib/utils";

export function SessionsList() {
  const query = useQuery({
    queryKey: ["me", "sessions"],
    queryFn: usersApi.mySessions,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active sessions</CardTitle>
        <CardDescription>
          Devices that currently hold a refresh token for your account
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {query.isPending ? (
          <>
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </>
        ) : query.isError ? (
          <Alert variant="destructive">
            <AlertTitle>Could not load sessions</AlertTitle>
            <AlertDescription>
              {query.error instanceof ApiError
                ? query.error.detail
                : "Please refresh the page and try again."}
            </AlertDescription>
          </Alert>
        ) : query.data.length === 0 ? (
          <p className="text-sm text-muted-foreground">No sessions found.</p>
        ) : (
          query.data.map((session) => (
            <div
              key={session.id}
              className="flex items-start gap-3 rounded-md border p-3"
            >
              <Monitor
                className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground"
                aria-hidden="true"
              />
              <div className="min-w-0 flex-1 space-y-1">
                <p className="truncate text-sm font-medium">
                  {session.user_agent ?? "Unknown device"}
                </p>
                <p className="text-xs text-muted-foreground">
                  IP: {session.ip_address ?? "unknown"}
                </p>
                <p className="text-xs text-muted-foreground">
                  Last seen: {formatDateTime(session.last_seen_at)}
                </p>
                <p className="text-xs text-muted-foreground">
                  Started: {formatDateTime(session.created_at)}
                </p>
              </div>
              <span
                className={
                  session.is_active
                    ? "rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800"
                    : "rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground"
                }
              >
                {session.is_active ? "Active" : "Inactive"}
              </span>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
