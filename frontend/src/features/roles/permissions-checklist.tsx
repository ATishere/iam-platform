"use client";

import { Checkbox } from "@/components/ui/checkbox";
import type { Permission } from "@/lib/api/admin";

interface PermissionsChecklistProps {
  permissions: Permission[];
  selected: string[];
  onChange: (codes: string[]) => void;
}

export function PermissionsChecklist({
  permissions,
  selected,
  onChange,
}: PermissionsChecklistProps) {
  const toggle = (code: string) => {
    onChange(
      selected.includes(code)
        ? selected.filter((c) => c !== code)
        : [...selected, code],
    );
  };

  return (
    <div className="max-h-56 space-y-2 overflow-y-auto rounded-md border p-3">
      {permissions.map((permission) => (
        <label key={permission.id} className="flex items-start gap-2 text-sm">
          <Checkbox
            className="mt-0.5"
            checked={selected.includes(permission.code)}
            onChange={() => toggle(permission.code)}
          />
          <span>
            <span className="font-mono text-xs">{permission.code}</span>
            {permission.description ? (
              <span className="ml-2 text-xs text-muted-foreground">
                {permission.description}
              </span>
            ) : null}
          </span>
        </label>
      ))}
    </div>
  );
}
