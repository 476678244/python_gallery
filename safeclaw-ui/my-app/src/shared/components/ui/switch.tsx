"use client";

import { cn } from "@/shared/utils/cn";

interface SwitchProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
  size?: "sm" | "md" | "lg";
}

export function Switch({
  checked,
  onCheckedChange,
  disabled = false,
  size = "md",
}: SwitchProps) {
  const sizeClasses = {
    sm: "w-8 h-4",
    md: "w-11 h-6",
    lg: "w-14 h-7",
  };

  const thumbClasses = {
    sm: "w-3 h-3",
    md: "w-5 h-5",
    lg: "w-6 h-6",
  };

  const translateClasses = {
    sm: checked ? "translate-x-4" : "translate-x-0.5",
    md: checked ? "translate-x-5" : "translate-x-0.5",
    lg: checked ? "translate-x-7" : "translate-x-0.5",
  };

  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onCheckedChange(!checked)}
      className={cn(
        "relative inline-flex items-center rounded-full transition-colors",
        sizeClasses[size],
        checked
          ? "bg-blue-500"
          : "bg-slate-200",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <span
        className={cn(
          "inline-block rounded-full bg-white shadow transition-transform",
          thumbClasses[size],
          translateClasses[size]
        )}
      />
    </button>
  );
}
