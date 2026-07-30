import type { DreamReturnEcho } from "../dreamReturnEchoTypes";
import { isDreamReturnEchoDisplayable } from "../dreamReturnEchoTypes";

export function DreamReturnEchoCard({
  echo,
}: {
  echo: DreamReturnEcho | null | undefined;
}) {
  if (!echo) return null;

  if (!isDreamReturnEchoDisplayable(echo)) {
    return (
      <aside
        className="dream-return-echo dream-return-echo-withheld"
        data-return-echo-status="WITHHELD"
        aria-label="归来回响暂不可显示"
      >
        <strong>这次归来暂时留在林中</strong>
        <p>边界凭据不完整，阿布不会补写梦中经历。</p>
      </aside>
    );
  }

  return (
    <aside
      className="dream-return-echo"
      data-return-echo-status="AVAILABLE"
      data-return-echo-ref={echo.echo_ref}
      data-return-echo-hash={echo.echo_hash}
      data-return-echo-version={echo.contract_version}
      data-semantics={echo.semantics}
      data-owner-mingli-evidence-allowed={
        echo.owner_mingli_evidence_allowed
      }
      data-dream-outcome-admitted-as-owner-evidence={
        echo.dream_outcome_admitted_as_owner_evidence
      }
      data-tree-candidate-set-or-order-changed={
        echo.tree_candidate_set_or_order_changed
      }
      data-read-only={echo.read_only}
      data-decision-write-allowed={echo.decision_write_allowed}
      data-knowledge-write-allowed={echo.knowledge_write_allowed}
      data-mingli-write-allowed={echo.mingli_write_allowed}
      data-canonical-write-allowed={echo.canonical_write_allowed}
      aria-label="上一段梦中生命的归来回响"
    >
      <header>
        <span>上一次归来</span>
        <strong>{echo.public_alias}</strong>
        <small>{echo.episode_title}</small>
      </header>

      <div className="dream-return-echo-sections">
        <section data-return-echo-section="judgment">
          <small>当时的判断</small>
          <strong>{echo.judgment.choice_label}</strong>
          <p>{echo.judgment.summary}</p>
        </section>
        <section data-return-echo-section="world-response">
          <small>世界的回应</small>
          <p>{echo.world_response.summary}</p>
          {echo.world_response.evidence_summaries.length > 0 && (
            <ul aria-label="已经抵达的梦中证据">
              {echo.world_response.evidence_summaries.map((summary, index) => (
                <li key={`${index}:${summary}`}>{summary}</li>
              ))}
            </ul>
          )}
        </section>
        <section data-return-echo-section="still-to-observe">
          <small>仍值得观察</small>
          <p>{echo.still_to_observe.summary}</p>
        </section>
      </div>

      <details className="dream-return-echo-recap">
        <summary>听阿布复盘这一次</summary>
        <dl>
          <div data-abu-recap-question="meaning">
            <dt>它说明了什么</dt>
            <dd>{echo.abu_recap.meaning}</dd>
          </div>
          <div data-abu-recap-question="boundary">
            <dt>它还不能说明什么</dt>
            <dd>{echo.abu_recap.boundary}</dd>
          </div>
          <div data-abu-recap-question="next">
            <dt>接下来该看什么</dt>
            <dd>{echo.abu_recap.next_attention}</dd>
          </div>
        </dl>
      </details>

      <p className="dream-return-echo-boundary">
        这张足迹只属于这条梦中生命；不得作为主人的命理证据，不改写命盘，也不改变三棵树的候选或顺序。
      </p>
    </aside>
  );
}
