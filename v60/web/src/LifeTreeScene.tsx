import type {
  DreamSnapshot,
  RuntimeAssetDelivery,
  TreeOrgan,
} from "./api";
import { DreamAttentionFollowThroughCard } from "./components/DreamAttentionFollowThroughCard";
import { DreamOpeningAttention } from "./components/DreamOpeningAttention";

interface LifeTreeSceneProps {
  background: RuntimeAssetDelivery;
  snapshot: DreamSnapshot;
  busy: boolean;
  focusedOrganRef: string | null;
  onFocus: (organ: TreeOrgan) => void;
  onOrgan: (organ: TreeOrgan) => void;
  onAnswer: (choiceId: string) => void;
  onReveal: () => void;
  onReconcile: () => void;
  onContinue: () => void;
  onReturnToGrove: () => void;
}

const ORGAN_PRESENTATION: Record<
  string,
  { glyph: string; sceneLabel: string }
> = {
  evidence_leaf_world: { glyph: "叶", sceneLabel: "世事叶" },
  evidence_leaf_structure: { glyph: "叶", sceneLabel: "命纹叶" },
  structure_branch: { glyph: "枝", sceneLabel: "主脉" },
  question_flower: { glyph: "花", sceneLabel: "问题花" },
  outcome_fruit: { glyph: "果", sceneLabel: "回声果" },
};

function organPresentation(organ: TreeOrgan) {
  return (
    ORGAN_PRESENTATION[organ.key] ?? {
      glyph: "观",
      sceneLabel: organ.label,
    }
  );
}

