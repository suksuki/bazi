import type { ExperienceUnit } from "../experienceUnits";
import type { SemanticFocus } from "../semanticFocus";

export function SemanticFocusThread({
  focus,
  unit,
}: {
  focus: SemanticFocus;
  unit: ExperienceUnit;
}) {
  const summaries: Record<ExperienceUnit, string> = {
    dream:
      focus.organ.role === "STRUCTURE_BRANCH"
        ? "这段枝路把现实线索与结构事实放在一起，但不会替你决定结果。"
        : focus.organ.role === "QUESTION_FLOWER"
          ? "这朵花承载当前命题；你的判断会封存，世界结果独立发生。"
          : focus.organ.role === "OUTCOME_FRUIT"
            ? "这枚果实只呈现已经提交的世界结果与复盘。"
            : "这片叶只承载已经公开的材料，观察它不会创建新事实。",
    mingli: focus.labFacts.length
      ? `这处焦点引用 ${focus.labFacts.length} 条正式命盘事实。`
      : "这处焦点来自世界经历，不会被伪装成命盘事实。",
    abu: focus.fruitLinked
      ? "阿布只围绕已经公开的后续事实解释这枚果实，不替结果补写意义。"
      : focus.evidence[0]?.summary
        ?? (focus.labFacts.length
          ? "这是一条已经提交的结构事实；它的作用与人生结果仍然未知。"
          : "阿布只解释已经公开的部分，不替系统补充结论。"),
    theater:
      focus.theaterEvidence[0]?.summary
      ?? "这个焦点目前没有独立的正史镜头，不会为了好看而补演一段。",
    lab: focus.labFacts.length
      ? `这个焦点连接 ${focus.labFacts.length} 条正式结构事实；作用与容量仍待定。`
      : "这是现实事件或故事状态，不会被 Lab 伪装成命盘事实。",
  };

  return (
    <section
      className="semantic-focus"
      data-content-key={focus.contentKey}
      data-focus-role={focus.organ.role}
    >
      <p className="rail-kicker">此刻正在看</p>
      <h2>{focus.organ.label}</h2>
      <p>{summaries[unit]}</p>
      <div className="focus-provenance" aria-label="关联材料">
        {focus.evidence.length > 0 && <span>现实证据 · {focus.evidence.length}</span>}
        {focus.labFacts.length > 0 && <span>命盘事实 · {focus.labFacts.length}</span>}
        {focus.theaterEvidence.length > 0 && <span>正史片段</span>}
        {focus.questionLinked && <span>封存命题</span>}
        {focus.fruitLinked && <span>世界结果</span>}
      </div>
    </section>
  );
}
