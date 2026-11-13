import { RecentEvents } from "@/features/dashboard/recent-events";
import { StatsGrid } from "@/features/dashboard/stats-grid";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Overview of users and recent security activity.
        </p>
      </div>
      <StatsGrid />
      <RecentEvents />
    </div>
  );
}
