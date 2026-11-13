"use client";

import { useEffect, useRef, useState } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";

interface UserSearchProps {
  value: string;
  onChange: (value: string) => void;
  activeFilter: "all" | "active" | "inactive";
  onActiveFilterChange: (value: "all" | "active" | "inactive") => void;
}

export function UserSearch({
  value,
  onChange,
  activeFilter,
  onActiveFilterChange,
}: UserSearchProps) {
  const [local, setLocal] = useState(value);
  const onChangeRef = useRef(onChange);

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    const timer = setTimeout(() => onChangeRef.current(local), 300);
    return () => clearTimeout(timer);
  }, [local]);

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <div className="flex-1 space-y-1">
        <Label htmlFor="user-search">Search</Label>
        <Input
          id="user-search"
          placeholder="Search by email or name"
          value={local}
          onChange={(e) => setLocal(e.target.value)}
        />
      </div>
      <div className="w-full space-y-1 sm:w-48">
        <Label htmlFor="user-status">Status</Label>
        <Select
          id="user-status"
          value={activeFilter}
          onChange={(e) =>
            onActiveFilterChange(
              e.target.value as "all" | "active" | "inactive",
            )
          }
        >
          <option value="all">All users</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </Select>
      </div>
    </div>
  );
}
