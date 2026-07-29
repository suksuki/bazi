import type { DreamSnapshot, TreeOrgan } from "./api";

export interface SemanticFocus {
  organ: TreeOrgan;
  contentKey: string;
  evidence: DreamSnapshot["public_evidence"];
  labFacts: DreamSnapshot["projections"]["lab"]["facts"];
  theaterEvidence: DreamSnapshot["public_evidence"];
  questionLinked: boolean;
  fruitLinked: boolean;
}

export type OrganRole = TreeOrgan["role"];
export type FocusSourcesHandler = (
  sourceRefs: readonly string[],
  preferredRoles: readonly OrganRole[],
) => void;

const CONTENT_KEYS: Record<string, string> = {
  evidence_leaf_world: "dream.focus.evidence-leaf-world",
  evidence_leaf_structure: "dream.focus.evidence-leaf-structure",
  structure_branch: "dream.focus.structure-branch",
  question_flower: "dream.focus.question-flower",
  outcome_fruit: "dream.focus.outcome-fruit",
};

export function deriveSemanticFocus(
  snapshot: DreamSnapshot,
  organRef: string | null,
): SemanticFocus | null {
  if (!organRef) return null;
  const organ = snapshot.tree.organs.find(
    (candidate) => candidate.visible && candidate.organ_ref === organRef,
  );
  if (!organ) return null;

  const sourceRefs = new Set(organ.source_refs);
  const fruitLinked =
    organ.role === "OUTCOME_FRUIT" &&
    organ.source_refs.includes(snapshot.lineage.world_event_ref);
  const revealedEvidenceRefs = new Set(
    fruitLinked ? snapshot.lineage.revealed_evidence_refs : [],
  );
  const evidence = snapshot.public_evidence.filter(
    (item) =>
      sourceRefs.has(item.evidence_ref) ||
      revealedEvidenceRefs.has(item.evidence_ref),
  );
  const labFacts = snapshot.projections.lab.facts.filter(
    (fact) => sourceRefs.has(fact.fact_ref) || sourceRefs.has(fact.source_ref),
  );
  const theaterRefs = new Set(snapshot.projections.theater.evidence_refs);
  const theaterEvidence = evidence.filter((item) =>
    theaterRefs.has(item.evidence_ref),
  );

  return {
    organ,
    contentKey:
      CONTENT_KEYS[organ.key] ?? `dream.focus.${organ.role.toLowerCase()}`,
    evidence,
    labFacts,
    theaterEvidence,
    questionLinked:
      organ.role === "QUESTION_FLOWER" &&
      organ.source_refs.includes(snapshot.lineage.question_ref),
    fruitLinked,
  };
}

export function findOrganForSources(
  snapshot: DreamSnapshot,
  sourceRefs: readonly string[],
  preferredRoles: readonly OrganRole[],
): TreeOrgan | null {
  const refs = new Set(sourceRefs);
  const revealedEvidenceSelected = snapshot.lineage.revealed_evidence_refs.some(
    (ref) => refs.has(ref),
  );
  const candidates = snapshot.tree.organs.filter((organ) => {
    if (!organ.visible) return false;
    if (organ.source_refs.some((ref) => refs.has(ref))) return true;
    return (
      revealedEvidenceSelected &&
      organ.role === "OUTCOME_FRUIT" &&
      organ.source_refs.includes(snapshot.lineage.world_event_ref)
    );
  });

  return (
    [...candidates].sort((left, right) => {
      const leftPriority = preferredRoles.indexOf(left.role);
      const rightPriority = preferredRoles.indexOf(right.role);
      return normalizePriority(leftPriority) - normalizePriority(rightPriority);
    })[0] ?? null
  );
}

function normalizePriority(index: number): number {
  return index === -1 ? Number.MAX_SAFE_INTEGER : index;
}
