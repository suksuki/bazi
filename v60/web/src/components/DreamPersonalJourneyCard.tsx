import { useEffect, useMemo, useState } from "react";

import type { DreamGroveCandidate } from "../api";
import {
  recordDreamPersonalCheckIn,
  selectDreamPersonalObservation,
} from "../dreamPersonalJourneyApi";
import {
  isDreamPersonalJourneyDisplayable,
  type DreamLifeDomain,
  type DreamPersonalCheckInStatus,
  type DreamPersonalJourney,
} from "../dreamPersonalJourneyTypes";

const DOMAIN_COPY: Record<
  DreamLifeDomain,
  { label: string; prompt: string }
> = {
  career: {
    label: "职责与位置",
    prompt: "最近哪一项投入、职责或位置变化，让你想看得更清楚？",
  },
  wealth: {
    label: "交换与回流",
    prompt: "最近哪一次投入、交换或回流，让你想继续观察？",
  },
  relationship: {
    label: "协作与边界",
    prompt: "最近哪段协作、关心或边界，让你还没有看清？",
  },
};

const CHECKIN_COPY: Array<{
  status: DreamPersonalCheckInStatus;
  label: string;
}> = [
  { status: "OBSERVED", label: "看见了" },
  { status: "NOT_OBSERVED", label: "暂未看见" },
  { status: "STILL_OBSERVING", label: "还在观察" },
];

function formatDate(value: string) {
  const [year, month, day] = value.split("-");
  return `${year}年${Number(month)}月${Number(day)}日`;
}

