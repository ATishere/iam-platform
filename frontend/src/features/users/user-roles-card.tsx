"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { adminApi, type Role, type UserAdmin } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";

import { RoleSelect } from "./role-select";

interface UserRolesCardProps {
  user: UserAdmin;
  roles: Role[];
}

export function UserRolesCard({ user, roles }: UserRolesCardProps) {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<string[]>([]);

  useEffect(() => {
    const byName = new Map(roles.map((role) => [role.name, role.id]));
    setSelected(
      user.roles
        .map((name) => byName.get(name))
        .filter((id): id is string => Boolean(id)),
    );
  }, [user, roles]);

  const mutation = useMutation({
    mutationFn: () => adminApi.users.setRoles(user.id, selected),
    onSuccess: () => {
      toast.success("Roles updated");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "user", user.id] });
    },
    onError: (error) =>
      toast.error(error instanceof ApiError ? error.detail : "Update failed"),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Roles</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <RoleSelect roles={roles} selected={selected} onChange={setSelected} />
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending ? "Saving..." : "Save roles"}
        </Button>
      </CardContent>
    </Card>
  );
}
