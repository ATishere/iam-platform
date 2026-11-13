"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { UserAdmin } from "@/lib/api/admin";
import { formatDateTime } from "@/lib/utils";

interface UsersTableProps {
  users: UserAdmin[] | undefined;
  isLoading: boolean;
}

export function UsersTable({ users, isLoading }: UsersTableProps) {
  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!users || users.length === 0) {
    return (
      <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">
        No users found.
      </div>
    );
  }

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Email</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Roles</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Last login</TableHead>
            <TableHead>Created</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {users.map((user) => (
            <TableRow key={user.id}>
              <TableCell>
                <Link
                  href={`/users/${user.id}`}
                  className="font-medium text-primary hover:underline"
                >
                  {user.email}
                </Link>
              </TableCell>
              <TableCell>{user.full_name ?? "—"}</TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-1">
                  {user.roles.length === 0 ? (
                    <span className="text-muted-foreground">—</span>
                  ) : (
                    user.roles.map((role) => (
                      <Badge key={role} variant="secondary">
                        {role}
                      </Badge>
                    ))
                  )}
                </div>
              </TableCell>
              <TableCell>
                {user.is_locked ? (
                  <Badge variant="destructive">Locked</Badge>
                ) : user.is_active ? (
                  <Badge variant="success">Active</Badge>
                ) : (
                  <Badge variant="outline">Inactive</Badge>
                )}
              </TableCell>
              <TableCell>{formatDateTime(user.last_login_at)}</TableCell>
              <TableCell>{formatDateTime(user.created_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
