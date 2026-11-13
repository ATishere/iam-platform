"use client";

import { LogOut, Menu } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useSignOut } from "@/features/auth/use-sign-out";
import { useAuthStore } from "@/stores/auth-store";

export function Topbar({ onMenuClick }: { onMenuClick: () => void }) {
  const user = useAuthStore((state) => state.user);
  const { signOut, isPending } = useSignOut();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b bg-background px-4 md:px-8">
      <div className="flex items-center gap-3 md:hidden">
        <Button
          variant="ghost"
          size="icon"
          onClick={onMenuClick}
          aria-label="Open navigation"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <span className="text-sm font-semibold">IAM Platform</span>
      </div>
      <div className="hidden truncate text-sm text-muted-foreground md:block">
        {user?.email}
      </div>
      <Button
        variant="outline"
        size="sm"
        onClick={signOut}
        disabled={isPending}
      >
        <LogOut className="h-4 w-4" />
        Sign out
      </Button>
    </header>
  );
}
