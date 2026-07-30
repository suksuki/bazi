import { useEffect, useState } from "react";

import { selectDreamPersonalObservation } from "../dreamPersonalJourneyApi";
import {
  isDreamPersonalJourneyDisplayable,
  type DreamPersonalJourney,
} from "../dreamPersonalJourneyTypes";

export function DreamPersonalJourneyEncounter({
  busy,
  encounterRef,
  journey: suppliedJourney,
}: {
  busy: boolean;
  encounterRef: string;
  journey: DreamPersonalJourney | null | undefined;
}) {
  const [journey, setJourney] = useState(suppliedJourney);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setJourney(suppliedJourney), [suppliedJourney]);

  if (!journey) return null;
  if (
    !isDreamPersonalJourneyDisplayable(journey, { encounterRef })
  ) {
    return (
      <aside
        className="dream-personal-encounter dream-personal-withheld"
        data-personal-journey-status="WITHHELD"
      >
        <strong>你带来的问题暂时留在私密记录里</strong>
        <p>它与当前相遇没有完整对上，阿布不会补写或猜测。</p>
      </aside>
    );
  }

  const selectObservation = async (optionRef: string) => {
    setSaving(true);
    setError(null);
    try {
      setJourney(
        await selectDreamPersonalObservation(journey, optionRef),
      );
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : String(reason),
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <aside
      className="dream-personal-encounter"
      data-personal-journey-status={journey.status}
      data-inquiry-ref={journey.inquiry.inquiry_ref}
      data-inquiry-hash={journey.inquiry.inquiry_hash}
      data-private-to-account={journey.private_to_account}
      data-mingli-evidence-role={journey.mingli_evidence_role}
      data-dream-answers-owner-question={
        journey.dream_answers_owner_question
      }
      data-tree-candidate-set-or-order-changed={
        journey.tree_candidate_set_or_order_changed
      }
      data-chapter-route-changed={journey.chapter_route_changed}
      data-episode-question-changed={journey.episode_question_changed}
      data-answer-changed={journey.answer_changed}
      data-npc-choice-changed={journey.npc_choice_changed}
      data-world-outcome-changed={journey.world_outcome_changed}
      data-mingli-write-allowed={journey.mingli_write_allowed}
      data-decision-write-allowed={journey.decision_write_allowed}
      data-knowledge-write-allowed={journey.knowledge_write_allowed}
      aria-label="带入梦境的私人现实问题"
    >
      <small>我的问题 · {journey.inquiry.public_alias}</small>
      <strong>{journey.inquiry.question}</strong>
      <p>
        这段人生只是一面观察镜。它不替你回答，也不改变树中的问题、选择或后来结果。
      </p>

      {journey.status === "AWAITING_OBSERVATION" && (
        <section className="dream-personal-encounter-observation">
          <span>把视线带回现实</span>
          <b>留一个未来七天可以核对的观察</b>
          <div>
            {journey.observation_options.map((option) => (
              <button
                data-personal-observation-option-ref={option.option_ref}
                disabled={busy || saving}
                key={option.option_ref}
                onClick={() => void selectObservation(option.option_ref)}
                type="button"
              >
                <span>{option.label}</span>
                <small>{option.summary}</small>
              </button>
            ))}
          </div>
        </section>
      )}

      {(journey.status === "OBSERVING" ||
        journey.status === "FOLLOWED_UP") &&
        journey.observation && (
          <section
            className="dream-personal-encounter-saved"
            data-personal-observation-task-ref={
              journey.observation.task_ref
            }
          >
            <span>现实观察已保存</span>
            <b>{journey.observation.option.label}</b>
            <p>{journey.observation.option.summary}</p>
            <em>回到雾林后，可以为它留下回访。</em>
          </section>
        )}

      {error && <p className="dream-personal-error">{error}</p>}
    </aside>
  );
}
