import type { DreamSnapshot } from "../api";
import {
  isDreamAttentionFollowThroughDisplayable,
  type DreamAttentionFollowThrough,
  type DreamAttentionFollowThroughStatus,
  type DreamAttentionFollowThroughWorldResponse,
} from "../dreamAttentionFollowThroughTypes";

const STATUS_COPY: Record<
  DreamAttentionFollowThroughStatus,
  { kicker: string; detail: string }
> = {
  OBSERVING: {
    kicker: "上次留下的观察 · 正在继续",
    detail: "先读完两片叶和一条主脉，再独立留下判断。",
  },
  OBSERVATIONS_COMPLETE: {
    kicker: "共同线索已看完",
    detail: "观察目标仍在这里，但不会替任何答案提前加分。",
  },
  AWAITING_WORLD_RESPONSE: {
    kicker: "判断已封存 · 等世界自己回应",
    detail: "后来发生的事不会被这个观察目标改变。",
  },
  WORLD_RESPONSE_READY_HIDDEN: {
    kicker: "世界回应已到 · 尚未打开",
    detail: "果实里已有后来材料，打开前仍不预告答案。",
  },
  WORLD_RESPONSE_AVAILABLE: {
    kicker: "这轮已有世界材料可对照",
    detail: "材料已经公开，但语义是否对应仍未评价。",
  },
  RECONCILED_NOT_EVALUATED: {
    kicker: "一轮已走完 · 尚未判定",
    detail: "复盘已收下；观察目标与后来材料仍保持分开。",
  },
  RETURNED_NOT_EVALUATED: {
    kicker: "这次观察已有世界材料",
    detail: "它已随这条梦中生命回到林中，但没有被判定为应验。",
  },
};

export function DreamAttentionFollowThroughCard({
  followThrough,
  snapshot,
}: {
  followThrough: DreamAttentionFollowThrough | null | undefined;
  snapshot: DreamSnapshot;
}) {
  const requiredOrganRefs = snapshot.tree.organs
    .filter(
      ({ role }) =>
        role === "EVIDENCE_LEAF" || role === "STRUCTURE_BRANCH",
    )
    .map(({ organ_ref }) => organ_ref);
  const observedOrganRefs = requiredOrganRefs.filter((ref) =>
    snapshot.encounter.state.observed_organs.includes(ref),
  );
  const expectedStatus = expectedStatusForSnapshot(
    snapshot,
    observedOrganRefs.length,
  );
  const worldResponse = snapshot.reveal
    ? worldResponseFromSnapshot(snapshot)
    : null;

  if (
    expectedStatus === null ||
    !isDreamAttentionFollowThroughDisplayable(followThrough, {
      targetEncounterRef: snapshot.encounter.encounter_ref,
      targetTreeRef: snapshot.tree.tree_ref,
      requiredOrganRefs,
      observedOrganRefs,
      expectedStatus,
      worldResponse,
    })
  ) {
    return null;
  }

  return <FollowThroughMarkup followThrough={followThrough} mode="encounter" />;
}

export function DreamReturnedAttentionSummary({
  candidateRefs,
  followThrough,
}: {
  candidateRefs: readonly string[];
  followThrough: DreamAttentionFollowThrough | null | undefined;
}) {
  if (
    !isDreamAttentionFollowThroughDisplayable(followThrough, {
      candidateRefs,
      expectedStatus: "RETURNED_NOT_EVALUATED",
    })
  ) {
    return null;
  }

  return <FollowThroughMarkup followThrough={followThrough} mode="grove" />;
}

