import {
  EXPERIENCE_UNITS,
  type ExperienceUnit,
} from "../experienceUnits";

export function ExperienceDock({
  activeUnit,
  onSelect,
}: {
  activeUnit: ExperienceUnit;
  onSelect: (unit: ExperienceUnit) => void;
}) {
  return (
    <nav className="perspective-switch experience-dock" aria-label="观察方式">
      {EXPERIENCE_UNITS.map(({ key, glyph, label, contentKey }) => (
        <button
          key={key}
          type="button"
          aria-pressed={activeUnit === key}
          data-content-key={contentKey}
          onClick={() => onSelect(key)}
        >
          <span className="dock-glyph" aria-hidden="true">{glyph}</span>
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
}
