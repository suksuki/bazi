import { useEffect, useState } from "react";

import type { DreamSnapshot } from "../api";
import type { SemanticFocus } from "../semanticFocus";

type AbuQuestion = "meaning" | "boundary" | "next";

const QUESTIONS: ReadonlyArray<{ id: AbuQuestion; label: string }> = [
  { id: "meaning", label: "它说明了什么" },
  { id: "boundary", label: "它还不能说明什么" },
  { id: "next", label: "接下来该看什么" },
];

export function AbuSaysUnit({
  focus,
  snapshot,
}: {
  focus: SemanticFocus | null;
  snapshot: DreamSnapshot;
}) {
  const [question, setQuestion] = useState<AbuQuestion>("meaning");

  useEffect(() => {
    setQuestion("meaning");
  }, [focus?.organ.organ_ref]);

  return (
    <>
      <p className="rail-kicker">阿布正在听</p>
      <blockquote>{snapshot.projections.abu.line}</blockquote>
      {focus ? (
        <section className="abu-focus-dialogue" aria-label="围绕当前生命线理解">
          <div className="abu-question-set">
            {QUESTIONS.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={question === item.id}
                onClick={() => setQuestion(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="quiet-note" aria-live="polite">
            <span aria-hidden="true">阿</span>
            <p>{answerForFocus(focus, question)}</p>
          </div>
        </section>
      ) : (
        <div className="quiet-note">
          <span aria-hidden="true">阿</span>
          <p>生命树还没有把某一处递到我们面前，我先陪你看完整棵树。</p>
        </div>
      )}
      <p className="unit-boundary">
        阿布可以解释和陪伴，但不会创建命盘事实、世界结果或替你封存答案。
      </p>
    </>
  );
}

function answerForFocus(
  focus: SemanticFocus,
  question: AbuQuestion,
): string {
  if (question === "meaning") {
    if (focus.organ.role === "OUTCOME_FRUIT" && focus.evidence.length > 0) {
      return `后来留下了两类可核验事实：${focus.evidence
        .map((item) => item.summary)
        .join("；")}`;
    }
    if (focus.evidence[0]) return focus.evidence[0].summary;
    if (focus.labFacts.length > 0) {
      return "这处对应已经提交的命盘结构事实，可以作为观察依据。";
    }
    if (focus.questionLinked) {
      return "这是当前需要独立判断的命题；你的选择会被封存，但不会决定世界结果。";
    }
    return "这处只承载当前已经公开的生命线材料。";
  }

  if (question === "boundary") {
    if (focus.organ.role === "OUTCOME_FRUIT") {
      return "这枚果实只核对本次事件，不能反过来把某条命盘关系自动升级成有效做功。";
    }
    if (focus.organ.role === "STRUCTURE_BRANCH" || focus.labFacts.length > 0) {
      return "结构关系存在，不等于作用、承载、时机和人生结果都已经成立。";
    }
    if (focus.organ.role === "QUESTION_FLOWER") {
      return "封存前的共同线索不能替任何候选答案提前加分。";
    }
    return "一条已经发生的经历不是命盘结论，也不能单独决定后来会发生什么。";
  }

  if (focus.organ.role === "OUTCOME_FRUIT") {
    return "把果实里的新事实放进小剧场核对，再去 Lab 看哪些结构仍然只是候选。";
  }
  if (focus.organ.role === "STRUCTURE_BRANCH") {
    return "先在命理测算里确认结构事实，再到 Lab 查看它尚未解决的条件。";
  }
  if (focus.organ.role === "QUESTION_FLOWER") {
    return "回到梦境独立留下判断，然后让世界时间给出后续证据。";
  }
  return "继续比较另一片叶与主脉，看看它们是否真的指向同一个待观察事件。";
}
