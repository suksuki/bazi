export const DREAM_RETURN_ECHO_VERSION = "v60.dream-return-echo.001" as const;

export interface DreamReturnEcho {
  contract_version: typeof DREAM_RETURN_ECHO_VERSION;
  echo_ref: string;
  echo_hash: string;
  encounter_ref: string;
  public_alias: string;
  episode_title: string;
  judgment: {
    choice_label: string;
    summary: string;
  };
  world_response: {
    summary: string;
    evidence_summaries: string[];
  };
  still_to_observe: {
    summary: string;
  };
  abu_recap: {
    meaning: string;
    boundary: string;
    next_attention: string;
  };
  semantics: "DREAM_LIFE_RETURN_ECHO_ONLY";
  owner_mingli_evidence_allowed: false;
  dream_outcome_admitted_as_owner_evidence: false;
  tree_candidate_set_or_order_changed: false;
  read_only: true;
  decision_write_allowed: false;
  knowledge_write_allowed: false;
  mingli_write_allowed: false;
  canonical_write_allowed: false;
}

export function isDreamReturnEchoDisplayable(
  echo: DreamReturnEcho | null | undefined,
): echo is DreamReturnEcho {
  return (
    echo?.contract_version === DREAM_RETURN_ECHO_VERSION &&
    echo.semantics === "DREAM_LIFE_RETURN_ECHO_ONLY" &&
    echo.owner_mingli_evidence_allowed === false &&
    echo.dream_outcome_admitted_as_owner_evidence === false &&
    echo.tree_candidate_set_or_order_changed === false &&
    echo.read_only === true &&
    echo.decision_write_allowed === false &&
    echo.knowledge_write_allowed === false &&
    echo.mingli_write_allowed === false &&
    echo.canonical_write_allowed === false
  );
}
