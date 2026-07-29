import type { ExperienceUnit } from "../experienceUnits";
import { ExperienceDock } from "./ExperienceDock";

export function ExperienceRuntimeOverlay({
  activeUnit,
  error,
  onSelect,
}: {
  activeUnit: ExperienceUnit;
  error: string | null;
  onSelect: (unit: ExperienceUnit) => void;
}) {
  return (
    <>
      <ExperienceDock activeUnit={activeUnit} onSelect={onSelect} />
      {error && (
        <p className="runtime-error" role="alert">
          {error}
        </p>
      )}
    </>
  );
}
