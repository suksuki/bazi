import type { HomeSnapshot } from "../homeApi";

export function MechanismComparisonCommand({
  busy,
  home,
  onCompare,
}: {
  busy: boolean;
  home: HomeSnapshot;
  onCompare: () => void;
}) {
  const comparison = home.lab.mechanism_comparison;
  if (comparison.decision_ref) {
    return (
      <p className="home-mechanism-decision">
        已形成一次有证据边界的关注排序；它不是有效做功裁决。
      </p>
    );
  }
  const multiple = comparison.candidate_count > 1;
  const ready =
    !multiple || comparison.reasoner_runtime.status === "READY";
  return (
    <div className="home-mechanism-command">
      <button
        disabled={!ready || busy || comparison.candidate_count === 0}
        onClick={onCompare}
        type="button"
      >
        {busy ? "正在比较…" : "比较候选路径"}
      </button>
      <span>
        {multiple && !ready
          ? "LLM 尚未配置，真实模型比较未运行"
          : "只决定下一步关注哪条，不写入命理真相"}
      </span>
    </div>
  );
}
