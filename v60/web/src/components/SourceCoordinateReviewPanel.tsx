import type {
  HomeSourceCoordinateReview,
  HomeSourceCoordinateReviewVector,
} from "../homeSourceReviewTypes";

const SLOT_LABELS = {
  year: "年柱",
  month: "月柱",
  day: "日柱",
  hour: "时柱",
} as const;

export function SourceCoordinateReviewPanel({
  mode = "summary",
  vector,
}: {
  mode?: "summary" | "detailed";
  vector: HomeSourceCoordinateReviewVector;
}) {
  const needsReview = vector.reviews.filter(
    (item) => item.relation_intersections.length > 0,
  );
  return (
    <section
      className="source-coordinate-review"
      data-mode={mode}
      data-review-required={vector.review_required_count}
      data-vector-ref={vector.vector_ref}
    >
      <header>
        <span>
          <small>新准入证据层</small>
          <strong>来源坐标复核</strong>
        </span>
        <em>不判旺衰</em>
      </header>
      <div className="source-review-summary">
        <span>
          <b>{vector.source_evidence_count}</b>
          来源候选
        </span>
        <span>
          <b>{vector.clear_coordinate_count}</b>
          未见关系命中
        </span>
        <span className={vector.review_required_count ? "needs-review" : undefined}>
          <b>{vector.review_required_count}</b>
          需要复核
        </span>
      </div>
      <p className="source-review-reading">
        {vector.review_required_count
          ? `其中 ${vector.review_required_count} 个来源坐标同时被已确认的六冲或六合关系命中，必须先核验关系作用，不能直接写成“根可用”。`
          : "本盘这些来源坐标暂未被已准入的六冲、六合关系命中；这只减少一类反证，不等于已经判定有根或可用。"}
      </p>
      {mode === "detailed" && (
        <SourceReviewDetails
          needsReview={needsReview}
          reviews={vector.reviews}
        />
      )}
      <footer>
        <span>六冲命中 {vector.six_clash_intersection_count}</span>
        <span>六合命中 {vector.six_harmony_intersection_count}</span>
        <span>关系作用仍待定</span>
      </footer>
    </section>
  );
}

function SourceReviewDetails({
  needsReview,
  reviews,
}: {
  needsReview: HomeSourceCoordinateReview[];
  reviews: HomeSourceCoordinateReview[];
}) {
  const visible = needsReview.length ? needsReview : reviews.slice(0, 4);
  if (!visible.length) {
    return <p className="source-review-empty">当前命盘没有跨层来源候选。</p>;
  }
  return (
    <div className="source-review-detail-list">
      {visible.map((item) => (
        <article key={item.review_ref}>
          <div>
            <strong>
              {SLOT_LABELS[item.visible_slot]} {item.visible_stem}
            </strong>
            <span aria-hidden="true">←</span>
            <strong>
              {SLOT_LABELS[item.source_slot]} {item.source_branch}藏
              {item.hidden_stem}
            </strong>
          </div>
          <small>
            {item.source_match_kind === "EXACT_IDENTITY"
              ? "同干跨层"
              : "同五行、不同干"}
          </small>
          {item.relation_intersections.length ? (
            <ul>
              {item.relation_intersections.map((relation) => (
                <li key={relation.intersection_ref}>
                  <b>
                    {relation.relation_type === "six_clash_membership"
                      ? "六冲复核"
                      : "六合复核"}
                  </b>
                  <span>
                    {SLOT_LABELS[relation.source_slot]} {relation.source_branch}
                    {" · "}
                    {SLOT_LABELS[relation.peer_slot]} {relation.peer_branch}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p>本版未见已准入关系命中，作用仍不推断。</p>
          )}
        </article>
      ))}
    </div>
  );
}
