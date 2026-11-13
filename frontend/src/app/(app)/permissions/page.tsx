import type { Metadata } from "next";

import { PermissionsTable } from "@/features/permissions/permissions-table";

export const metadata: Metadata = {
  title: "Permissions",
};

export default function PermissionsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Permissions</h1>
        <p className="text-sm text-muted-foreground">
          The permission catalog is managed by the platform and is read-only.
        </p>
      </div>
      <PermissionsTable />
    </div>
  );
}