export function LifeTreeScene({
  background,
  snapshot,
  busy,
  focusedOrganRef,
  onFocus,
  onOrgan,
  onAnswer,
  onReveal,
  onReconcile,
  onContinue,
  onReturnToGrove,
}: LifeTreeSceneProps) {
  const visibleOrgans = snapshot.tree.organs.filter((organ) => organ.visible);
  const waiting = snapshot.encounter.status === "WAITING_FOR_WORLD";
  const revealReady = snapshot.encounter.status === "REVEAL_READY";
  const revealed = snapshot.encounter.status === "REVEALED";
  const completed = snapshot.encounter.status === "COMPLETED";
  const narrative = snapshot.projections.dream;
  const flowerName = snapshot.question?.flower_name ?? "问题花";
  const fruitName =
    typeof snapshot.fruit?.fruit_json.name === "string"
      ? snapshot.fruit.fruit_json.name
      : "故事果实";
  const worldTicksRemaining = snapshot.question
    ? Math.max(0, snapshot.question.due_tick - snapshot.world.current_tick)
    : 0;
  const followThroughSupplied =
    snapshot.attention_follow_through !== null &&
    snapshot.attention_follow_through !== undefined;

  return (
    <div
      className="life-tree-experience"
      data-state={snapshot.encounter.status.toLowerCase()}
    >
      <div className="tree-stage" aria-label={`${snapshot.actor.display_name}的生命树`}>
        <img
          className="tree-base"
          data-asset-ref={background.asset_ref}
          src={background.url}
          alt=""
        />
        <div className="tree-paper-wash" aria-hidden="true" />
        <div
          className="tree-resonance"
          data-active={snapshot.question !== null}
          aria-hidden="true"
        />
        {visibleOrgans.map((organ) => {
          const presentation = organPresentation(organ);
          const observed =
            organ.status === "COMPLETED" || organ.status === "SEALED";
          const actionable = organ.status === "AVAILABLE";
          const focused = organ.organ_ref === focusedOrganRef;

          return (
            <button
              className={`tree-organ tree-organ-${organ.key}`}
              data-status={organ.status}
              data-focused={focused}
              data-content-key={`dream.organ.${organ.key}`}
              key={organ.organ_ref}
              type="button"
              disabled={busy}
              onClick={() => {
                onFocus(organ);
                if (actionable) onOrgan(organ);
              }}
              aria-pressed={focused}
              aria-label={`${organ.label}，${
                actionable ? "可观察" : observed ? "已观察，可重新查看" : "可查看"
              }`}
              title={organ.label}
            >
              <span className="organ-ripple" aria-hidden="true" />
              <span className="organ-glyph" aria-hidden="true">
                {presentation.glyph}
              </span>
              <span className="organ-caption" aria-hidden="true">
                {presentation.sceneLabel}
              </span>
            </button>
          );
        })}
        <div className="tree-state-key" aria-hidden="true">
          <span />
          <p>生命树 · {snapshot.tree.projection_version}</p>
        </div>
      </div>

      <section className="question-band" aria-live="polite">
        <DreamAttentionFollowThroughCard
          followThrough={snapshot.attention_follow_through}
          snapshot={snapshot}
        />
        {!snapshot.question && (
          <>
            {!followThroughSupplied && (
              <DreamOpeningAttention attention={snapshot.opening_attention} />
            )}
            <div className="question-copy opening-copy">
              <p className="question-kicker">{snapshot.actor.display_name}的生命现场</p>
              <h1>{narrative.journey_title}</h1>
              <p>{narrative.journey_status}</p>
            </div>
          </>
        )}

        {snapshot.question && !snapshot.human_seal && (
          <>
            <div className="question-copy">
              <p className="question-kicker">{flowerName}</p>
              <h1>{snapshot.question.prompt}</h1>
              <p>已发生的线索对所有选项相同，后来会怎样仍然未知。选择会立即封存。</p>
              <details className="dream-question-basis">
                <summary>为什么这朵花会出现</summary>
                <ul>
                  {snapshot.public_evidence.slice(0, 3).map((evidence) => (
                    <li key={evidence.evidence_ref}>{evidence.summary}</li>
                  ))}
                </ul>
                <small>这些只是所有选项共同看到的既有事实，不暗示后来结果。</small>
              </details>
            </div>
            <div className="answer-options">
              {snapshot.question.options.map((option) => (
                <button
                  key={option.choice_id}
                  type="button"
                  disabled={busy}
                  onClick={() => onAnswer(option.choice_id)}
                >
                  <span>{option.label}</span>
                  <i aria-hidden="true">→</i>
                </button>
              ))}
            </div>
          </>
        )}

        {waiting && (
          <div className="question-copy">
            <p className="question-kicker">{flowerName} · 判断已封存</p>
            <h1>{narrative.journey_title}</h1>
            <p>{narrative.journey_status}</p>
            <p className="world-wait-mark">
              {worldTicksRemaining > 0
                ? `还需经过 ${worldTicksRemaining} 个世界刻，后来发生的事才会写入果实。`
                : "世界证据正在提交，稍后重新进入即可查看果实。"}
            </p>
          </div>
        )}

        {revealReady && (
          <>
            <div className="question-copy">
              <p className="question-kicker">果实已成熟</p>
              <h1>{narrative.journey_title}</h1>
              <p>{narrative.journey_status}</p>
            </div>
            <button
              className="primary-command"
              type="button"
              disabled={busy}
              onClick={onReveal}
            >
              打开{fruitName}
              <span aria-hidden="true">→</span>
            </button>
          </>
        )}

        {(revealed || completed) && snapshot.reveal && (
          <>
            <div className="question-copy reveal-copy">
              <p className="question-kicker">
                {snapshot.reveal.result === "SUPPORTED"
                  ? "判断得到支持"
                  : snapshot.reveal.result === "PARTIAL"
                    ? "判断得到部分支持"
                    : "判断未得到支持"}
              </p>
              <h1>{snapshot.reveal.reveal_json.actual_event}</h1>
              <div className="reveal-evidence">
                {snapshot.reveal.reveal_json.actual_evidence.map((evidence) => (
                  <p key={evidence.evidence_ref}>{evidence.summary}</p>
                ))}
              </div>
            </div>
            {!completed && (
              <button
                className="primary-command"
                type="button"
                disabled={busy}
                onClick={onReconcile}
              >
                收下这次复盘
                <span aria-hidden="true">→</span>
              </button>
            )}
            {completed && (
              <>
                <p className="completion-mark">
                  <span aria-hidden="true">果</span>
                  {fruitName}已进入你的观察记录
                </p>
                {snapshot.continuation.available && snapshot.continuation.label && (
                  <button
                    className="primary-command continuation-command"
                    type="button"
                    disabled={busy}
                    onClick={onContinue}
                  >
                    {snapshot.continuation.label}
                    <span aria-hidden="true">→</span>
                  </button>
                )}
                {snapshot.game.available_commands.includes("RETURN_TO_GROVE") && (
                  <button
                    className="secondary-command grove-return-command"
                    type="button"
                    disabled={busy}
                    onClick={onReturnToGrove}
                  >
                    回到雾林，遇见另一棵树
                    <span aria-hidden="true">→</span>
                  </button>
                )}
              </>
            )}
          </>
        )}
      </section>
    </div>
  );
}
