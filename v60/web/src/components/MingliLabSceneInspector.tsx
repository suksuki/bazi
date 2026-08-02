import type { MingliReadingClaimGraph } from "../mingliClaimGraphTypes";
import type { MingliStageProjection } from "../mingliStageTypes";
import { visibleClaimAssessmentCodes } from "./MingliClaimPresentation";

export function MingliLabSceneInspector({
  claimGraph,
  onAskGuide,
  onSelectRelation,
  selectedRelationRef,
  stage,
}: {
  claimGraph: MingliReadingClaimGraph | null;
  onAskGuide: () => void;
  onSelectRelation: (relationRef: string | null) => void;
  selectedRelationRef: string | null;
  stage: MingliStageProjection;
}) {
  const selected =
    stage.relations.find(
      (relation) => relation.relation_ref === selectedRelationRef,
    ) ?? null;
  const wholeChart = claimGraph?.claims.find(
    (claim) => claim.semantic_key === "WHOLE_CHART",
  );
  const primary = claimGraph?.claims.find((claim) => claim.role === "PRIMARY");
  const alternative = claimGraph?.claims.find((claim) => claim.role === "ALTERNATIVE");
  const workPath = claimGraph?.claims.find(
    (claim) => claim.semantic_key === "WORK_PATH",
  );
  const question = claimGraph?.claims.find(
    (claim) => claim.semantic_key === "DISCRIMINATING_QUESTION",
  );

  return (
    <aside className="mingli-lab-inspector" aria-label="命理 Lab 舞台观察">
      <header>
        <p>Lab · 展开同一次整盘初断</p>
        <h2>{wholeChart?.status === "WITHHELD"
          ? "整盘总纲本条未采纳"
          : wholeChart?.headline ?? "整盘判断尚未生成"}</h2>
        <span>
          {wholeChart?.status === "WITHHELD"
            ? "整盘 Reading 仍然成立；这里只撤下存在局部越界的具体表述。"
            : wholeChart?.statement
            ?? "生成初断后，这里会展开主解释、竞争解释及每条判断引用的证据。"}
        </span>
        {wholeChart && <ClaimAssessment item={wholeChart} />}
      </header>
      {claimGraph && primary && workPath && (
        <section
          className="mingli-lab-claim-graph"
          data-claim-graph-ref={claimGraph.graph_ref}
        >
          <article data-claim-status={primary.status}>
            <small>当前主解释</small>
            <strong>{primary.headline}</strong>
            <p>{primary.statement}</p>
            <span>{primary.evidence_ids.join(" · ")}</span>
            {primary.mechanism_evidence_ids.length > 0 && (
              <small>机制候选证据：{primary.mechanism_evidence_ids.join(" · ")}</small>
            )}
            <ClaimAssessment item={primary} />
          </article>
          {alternative && (
            <article data-claim-status={alternative.status}>
              <small>竞争解释</small>
              <strong>{alternative.headline}</strong>
              <p>{alternative.statement}</p>
              <span>{alternative.evidence_ids.join(" · ")}</span>
              {alternative.mechanism_evidence_ids.length > 0 && (
                <small>机制候选证据：{alternative.mechanism_evidence_ids.join(" · ")}</small>
              )}
              <ClaimAssessment item={alternative} />
            </article>
          )}
          <article data-claim-status={workPath.status}>
            <small>主路径</small>
            <strong>{workPath.statement}</strong>
            <p>{workPath.condition}</p>
            <ClaimAssessment item={workPath} />
          </article>
          {question && <p>校准问题：{question.statement}</p>}
        </section>
      )}
      <h3 className="mingli-lab-section-title">舞台关系坐标</h3>
      <div className="mingli-lab-relation-list" role="list" aria-label="已准入关系成员">
        {stage.relations.length ? (
          stage.relations.map((relation) => (
            <button
              aria-pressed={selectedRelationRef === relation.relation_ref}
              data-relation-ref={relation.relation_ref}
              key={relation.relation_ref}
              onClick={() =>
                onSelectRelation(
                  selectedRelationRef === relation.relation_ref
                    ? null
                    : relation.relation_ref,
                )
              }
              type="button"
            >
              <strong>{relation.left_branch}—{relation.right_branch}</strong>
              <span>{relation.label}</span>
              <small>成员关系成立 · 作用待定</small>
            </button>
          ))
        ) : (
          <p>当前柱位没有命中已准入的六冲／六合成员关系。</p>
        )}
      </div>
      {selected && (
        <dl className="mingli-lab-evidence" data-selected-relation-ref={selected.relation_ref}>
          <div>
            <dt>来源柱位</dt>
            <dd>{selected.left_column_ref} ↔ {selected.right_column_ref}</dd>
          </div>
          <div>
            <dt>规则正本</dt>
            <dd>{selected.rule_ref}</dd>
          </div>
          <div>
            <dt>证据引用</dt>
            <dd>{selected.evidence_refs.join(" · ")}</dd>
          </div>
          <div>
            <dt>当前边界</dt>
            <dd>这里只确认两支在当前舞台相遇；实际作用仍需放回整盘主线判断。</dd>
          </div>
        </dl>
      )}
      <button className="mingli-lab-ask-guide" onClick={onAskGuide} type="button">
        请角色按当前舞台讲解
        <span aria-hidden="true">声画同步 →</span>
      </button>
    </aside>
  );
}

function ClaimAssessment({
  item,
}: {
  item: MingliReadingClaimGraph["claims"][number];
}) {
  if (item.assessment_codes.length === 0) return null;
  const visibleCodes = visibleClaimAssessmentCodes(item);
  const labels = visibleCodes.map((code) => (
    code === "PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE"
      ? "主解释已保留，整盘命据仍需补齐"
    : code === "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION"
      ? "这仍是机制候选，尚未完成逐项专业裁决"
    : code === "CONFIDENCE_EXCEEDS_PACKET"
      ? "模型置信度超出卷宗，投射已降为中等置信"
    : code === "DEPENDENCY_WITHHELD"
      ? "总纲的一条局部支撑路径已经撤下"
    : code === "TIMING_COORDINATE_EVIDENCE_MISSING"
      ? "岁运判断缺少对应时间坐标证据"
    : code === "TIMING_RELATION_EVIDENCE_MISSING"
      ? "岁运文字点名关系但未绑定关系证据"
    : code === "RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT"
      ? "关系成员被直接升级为确定作用"
      : code === "WORK_PATH_CLOSURE_EXCEEDS_PACKET"
        ? "有条件的做功路径被写成已经闭合"
        : code === "HIGH_RISK_EVENT_ASSERTION"
          ? "命盘被直接扩写为高风险现实事件"
        : code === "ROOT_ASSERTION_CONFLICTS_WITH_PACKET"
          ? "文本虚构了地支根位"
        : code === "NAMED_COORDINATE_CONFLICTS_WITH_PACKET"
          ? "文本中的藏干坐标与命盘不符"
        : code === "UNLISTED_RELATION_COORDINATE_ASSERTION"
          ? "文本使用了卷宗未列出的地支关系"
        : code === "UNADMITTED_CLASSICAL_ASSERTION"
          ? "文本使用了尚未完成专业判定的传统标签"
      : "岁运信息反写进原局判断"
  ));
  return <em>{item.status === "WITHHELD" ? "本条未采纳" : "本条待校准"}：{[...new Set(labels)].join("；")}</em>;
}
