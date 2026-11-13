"use client";

import { useCallback } from "react";
import { useQuery } from "@tanstack/react-query";

import { usersApi } from "@/lib/api/users";
import { useAuthStore } from "@/stores/auth-store";

export function usePermissions() {
  const accessToken = useAuthStore((state) => state.accessToken);

  const query = useQuery({
    queryKey: ["me", "permissions"],
    queryFn: usersApi.myPermissions,
    enabled: Boolean(accessToken),
    staleTime: 60_000,
  });

  const permissions = query.data?.permissions ?? [];

  const has = useCallback(
    (permission: string) => permissions.includes(permission),
    [permissions],
  );

  const hasAny = useCallback(
    (required: string[]) => required.some((p) => permissions.includes(p)),
    [permissions],
  );

  const hasAll = useCallback(
    (required: string[]) => required.every((p) => permissions.includes(p)),
    [permissions],
  );

  return {
    permissions,
    has,
    hasAny,
    hasAll,
    isLoading: query.isLoading,
  };
}
