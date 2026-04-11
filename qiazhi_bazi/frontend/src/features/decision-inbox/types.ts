export type DecisionInboxCard = {
  id: string;
  title: string;
  markdown: string;
  conflictDetail?: string;
  displayText?: string;
  cardType?: "conflict" | "auditor-proposal" | "proposal";
  proposal?: unknown;
  skillId?: string;
  sovereigntyMark?: "PATTERN_SOVEREIGNTY";
};

export type VerdictChangeLog = {
  physics_diff?: string[];
  consensus_diff?: string[];
  text_diff_hint?: string;
};
