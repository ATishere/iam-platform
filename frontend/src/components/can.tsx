"use client";

import type { ReactNode } from "react";

import { usePermissions } from "@/hooks/use-permissions";

interface CanProps {
  permission?: string;
  anyOf?: string[];
  allOf?: string[];
  fallback?: ReactNode;
  children: ReactNode;
}

export function Can({
  permission,
  anyOf,
  allOf,
  fallback = null,
  children,
}: CanProps) {
  const { has, hasAny, hasAll, isLoading } = usePermissions();

  if (isLoading) return null;

  let allowed = true;
  if (permission) allowed = allowed && has(permission);
  if (anyOf && anyOf.length > 0) allowed = allowed && hasAny(anyOf);
  if (allOf && allOf.length > 0) allowed = allowed && hasAll(allOf);

  return <>{allowed ? children : fallback}</>;
}
