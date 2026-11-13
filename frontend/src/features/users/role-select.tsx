"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import type { Role } from "@/lib/api/admin";

interface RoleSelectProps {
  roles: Role[];
  selected: string[];
  onChange: (roleIds: string[]) => void;
}

export function RoleSelect({ roles, selected, onChange }: RoleSelectProps) {
  const toggle = (roleId: string) => {
    onChange(
      selected.includes(roleId)
        ? selected.filter((id) => id !== roleId)
        : [...selected, roleId],
    );
  };

  return (
    <div className="max-h-48 space-y-2 overflow-y-auto rounded-md border p-3">
      {roles.map((role) => (
        <label
          key={role.id}
          className="flex items-center gap-2 text-sm"
        >
          <Checkbox
            checked={selected.includes(role.id)}
            onChange={() => toggle(role.id)}
          />
          <span>
            {role.name}
            <span className="ml-2 text-xs text-muted-foreground">
              {role.permission_codes.length} perms
            </span>
          </span>
        </label>
      ))}
    </div>
  );
}
