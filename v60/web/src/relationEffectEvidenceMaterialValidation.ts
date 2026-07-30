import type { RelationEffectEvidenceMaterialBibliography } from "./homeRelationEffectEvidenceMaterialTypes";

const CONTROL_CHARACTER = /[\u0000-\u001f\u007f]/;
const URL_PREFIXES = [
  "http:",
  "https:",
  "ftp:",
  "file:",
  "data:",
  "www.",
] as const;

export function normalizeRelationEffectMaterialBibliography(
  value: RelationEffectEvidenceMaterialBibliography,
): RelationEffectEvidenceMaterialBibliography {
  return {
    title: value.title.trim(),
    responsible_party: value.responsible_party.trim(),
    edition_or_publication_identity:
      value.edition_or_publication_identity.trim(),
    locator: value.locator.trim(),
  };
}

export function isRelationEffectMaterialBibliographyValid(
  value: RelationEffectEvidenceMaterialBibliography,
): boolean {
  const normalized = normalizeRelationEffectMaterialBibliography(value);
  return (
    isBoundedMetadata(normalized.title, 240) &&
    isBoundedMetadata(normalized.responsible_party, 180) &&
    isBoundedMetadata(
      normalized.edition_or_publication_identity,
      180,
    ) &&
    isBoundedMetadata(normalized.locator, 180)
  );
}

function isBoundedMetadata(value: string, maxLength: number): boolean {
  const lowered = value.toLowerCase();
  return (
    value.length >= 1 &&
    value.length <= maxLength &&
    !CONTROL_CHARACTER.test(value) &&
    !lowered.includes("://") &&
    !URL_PREFIXES.some((prefix) => lowered.startsWith(prefix))
  );
}
