"use client";

import { SEED_YEAR_MAX, SEED_YEAR_MIN, SEED_YEAR_STRINGS } from "@/components/seedYearRange";

type Props = {
  value: number;
  onChange: (year: number) => void;
  className?: string;
  disabled?: boolean;
  id?: string;
  "aria-label"?: string;
};

export function ReferenceYearSelect({ value, onChange, className, disabled, id, "aria-label": ariaLabel }: Props) {
  const clamped = Math.min(SEED_YEAR_MAX, Math.max(SEED_YEAR_MIN, Math.round(Number(value) || SEED_YEAR_MIN)));
  return (
    <select
      id={id}
      aria-label={ariaLabel}
      disabled={disabled}
      value={String(clamped)}
      onChange={(e) => {
        const y = Number(e.target.value);
        if (!Number.isFinite(y)) return;
        onChange(y);
      }}
      className={className}
    >
      {SEED_YEAR_STRINGS.map((y) => (
        <option key={y} value={y}>
          {y}
        </option>
      ))}
    </select>
  );
}
