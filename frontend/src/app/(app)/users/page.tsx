"use client";

import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { Can } from "@/components/can";
import { Pagination } from "@/components/pagination";
import { Button } from "@/components/ui/button";
import { adminApi } from "@/lib/api/admin";
import { CreateUserDialog } from "@/features/users/create-user-dialog";
import { UserSearch } from "@/features/users/user-search";
import { UsersTable } from "@/features/users/users-table";

type StatusFilter = "all" | "active" | "inactive";

export default function UsersPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);

  const query = useQuery({
    queryKey: ["admin", "users", { search, status, page }],
    queryFn: () =>
      adminApi.users.list({
        q: search || undefined,
        is_active: status === "all" ? undefined : status === "active",
        page,
        page_size: 20,
      }),
    placeholderData: keepPreviousData,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Users</h1>
          <p className="text-sm text-muted-foreground">
            Manage members of your organization.
          </p>
        </div>
        <Can permission="users:create">
          <Button onClick={() => setCreateOpen(true)}>Create user</Button>
        </Can>
      </div>

      <UserSearch
        value={search}
        onChange={(value) => {
          setSearch(value);
          setPage(1);
        }}
        activeFilter={status}
        onActiveFilterChange={(value) => {
          setStatus(value);
          setPage(1);
        }}
      />

      <UsersTable users={query.data?.items} isLoading={query.isPending} />

      <Pagination
        page={page}
        pageSize={20}
        total={query.data?.total ?? 0}
        onChange={setPage}
      />

      <CreateUserDialog open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
