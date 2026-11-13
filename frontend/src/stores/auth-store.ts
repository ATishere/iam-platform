"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { TokenPair, User } from "@/lib/api/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  hydrated: boolean;
  setTokens: (pair: TokenPair) => void;
  setUser: (user: User | null) => void;
  setHydrated: (hydrated: boolean) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      hydrated: false,
      setTokens: (pair) =>
        set({
          accessToken: pair.access_token,
          refreshToken: pair.refresh_token,
        }),
      setUser: (user) => set({ user }),
      setHydrated: (hydrated) => set({ hydrated }),
      clear: () =>
        set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: "iam-auth",
      storage: createJSONStorage(() => sessionStorage),
      skipHydration: true,
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    },
  ),
);
