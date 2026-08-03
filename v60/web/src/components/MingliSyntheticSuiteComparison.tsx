import type { MingliSyntheticSuiteRunComparison } from "../mingliSyntheticSuiteSelection";
import type {
  MingliSyntheticSuiteCandidateIdentity,
  MingliSyntheticSuiteRunSelection,
} from "../mingliSyntheticSuiteTypes";

export function MingliSyntheticSuiteTrainingComparison({
  comparison,
  currentCandidate,
  onSelectRun,
}: {
  comparison: MingliSyntheticSuiteRunComparison | null;
  currentCandidate: MingliSyntheticSuiteCandidateIdentity | null;
  onSelectRun: (selection: MingliSyntheticSuiteRunSelection) => void;
}) {
  return (
    <>
      {currentCandidate && (
        <CandidateIdentity candidate={currentCandidate} label="本轮候选" />
      )}
      {comparison && (
        <div
          className="mingli-synthetic-suite-comparison"
          data-comparable={comparison.status === "COMPARABLE"}
        >
          <header>
            <div>
              <small>紧邻训练对照</small>
              <strong>
                {comparison.status === "COMPARABLE"
                  ? "同一把评尺"
                  : "评尺不同，不计算进步"}
              </strong>
            </div>
            <button onClick={() => onSelectRun(comparison.previous)} type="button">
              查看上轮
            </button>
          </header>
          {comparison.status === "COMPARABLE" ? (
            <ComparableMetrics comparison={comparison} />
          ) : (
            <p>{comparison.reason}</p>
          )}
          {comparison.previous.run.candidate_identity && currentCandidate && (
            <CandidateDelta
              current={currentCandidate}
              previous={comparison.previous.run.candidate_identity}
            />
          )}
        </div>
      )}
    </>
  );
}

function ComparableMetrics({
  comparison,
}: {
  comparison: MingliSyntheticSuiteRunComparison;
}) {
  return (
    <>
      <div className="mingli-synthetic-suite-metrics">
        <span>
          <small>模型独立</small>
          <strong>
            {comparison.previousMetrics.modelIndependent}/{comparison.previousMetrics.total}
            <i aria-hidden="true">→</i>
            {comparison.currentMetrics.modelIndependent}/{comparison.currentMetrics.total}
          </strong>
        </span>
        <span>
          <small>需校正课题</small>
          <strong>
            {comparison.previousMetrics.reviewRequired}
            <i aria-hidden="true">→</i>
            {comparison.currentMetrics.reviewRequired}
          </strong>
        </span>
      </div>
      <div className="mingli-synthetic-suite-deltas" aria-label="错误变化">
        <small>真正发生变化的错误</small>
        {comparison.clusterChanges.length ? (
          <div>
            {comparison.clusterChanges.map((change) => (
              <span key={change.key} data-improved={change.current < change.previous}>
                {change.label} {change.previous} → {change.current}
              </span>
            ))}
          </div>
        ) : (
          <p>错误簇数量没有变化。</p>
        )}
      </div>
    </>
  );
}

function CandidateIdentity({
  candidate,
  label,
}: {
  candidate: MingliSyntheticSuiteCandidateIdentity;
  label: string;
}) {
  return (
    <div className="mingli-synthetic-suite-candidate">
      <small>{label}</small>
      <span title={`${candidate.provider_id} / ${candidate.model_ref} / ${candidate.model_digest}`}>
        {candidate.provider_id} · {candidate.model_ref} · {shortHash(candidate.model_digest)}
      </span>
      <span title={`${candidate.agent_profile_ref} / ${candidate.agent_profile_hash}`}>
        Profile {shortRef(candidate.agent_profile_ref)} · {shortHash(candidate.agent_profile_hash)}
      </span>
      <span title={`${candidate.provider_profile_ref} / ${candidate.provider_profile_hash}`}>
        Provider {shortRef(candidate.provider_profile_ref)} · {shortHash(candidate.provider_profile_hash)}
      </span>
      <span title={`${candidate.prompt_ref} / ${candidate.prompt_hash}`}>
        Prompt {shortRef(candidate.prompt_ref)} · {shortHash(candidate.prompt_hash)}
      </span>
      {candidate.agent_reading_version && (
        <span>Reading {shortRef(candidate.agent_reading_version)}</span>
      )}
    </div>
  );
}

function CandidateDelta({
  current,
  previous,
}: {
  current: MingliSyntheticSuiteCandidateIdentity;
  previous: MingliSyntheticSuiteCandidateIdentity;
}) {
  const changes = candidateChanges(previous, current);
  return (
    <div className="mingli-synthetic-suite-candidate-delta">
      <small>候选变化</small>
      {changes.length ? changes.map((change) => (
        <span key={change.label} title={`${change.previous} → ${change.current}`}>
          {change.label} {compactIdentity(change.previous)} → {compactIdentity(change.current)}
        </span>
      )) : <span>候选身份未变化</span>}
    </div>
  );
}

function candidateChanges(
  previous: MingliSyntheticSuiteCandidateIdentity,
  current: MingliSyntheticSuiteCandidateIdentity,
) {
  const entries = [
    {
      label: "Model",
      previous: `${previous.provider_id}/${previous.model_ref}/${previous.model_digest}`,
      current: `${current.provider_id}/${current.model_ref}/${current.model_digest}`,
    },
    {
      label: "Profile",
      previous: `${previous.agent_profile_ref}/${previous.agent_profile_hash}`,
      current: `${current.agent_profile_ref}/${current.agent_profile_hash}`,
    },
    {
      label: "Provider",
      previous: `${previous.provider_profile_ref}/${previous.provider_profile_hash}`,
      current: `${current.provider_profile_ref}/${current.provider_profile_hash}`,
    },
    {
      label: "Prompt",
      previous: `${previous.prompt_ref}/${previous.prompt_hash}`,
      current: `${current.prompt_ref}/${current.prompt_hash}`,
    },
    {
      label: "Reading",
      previous: previous.agent_reading_version ?? "legacy",
      current: current.agent_reading_version ?? "legacy",
    },
  ];
  return entries.filter((entry) => entry.previous !== entry.current);
}

function compactIdentity(value: string): string {
  return value
    .split("/")
    .map((part) => part.length === 64 ? shortHash(part) : shortRef(part))
    .join("/");
}

function shortHash(value: string): string {
  return value.slice(0, 8);
}

function shortRef(value: string): string {
  if (!value.includes(".")) return value;
  const parts = value.split(".");
  return `.${parts[parts.length - 1] ?? value}`;
}
