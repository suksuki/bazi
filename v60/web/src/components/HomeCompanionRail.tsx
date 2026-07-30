import type { HomeSnapshot } from "../homeApi";
import {
  type ExperienceUnit,
  unitSubtitle,
  unitTitle,
} from "../experienceUnits";
import { HomeReadingBrief } from "./HomeReadingBrief";
import { MechanismComparisonCommand } from "./MechanismComparisonCommand";
import { MechanismDecisionTrace } from "./MechanismDecisionTrace";
import { MechanismEvidenceContrast } from "./MechanismEvidenceContrast";
import { MechanismQualificationMatrix } from "./MechanismQualificationMatrix";
import { MingliEvidenceExplanation } from "./MingliEvidenceExplanation";
import { MingliCaseManager } from "./MingliCaseManager";
import { SourceCoordinateReviewPanel } from "./SourceCoordinateReviewPanel";
import { SourceDiscussionAbstentionReceipt } from "./SourceDiscussionAbstentionReceipt";

const PILLAR_LABELS: Record<string, string> = {
  year: "年柱",
  month: "月柱",
  day: "日柱",
  hour: "时柱",
};
const PILLAR_ORDER = ["year", "month", "day", "hour"] as const;
const ELEMENT_LABELS = {
  wood: "木",
  fire: "火",
  earth: "土",
  metal: "金",
  water: "水",
} as const;

