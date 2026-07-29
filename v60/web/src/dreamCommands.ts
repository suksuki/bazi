import type { DreamCommand, TreeOrgan } from "./api";

export function commandForOrgan(organ: TreeOrgan): DreamCommand {
  if (organ.role === "EVIDENCE_LEAF") return "OBSERVE_EVIDENCE";
  if (organ.role === "STRUCTURE_BRANCH") return "OBSERVE_STRUCTURE";
  if (organ.role === "QUESTION_FLOWER") return "OPEN_QUESTION";
  throw new Error("tree_organ_has_no_observation_command");
}
