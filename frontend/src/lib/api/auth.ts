import { apiFetch } from "./client";
import type { LoginRequest, RegisterRequest, TokenPair, User } from "./types";

export const authApi = {
  login(data: LoginRequest): Promise<TokenPair> {
    return apiFetch<TokenPair>("/auth/login", {
      method: "POST",
      body: data,
      auth: false,
    });
  },

  register(data: RegisterRequest): Promise<User> {
    return apiFetch<User>("/auth/register", {
      method: "POST",
      body: data,
      auth: false,
    });
  },

  logout(refreshToken: string): Promise<void> {
    return apiFetch<void>("/auth/logout", {
      method: "POST",
      body: { refresh_token: refreshToken },
      retryOn401: false,
    });
  },

  logoutAll(): Promise<void> {
    return apiFetch<void>("/auth/logout-all", { method: "POST" });
  },

  changePassword(data: {
    old_password: string;
    new_password: string;
  }): Promise<void> {
    return apiFetch<void>("/auth/change-password", {
      method: "POST",
      body: data,
    });
  },
};
