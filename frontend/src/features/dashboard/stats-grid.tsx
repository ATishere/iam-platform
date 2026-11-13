"use client";

import { useQuery } from "@tanstack/react-query";
import { Lock, LogIn, ShieldAlert, UserCheck, Users } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { adminApi } from "@/lib/api/admin";

import { StatCard } from "./stat-card";

export function StatsGrid() {
  const query = useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: adminApi.dashboard.stats,
    refetchInterval: 30_000,
  });

  if (query.isPending) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-28 w-full" />
        ))}
      </div>
    );
  }

  if (query.error || !query.data) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-destructive">
          {query.error instanceof Error
            ? query.error.message
            : "Could not load dashboard statistics."}
        </CardContent>
      </Card>
    );
  }

  const stats = query.data;

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <StatCard
        label="Total users"
        value={stats.users_total}
        icon={<Users className="h-5 w-5" />}
      />
      <StatCard
        label="Active users"
        value={stats.users_active}
        icon={<UserCheck className="h-5 w-5" />}
      />
      <StatCard
        label="Locked users"
        value={stats.users_locked}
        icon={<Lock className="h-5 w-5" />}
      />
      <StatCard
        label="Logins (24h)"
        value={stats.recent_logins_24h}
        icon={<LogIn className="h-5 w-5" />}
      />
      <StatCard
        label="Failed logins (24h)"
        value={stats.failed_logins_24h}
        icon={<ShieldAlert className="h-5 w-5" />}
      />
    </div>
  );
}