export function HomeCompanionRail({
  activeUnit,
  busy,
  home,
  onCompareMechanisms,
  onHomeRefresh,
  onEnterDream,
}: {
  activeUnit: ExperienceUnit;
  busy: boolean;
  home: HomeSnapshot;
  onCompareMechanisms: () => void;
  onHomeRefresh: () => Promise<void>;
  onEnterDream: () => void;
}) {
  return (
    <aside className="companion-rail home-companion-rail" data-perspective={activeUnit}>
      <header className="companion-header home-companion-header">
        <span className="home-unit-seal" aria-hidden="true">
          {activeUnit === "dream"
            ? "界"
            : activeUnit === "mingli"
              ? "命"
              : activeUnit === "abu"
                ? "阿"
                : activeUnit === "theater"
                  ? "故"
                  : "研"}
        </span>
        <span>
          <strong>{unitTitle(activeUnit)}</strong>
          <small>{unitSubtitle(activeUnit)}</small>
        </span>
      </header>

      <div className="companion-content home-unit-content">
        {activeUnit === "dream" && (
          <section>
            <p className="rail-kicker">空间门槛</p>
            <h2>梦境在另一条生命线上继续</h2>
            <p>{home.units.dream.line}</p>
            <button className="rail-primary-command" type="button" onClick={onEnterDream}>
              进入阿布梦境
              <span aria-hidden="true">→</span>
            </button>
          </section>
        )}

        {activeUnit === "mingli" && (
          <section>
            <p className="rail-kicker">正式命盘</p>
            <h2>{home.profile.display_name}的四柱</h2>
            <div className="home-pillar-list">
              {PILLAR_ORDER.map((slot) => (
                <span key={slot}>
                  <small>{PILLAR_LABELS[slot]}</small>
                  <strong>{home.chart.pillars[slot]}</strong>
                </span>
              ))}
            </div>
            <MingliCaseManager home={home} onChanged={onHomeRefresh} />
            <HomeReadingBrief
              brief={home.mingli.reading_brief}
              busy={busy}
              canCompare={
                home.lab.mechanism_comparison.candidate_count > 0 &&
                !home.lab.mechanism_comparison.decision_ref
              }
              comparisonAvailable={
                home.lab.mechanism_comparison.candidate_count <= 1 ||
                home.lab.mechanism_comparison.reasoner_runtime.status ===
                  "READY"
              }
              onCompare={onCompareMechanisms}
            />
            <MechanismDecisionTrace
              comparison={home.lab.mechanism_comparison}
              mode="mingli"
              qualification={home.mingli.mechanism_qualification}
              reading={home.mingli.reading}
            />
            <SourceDiscussionAbstentionReceipt
              mode="summary"
              receipt={home.mingli.source_discussion_receipt}
            />
            <MingliEvidenceExplanation explanation={home.mingli.explanation} />
            <MechanismEvidenceContrast
              depth={home.mingli.mechanism_evidence_depth}
            />
            <SourceCoordinateReviewPanel
              readiness={home.mingli.source_usability_prerequisite}
              vector={home.mingli.source_coordinate_review}
            />
            <MechanismQualificationMatrix
              qualification={home.mingli.mechanism_qualification}
            />
            <details className="home-reading-evidence-details">
              <summary>查看命盘计量、时序与证据明细</summary>
              <QuantFoundationSummary home={home} />
              <TimingEvidenceSummary home={home} />
              <LifeDomainSummary home={home} />
              <p className="home-boundary-note">
                当前读取 {home.mingli.facts.length} 条版本化事实。尚未解决的专业判断不会被补写。
              </p>
            </details>
            <div className="home-abu-reading" data-reading-ref={home.mingli.reading.reading_ref}>
              <span className="home-abu-reading-mark" aria-hidden="true">
                阿
              </span>
              <div>
                <strong>{home.mingli.abu_expression.summary}</strong>
                <p>{home.mingli.abu_expression.boundary}</p>
              </div>
            </div>
          </section>
        )}

        {activeUnit === "abu" && (
          <section>
            <p className="rail-kicker">阿布说</p>
            <h2>继续读刚才那一份命理结果</h2>
            <p>{home.mingli.abu_expression.known}</p>
            <dl className="home-abu-notes">
              <div>
                <dt>现在能说什么？</dt>
                <dd>{home.mingli.abu_expression.boundary}</dd>
              </div>
              <div>
                <dt>接下来关注什么？</dt>
                <dd>{home.mingli.abu_expression.next_attention}</dd>
              </div>
              <div>
                <dt>证据还缺什么？</dt>
                <dd>{home.mingli.abu_expression.evidence_gap_summary}</dd>
              </div>
              <div>
                <dt>是否另起了一次分析？</dt>
                <dd>没有。这里绑定的是命理页正在显示的同一份版本化读取。</dd>
              </div>
            </dl>
            <MechanismDecisionTrace
              comparison={home.lab.mechanism_comparison}
              mode="abu"
              qualification={home.mingli.mechanism_qualification}
              reading={home.mingli.reading}
            />
            <SourceDiscussionAbstentionReceipt
              mode="summary"
              receipt={home.mingli.source_discussion_receipt}
            />
          </section>
        )}

        {activeUnit === "theater" && (
          <section>
            <p className="rail-kicker">你的生命片段</p>
            <h2>小剧场还没有改写你的故事</h2>
            <p>{home.units.theater.line}</p>
            <p className="home-boundary-note">
              V60 只会播放已正式进入你生命线的片段，不用梦境故事冒充你的经历。
            </p>
          </section>
        )}

        {activeUnit === "lab" && (
          <section>
            <p className="rail-kicker">做功候选与证据边界</p>
            <h2>先看真实结构，再比较追查顺序</h2>
            {home.lab.mechanism_candidates.length ? (
              <div className="home-mechanism-stack">
                {home.lab.mechanism_candidates.map((candidate) => {
                  const selected =
                    home.lab.mechanism_comparison.selected_candidate_ref ===
                    candidate.candidate_ref;
                  return (
                    <article
                      className={selected ? "is-selected" : undefined}
                      key={candidate.candidate_ref}
                    >
                      <header>
                        <strong>{candidate.pattern_label}</strong>
                        {selected && <em>当前优先追查</em>}
                      </header>
                      <p>{candidate.structural_statement}</p>
                      <div>
                        {candidate.roles.map((role) => (
                          <span key={role.role_id}>
                            {role.role_id === "SOURCE"
                              ? "起点"
                              : role.role_id === "BRIDGE"
                                ? "承接"
                                : "去向"}
                            <b>{Array.from(new Set(role.occurrence_labels)).join("／")}</b>
                            <small>
                              明 {role.visible_occurrence_count} · 藏{" "}
                              {role.hidden_occurrence_count}
                            </small>
                          </span>
                        ))}
                      </div>
                      <small>
                        {candidate.forbidden_shortcut} 容量、可用性与作用仍待核验。
                      </small>
                    </article>
                  );
                })}
              </div>
            ) : (
              <p>当前真实命盘没有达到本版候选路径的最低结构门槛。</p>
            )}
            <MechanismDecisionTrace
              comparison={home.lab.mechanism_comparison}
              mode="lab"
              qualification={home.mingli.mechanism_qualification}
              reading={home.mingli.reading}
            />
            <SourceDiscussionAbstentionReceipt
              mode="detailed"
              receipt={home.mingli.source_discussion_receipt}
            />
            <MechanismEvidenceContrast
              depth={home.mingli.mechanism_evidence_depth}
              mode="detailed"
            />
            <SourceCoordinateReviewPanel
              mode="detailed"
              readiness={home.mingli.source_usability_prerequisite}
              vector={home.mingli.source_coordinate_review}
            />
            <MechanismQualificationMatrix
              detailed
              qualification={home.mingli.mechanism_qualification}
              selectedCandidateRef={
                home.lab.mechanism_comparison.selected_candidate_ref
              }
            />
            <MechanismComparisonCommand
              busy={busy}
              home={home}
              onCompare={onCompareMechanisms}
            />
            <MingliEvidenceExplanation
              explanation={home.mingli.explanation}
              mode="candidates"
            />
            <div className="home-lab-quant-line">
              <strong>同源量化结构</strong>
              <span>
                {home.mingli.quant_foundation.source_manifestation_evidence.length}
                条根源/显化候选证据，作用均保持待定
              </span>
            </div>
            <TimingLabSummary home={home} />
            <p className="home-boundary-note">
              Lab 与当前命理读取共用同一份事实和规则版本。研究结果只有正式准入新版本后，
              才会影响之后的新读取；当前结果不会被改写。
            </p>
            {home.lab.candidate_paths.length > 0 && (
              <details className="home-relation-context">
                <summary>查看基础关系事实</summary>
                <ul className="home-candidate-list">
                  {home.lab.candidate_paths.map((candidate) => (
                    <li key={candidate.candidate_ref}>
                      <strong>{candidate.label}</strong>
                      <span>关系作用仍待定</span>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </section>
        )}
      </div>

      <footer className="companion-footer">
        <span className="status-seed" aria-hidden="true" />
        <p>当前观察：{home.profile.display_name}的私密生命线</p>
      </footer>
    </aside>
  );
}

function QuantFoundationSummary({ home }: { home: HomeSnapshot }) {
  const vector = home.mingli.quant_foundation;
  const activeTenGods = vector.ten_god_counts.filter(
    (item) => item.visible_count + item.hidden_membership_count > 0,
  );
  const exactEvidence = vector.source_manifestation_evidence.filter(
    (item) => item.source_match_kind === "EXACT_IDENTITY",
  ).length;
  const affinityEvidence =
    vector.source_manifestation_evidence.length - exactEvidence;

  return (
    <div
      className="home-quant-foundation"
      data-vector-ref={vector.vector_ref}
    >
      <header>
        <span>
          <strong>量化结构 V1</strong>
          <small>日主 {vector.day_master_stem}</small>
        </span>
        <em>非旺衰 · 非概率</em>
      </header>
      <div className="home-element-measurements">
        {vector.element_measurements.map((item) => (
          <span key={item.element}>
            <small>{ELEMENT_LABELS[item.element]}</small>
            <i>
              <b
                style={{
                  width:
                    item.total_membership_count === 0
                      ? "0%"
                      : `${Math.max(3, item.total_membership_share * 100)}%`,
                }}
              />
            </i>
            <strong>{item.total_membership_count}</strong>
          </span>
        ))}
      </div>
      <div className="home-quant-meta">
        {vector.polarity_measurements.map((item) => (
          <span key={item.polarity}>
            {item.polarity === "yang" ? "阳" : "阴"} {item.total_membership_count}
          </span>
        ))}
        <span>同干证据 {exactEvidence}</span>
        <span>同五行证据 {affinityEvidence}</span>
      </div>
      <div className="home-ten-god-strip">
        {activeTenGods.map((item) => (
          <span key={item.label}>
            {item.label}
            <small>{item.visible_count + item.hidden_membership_count}</small>
          </span>
        ))}
      </div>
      <p>
        明干与藏干成员分别计数；根、旺衰、容量、可用性和事件结论仍未裁定。
      </p>
    </div>
  );
}

function TimingEvidenceSummary({ home }: { home: HomeSnapshot }) {
  const vector = home.mingli.timing_evidence;
  const layerLabels = {
    DAYUN: "大运",
    ANNUAL: "流年",
    MONTHLY: "流月",
  } as const;
  return (
    <div className="home-timing-evidence" data-vector-ref={vector.vector_ref}>
      <header>
        <span>
          <strong>时序坐标</strong>
          <small>{vector.analysis_date}</small>
        </span>
        <em>作用待定</em>
      </header>
      <div className="home-timing-coordinate-row">
        {vector.coordinates.map((coordinate) => (
          <span key={coordinate.coordinate_ref}>
            <small>{layerLabels[coordinate.layer]}</small>
            <strong>{coordinate.pillar}</strong>
            <b>{coordinate.ten_god_label}</b>
          </span>
        ))}
      </div>
      <p>
        识别到 {vector.relation_evidence.length} 条与原局的成员关系；这里只记录坐标和关系，
        不自动判定激活、吉凶或事件结果。
      </p>
    </div>
  );
}

function TimingLabSummary({ home }: { home: HomeSnapshot }) {
  const overlaps = home.lab.timing_candidate_overlaps;
  const coordinateByRef = new Map(
    home.lab.timing_coordinates.map((item) => [item.coordinate_ref, item]),
  );
  return (
    <div className="home-timing-lab">
      <header>
        <strong>时序 × 候选机制</strong>
        <span>标签交叠，不等于激活</span>
      </header>
      {overlaps.length ? (
        <ul>
          {overlaps.map((overlap) => {
            const coordinate = coordinateByRef.get(overlap.timing_coordinate_ref);
            return (
              <li key={overlap.overlap_ref}>
                <strong>
                  {coordinate?.pillar ?? "时序"} · {overlap.timing_ten_god_label}
                </strong>
                <span>{overlap.matching_role_ids.join("／")} 出现同标签证据</span>
                <em>容量待定 · 作用待定</em>
              </li>
            );
          })}
        </ul>
      ) : (
        <p>本期时序标签没有与当前候选机制形成直接角色交叠。</p>
      )}
    </div>
  );
}

function LifeDomainSummary({ home }: { home: HomeSnapshot }) {
  const signalLabels = {
    TIMING_MECHANISM_OVERLAP: "时序与结构交叠",
    TIMING_AND_MECHANISM_PRESENT: "时序与结构并见",
    TIMING_ONLY: "仅见时序标签",
    MECHANISM_ONLY: "仅见结构候选",
    NO_BOUNDED_EVIDENCE: "暂无合格证据",
  } as const;
  return (
    <div
      className="home-life-domains"
      data-vector-ref={home.mingli.life_domains.vector_ref}
    >
      <header>
        <span>
          <strong>现实观察窗口</strong>
          <small>同一命盘 · 同一时序</small>
        </span>
        <em>不是吉凶结论</em>
      </header>
      <div className="home-life-domain-list">
        {home.mingli.life_domains.observations.map((observation) => (
          <section key={observation.observation_ref}>
            <span>
              <strong>{observation.label}</strong>
              <small>{signalLabels[observation.signal_status]}</small>
            </span>
            <p>{observation.statement}</p>
            <blockquote>{observation.observation_prompt}</blockquote>
          </section>
        ))}
      </div>
    </div>
  );
}
