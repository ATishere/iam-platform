"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

import { authApi } from "@/lib/api/auth";
import { useAuthStore } from "@/stores/auth-store";

export function useSignOut() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isPending, setIsPending] = useState(false);

  const signOutLocal = useCallback(() => {
    useAuthStore.getState().clear();
    queryClient.clear();
    router.replace("/login");
  }, [queryClient, router]);

  const signOut = useCallback(async () => {
    setIsPending(true);
    const refreshToken = useAuthStore.getState().refreshToken;
    try {
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } catch {
      // Local cleanup must proceed even if the server call fails.
    } finally {
      signOutLocal();
      setIsPending(false);
    }
  }, [signOutLocal]);

  return { signOut, signOutLocal, isPending };
}
