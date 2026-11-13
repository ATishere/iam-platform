"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import {
  KeyRound,
  LayoutDashboard,
  ScrollText,
  Shield,
  ShieldAlert,
  ShieldCheck,
  UserCircle,
  Users,
} from "lucide-react";

import { usePermissions } from "@/hooks/use-permissions";
import { useAuthStore } from "@/stores/auth-store";
import { cn, initials } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  permission?: string;
}

const NAV: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/users", label: "Users", icon: Users, permission: "users:read" },
  { href: "/roles", label: "Roles", icon: Shield, permission: "roles:read" },
  {
    href: "/permissions",
    label: "Permissions",
    icon: KeyRound,
    permission: "roles:read",
  },
  {
    href: "/audit",
    label: "Audit log",
    icon: ScrollText,
    permission: "audit:read",
  },
  {
    href: "/security",
    label: "Security events",
    icon: ShieldAlert,
    permission: "audit:read",
  },
  { href: "/profile", label: "Profile", icon: UserCircle },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/dashboard") return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { has, isLoading } = usePermissions();
  const user = useAuthStore((state) => state.user);

  const items = NAV.filter(
    (item) =>
      !item.permission || (!isLoading && has(item.permission)),
  );

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <ShieldCheck className="h-6 w-6 text-primary" aria-hidden="true" />
        <div>
          <p className="text-sm font-semibold">IAM Platform</p>
          <p className="text-xs text-muted-foreground">Admin console</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {items.map((item) => {
          const Icon = item.icon;
          const active = isActive(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      {user ? (
        <div className="border-t p-3">
          <div className="flex items-center gap-3 rounded-md px-2 py-2">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-semibold">
              {initials(user.full_name, user.email)}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">
                {user.full_name ?? user.email}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {user.email}
              </p>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
