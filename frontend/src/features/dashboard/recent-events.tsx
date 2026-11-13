"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { adminApi } from "@/lib/api/admin";

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

export function RecentEvents() {
  const query = useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: adminApi.dashboard.stats,
    refetchInterval: 30_000,
  });

  if (query.isPending) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (query.error || !query.data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent security events</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-destructive">
          {query.error instanceof Error
            ? query.error.message
            : "Could not load recent security events."}
        </CardContent>
      </Card>
    );
  }

  const events = query.data.recent_security_events;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Recent security events</CardTitle>
        <CardDescription>
          Latest authentication and account activity.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No security events recorded yet.
          </p>
        ) : (
          <ul className="divide-y">
            {events.map((event) => (
              <li
                key={event.id}
                className="flex items-center justify-between gap-4 py-2 text-sm"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">{event.action}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    Actor&nbsp;
                    <span title={event.actor_id ?? undefined}>
                      {event.actor_id
                        ? `${event.actor_id.slice(0, 8)}…`
                        : "system"}
                    </span>
                    {" · "}
                    {dateFormatter.format(new Date(event.created_at))}
                  </p>
                </div>
                <Badge
                  variant={event.outcome === "success" ? "success" : "destructive"}
                >
                  {event.outcome}
                </Badge>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
