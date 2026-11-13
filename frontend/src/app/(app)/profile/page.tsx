import type { Metadata } from "next";

import { ChangePasswordCard } from "@/features/profile/change-password-card";
import { ProfileCard } from "@/features/profile/profile-card";
import { SessionsList } from "@/features/profile/sessions-list";

export const metadata: Metadata = {
  title: "Profile",
};

export default function ProfilePage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
        <p className="text-sm text-muted-foreground">
          Manage your account details and review active sessions.
        </p>
      </div>
      <ProfileCard />
      <ChangePasswordCard />
      <SessionsList />
    </div>
  );
}
