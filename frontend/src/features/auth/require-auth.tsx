"use client";

import { useCallback, useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { Spinner } from "@/components/ui/spinner";
import { ApiError } from "@/lib/api/client";
import { usersApi } from "@/lib/api/users";
import { useAuthStore } from "@/stores/auth-store";

export function RequireAuth({ children }: { children: ReactNode }) {
  const router = useRouter();
  const accessToken = useAuthStore((state) => state.accessToken);
  const hydrated = useAuthStore((state) => state.hydrated);
  const setUser = useAuthStore((state) => state.setUser);
  const clear = useAuthStore((state) => state.clear);

  const me = useQuery({
    queryKey: ["me"],
    queryFn: usersApi.me,
    enabled: hydrated && Boolean(accessToken),
    retry: false,
  });

  const handleUnauthorized = useCallback(() => {
    clear();
    router.replace("/login");
  }, [clear, router]);

  useEffect(() => {
    if (hydrated && !accessToken) {
      router.replace("/login");
    }
  }, [hydrated, accessToken, router]);

  useEffect(() => {
    if (me.data) {
      setUser(me.data);
    }
  }, [me.data, setUser]);

  useEffect(() => {
    if (me.error instanceof ApiError) {
      if (me.error.status === 401 || me.error.status === 403) {
        handleUnauthorized();
      }
    }
  }, [me.error, handleUnauthorized]);

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if (!accessToken) {
    return null;
  }

  if (me.isPending) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  return <>{children}</>;
}
