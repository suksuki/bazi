import type { ExperienceUnit } from "../experienceUnits";
import { ExperienceDock } from "./ExperienceDock";

export function ExperienceRuntimeOverlay({
  activeUnit,
  error,
  hideDock = false,
  onSelect,
}: {
  activeUnit: ExperienceUnit;
  error: string | null;
  hideDock?: boolean;
  onSelect: (unit: ExperienceUnit) => void;
}) {
  return (
    <>
      {!hideDock && <ExperienceDock activeUnit={activeUnit} onSelect={onSelect} />}
      {error && (
        <p className="runtime-error" role="alert">
          {error}
        </p>
      )}
    </>
  );
}