function FollowThroughMarkup({
  followThrough,
  mode,
}: {
  followThrough: DreamAttentionFollowThrough;
  mode: "encounter" | "grove";
}) {
  const copy = STATUS_COPY[followThrough.status];
  const response = followThrough.world_response;

  return (
    <aside
      className={`dream-attention-follow-through dream-attention-follow-through-${mode}`}
      data-follow-through-status={followThrough.status}
      data-follow-through-version={followThrough.contract_version}
      data-application-ref={followThrough.application_ref}
      data-application-hash={followThrough.application_hash}
      data-attention-ref={followThrough.attention_ref}
      data-attention-hash={followThrough.attention_hash}
      data-source-encounter-ref={followThrough.source_encounter_ref}
      data-source-encounter-version={followThrough.source_encounter_version}
      data-source-echo-ref={followThrough.source_echo_ref}
      data-source-echo-hash={followThrough.source_echo_hash}
      data-source-candidate-ref={followThrough.source_candidate_ref}
      data-source-candidate-hash={followThrough.source_candidate_hash}
      data-source-tree-ref={followThrough.source_tree_ref}
      data-target-tree-ref={followThrough.target_tree_ref}
      data-target-encounter-ref={followThrough.target_encounter_ref}
      data-observation-ref={followThrough.observation_ref}
      data-semantic-match-status={followThrough.semantic_match_status}
      data-answer-status={followThrough.answer_status}
      data-semantics={followThrough.semantics}
      data-evidence-role={followThrough.evidence_role}
      data-tree-candidate-set-or-order-changed={
        followThrough.tree_candidate_set_or_order_changed
      }
      data-question-changed={followThrough.question_changed}
      data-answer-changed={followThrough.answer_changed}
      data-npc-choice-changed={followThrough.npc_choice_changed}
      data-outcome-changed={followThrough.outcome_changed}
      data-mingli-write-allowed={followThrough.mingli_write_allowed}
      data-decision-write-allowed={followThrough.decision_write_allowed}
      data-knowledge-write-allowed={followThrough.knowledge_write_allowed}
      data-read-only={followThrough.read_only}
      aria-label="上次观察在这次相遇中的继续"
    >
      <header>
        <small>{copy.kicker}</small>
        <strong>{followThrough.label}</strong>
      </header>
      <p>{followThrough.summary}</p>

      <div
        className="dream-attention-progress"
        data-required-count={followThrough.progress.required_count}
        data-observed-count={followThrough.progress.observed_count}
        aria-label={`${followThrough.progress.observed_count} / ${followThrough.progress.required_count} 条共同线索已看见`}
      >
        <span>
          共同线索 · {followThrough.progress.observed_count} /{" "}
          {followThrough.progress.required_count}
        </span>
        <i aria-hidden="true">
          <b
            style={{
              width: `${
                (followThrough.progress.observed_count /
                  followThrough.progress.required_count) *
                100
              }%`,
            }}
          />
        </i>
      </div>

      <span className="dream-attention-status-detail">{copy.detail}</span>
      {response && <WorldResponse response={response} />}
      <em>
        只继续这条梦中观察；不改变问题、答案或世界结果，也不写入命理。
      </em>
    </aside>
  );
}

function WorldResponse({
  response,
}: {
  response: DreamAttentionFollowThroughWorldResponse;
}) {
  return (
    <section
      className="dream-attention-world-response"
      data-world-response-material-count={response.material_count}
    >
      <small>这次世界留下的材料 · 未评价对应关系</small>
      <strong>{response.actual_event}</strong>
      <ul>
        {response.evidence_summaries.map((summary, index) => (
          <li
            data-evidence-ref={response.evidence_refs[index]}
            key={response.evidence_refs[index]}
          >
            {summary}
          </li>
        ))}
      </ul>
    </section>
  );
}

function expectedStatusForSnapshot(
  snapshot: DreamSnapshot,
  observedCount: number,
): DreamAttentionFollowThroughStatus | null {
  switch (snapshot.encounter.status) {
    case "OBSERVING":
      return observedCount === 3 ? "OBSERVATIONS_COMPLETE" : "OBSERVING";
    case "QUESTION_OPEN":
      return "OBSERVATIONS_COMPLETE";
    case "WAITING_FOR_WORLD":
      return "AWAITING_WORLD_RESPONSE";
    case "REVEAL_READY":
      return "WORLD_RESPONSE_READY_HIDDEN";
    case "REVEALED":
      return "WORLD_RESPONSE_AVAILABLE";
    case "COMPLETED":
      return "RECONCILED_NOT_EVALUATED";
    default:
      return null;
  }
}

function worldResponseFromSnapshot(
  snapshot: DreamSnapshot,
): DreamAttentionFollowThroughWorldResponse {
  const reveal = snapshot.reveal;
  if (reveal === null) {
    return {
      actual_event: "",
      evidence_refs: [],
      evidence_summaries: [],
      material_count: 0,
    };
  }
  const evidence = [...reveal.reveal_json.actual_evidence].sort(
    (left, right) => left.evidence_ref.localeCompare(right.evidence_ref),
  );
  return {
    actual_event: reveal.reveal_json.actual_event,
    evidence_refs: evidence.map(({ evidence_ref }) => evidence_ref),
    evidence_summaries: evidence.map(({ summary }) => summary),
    material_count: evidence.length,
  };
}
