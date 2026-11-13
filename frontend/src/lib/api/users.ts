import { apiFetch } from "./client";
import type { MyPermissions, Session, User } from "./types";

export const usersApi = {
  me(): Promise<User> {
    return apiFetch<User>("/users/me");
  },

  updateMe(data: { full_name: string | null }): Promise<User> {
    return apiFetch<User>("/users/me", { method: "PATCH", body: data });
  },

  myPermissions(): Promise<MyPermissions> {
    return apiFetch<MyPermissions>("/users/me/permissions");
  },

  mySessions(): Promise<Session[]> {
    return apiFetch<Session[]>("/users/me/sessions");
  },
};