export function DreamPersonalJourneyCard({
  busy,
  candidates,
  journey: suppliedJourney,
  onStart,
}: {
  busy: boolean;
  candidates: DreamGroveCandidate[];
  journey: DreamPersonalJourney | null | undefined;
  onStart: (
    candidateRef: string,
    domain: DreamLifeDomain,
    question: string,
  ) => void;
}) {
  const [journey, setJourney] = useState(suppliedJourney);
  const [editing, setEditing] = useState(!suppliedJourney);
  const [domain, setDomain] = useState<DreamLifeDomain>(
    suppliedJourney?.inquiry.domain ?? "relationship",
  );
  const [question, setQuestion] = useState("");
  const [checkinStatus, setCheckinStatus] =
    useState<DreamPersonalCheckInStatus>("STILL_OBSERVING");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setJourney(suppliedJourney);
    if (!suppliedJourney) setEditing(true);
  }, [suppliedJourney]);

  const candidate = useMemo(
    () => candidates.find((item) => item.domain === domain) ?? null,
    [candidates, domain],
  );
  const boundCandidate = journey
    ? candidates.find(
        (item) =>
          item.candidate_ref === journey.inquiry.candidate_ref,
      ) ?? null
    : null;
  const journeyValid =
    journey !== null &&
    journey !== undefined &&
    boundCandidate !== null &&
    isDreamPersonalJourneyDisplayable(journey, {
      candidateRef: boundCandidate.candidate_ref,
      candidateHash: boundCandidate.candidate_hash,
      treeRef: boundCandidate.tree_ref,
    });

  const selectObservation = async (optionRef: string) => {
    if (!journeyValid) return;
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

  const recordCheckin = async () => {
    if (!journeyValid || !journey.observation) return;
    setSaving(true);
    setError(null);
    try {
      setJourney(
        await recordDreamPersonalCheckIn(
          journey,
          checkinStatus,
          note,
        ),
      );
      setNote("");
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : String(reason),
      );
    } finally {
      setSaving(false);
    }
  };

  if (journey && !journeyValid) {
    return (
      <aside
        className="dream-personal-card dream-personal-withheld"
        data-personal-journey-status="WITHHELD"
      >
        <strong>私人观察暂不可显示</strong>
        <p>记录与对应生命树没有完整对上，阿布不会补写你的问题。</p>
      </aside>
    );
  }

  const routeAvailable =
    candidate?.chapter_route?.status === "AVAILABLE";
  const normalizedQuestion = question.trim().replace(/\s+/g, " ");
  const canStart =
    candidate !== null &&
    routeAvailable &&
    normalizedQuestion.length >= 4 &&
    normalizedQuestion.length <= 120;

  if (editing || !journeyValid) {
    return (
      <aside
        className="dream-personal-card dream-personal-intake"
        data-personal-journey-status="INTAKE"
        aria-label="带一个现实问题进入梦境"
      >
        <header>
          <small>只属于你的观察</small>
          <strong>带一个现实问题入梦</strong>
          <p>
            选一个你此刻真正关心的方向。系统只按主题对应一条人生，不替你解释问题。
          </p>
        </header>
        <fieldset>
          <legend>我想观察</legend>
          <div className="dream-personal-domain-options">
            {candidates.map((item) => (
              <button
                aria-pressed={domain === item.domain}
                data-route-status={
                  item.chapter_route?.status ?? "WITHHELD"
                }
                key={item.candidate_ref}
                onClick={() => setDomain(item.domain)}
                type="button"
              >
                <span>{DOMAIN_COPY[item.domain].label}</span>
                <small>{item.public_alias}</small>
              </button>
            ))}
          </div>
        </fieldset>
        <label className="dream-personal-question">
          <span>{DOMAIN_COPY[domain].prompt}</span>
          <textarea
            maxLength={120}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="写下一句具体、现在仍可观察的问题"
            rows={3}
            value={question}
          />
          <small>{normalizedQuestion.length} / 120</small>
        </label>
        {candidate && (
          <p className="dream-personal-match">
            <span>对应人生</span>
            <strong>{candidate.public_alias}</strong>
            <em>
              {routeAvailable
                ? "这条人生有一段可进入的新事件。"
                : "这条人生本季已走完，新的可进入章节尚未抵达。"}
            </em>
          </p>
        )}
        <button
          className="dream-personal-primary"
          disabled={busy || !canStart}
          onClick={() =>
            candidate &&
            onStart(
              candidate.candidate_ref,
              domain,
              normalizedQuestion,
            )
          }
          type="button"
        >
          {routeAvailable
            ? `带着这个问题去看${candidate?.public_alias ?? "这棵树"}`
            : "对应人生暂时没有可进入章节"}
        </button>
        <p className="dream-personal-boundary">
          问题只保存在你的私密梦境记录；不进入命理证据，也不改变树里的问题、选择或结果。
        </p>
      </aside>
    );
  }

  return (
    <aside
      className="dream-personal-card"
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
      aria-label="我的现实问题与观察"
    >
      <header>
        <small>我的问题 · {journey.inquiry.public_alias}</small>
        <strong>{journey.inquiry.question}</strong>
        <p>梦中结局没有回答它；这条记录只帮你把视线带回现实。</p>
      </header>

      {journey.status === "DREAM_INTERRUPTED" && (
        <section>
          <b>这次没有留下完整判断</b>
          <p>错过仍被保留，但不会倒推替你作答。可以换一个问题再出发。</p>
        </section>
      )}

      {journey.status === "AWAITING_OBSERVATION" && (
        <section className="dream-personal-observation-options">
          <small>未来七天</small>
          <b>选一件现实中可以核对的事</b>
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

      {journey.observation && (
        <section
          className="dream-personal-task"
          data-personal-observation-task-ref={
            journey.observation.task_ref
          }
          data-personal-observation-task-hash={
            journey.observation.task_hash
          }
        >
          <small>
            观察到 {formatDate(journey.observation.checkpoint_on)}
          </small>
          <b>{journey.observation.option.label}</b>
          <p>{journey.observation.option.summary}</p>
        </section>
      )}

      {journey.status === "FOLLOWED_UP" &&
        journey.latest_checkin && (
          <section
            className="dream-personal-latest-checkin"
            data-personal-checkin-ref={
              journey.latest_checkin.checkin_ref
            }
          >
            <small>第 {journey.checkin_count} 次回访</small>
            <b>
              {
                CHECKIN_COPY.find(
                  ({ status }) =>
                    status === journey.latest_checkin?.status,
                )?.label
              }
            </b>
            {journey.latest_checkin.note && (
              <p>{journey.latest_checkin.note}</p>
            )}
            <em>
              这是你的现实自述，不验证梦境，也不会变成命理结论。
            </em>
          </section>
        )}

      {(journey.status === "OBSERVING" ||
        journey.status === "FOLLOWED_UP") && (
        <section className="dream-personal-checkin">
          <small>记录一次回访</small>
          <div>
            {CHECKIN_COPY.map((item) => (
              <button
                aria-pressed={checkinStatus === item.status}
                key={item.status}
                onClick={() => setCheckinStatus(item.status)}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
          <textarea
            maxLength={160}
            onChange={(event) => setNote(event.target.value)}
            placeholder="可选：留下一句已经发生的事实"
            rows={2}
            value={note}
          />
          <button
            className="dream-personal-primary"
            disabled={busy || saving}
            onClick={() => void recordCheckin()}
            type="button"
          >
            保存这次回访
          </button>
        </section>
      )}

      {error && <p className="dream-personal-error">{error}</p>}
      {(journey.status === "DREAM_INTERRUPTED" ||
        journey.status === "AWAITING_OBSERVATION" ||
        (journey.status === "FOLLOWED_UP" &&
          journey.latest_checkin?.status !== "STILL_OBSERVING")) && (
        <button
          className="dream-personal-secondary"
          disabled={busy || saving}
          onClick={() => {
            setQuestion("");
            setEditing(true);
          }}
          type="button"
        >
          换一个现实问题
        </button>
      )}
      <p className="dream-personal-boundary">
        私密自我观察 · 非命理证据 · 不改变三棵树、章节路线或世界结果。
      </p>
    </aside>
  );
}
