import type { DreamGroveChapterRoute } from "../dreamChapterRouteTypes";

export function DreamGroveChapterRouteSummary({
  route,
}: {
  route: DreamGroveChapterRoute | null;
}) {
  if (route === null) {
    return (
      <span
        className="dream-grove-chapter-route dream-grove-chapter-route-withheld"
        data-chapter-route-status="WITHHELD"
        aria-label="章节路线暂不可进入"
      >
        <small>章节路线暂不可用</small>
        <strong>这棵树先留在雾里</strong>
        <em>路线凭据没有完整对上，阿布不会用旧篇章替代。</em>
      </span>
    );
  }

  const complete = route.status === "STORY_CURRENTLY_COMPLETE";
  return (
    <span
      className={`dream-grove-chapter-route${
        complete ? " dream-grove-chapter-route-complete" : ""
      }`}
      data-chapter-route-status={route.status}
      data-chapter-route-version={route.contract_version}
      data-route-hash={route.route_hash}
      data-route-basis={route.basis}
      data-route-candidate-ref={route.candidate_ref}
      data-route-candidate-hash={route.candidate_hash}
      data-route-tree-ref={route.tree_ref}
      data-previous-source-question-ref={
        route.previous_source_question_ref ?? undefined
      }
      data-previous-source-episode-ref={
        route.previous_source_episode_ref ?? undefined
      }
      data-target-source-question-ref={route.target_source_question_ref}
      data-target-source-episode-ref={route.target_source_episode_ref}
      data-target-source-episode-version={
        route.target_source_episode_version
      }
      data-target-chapter={route.target_chapter}
      data-transition-ref={route.transition_ref ?? undefined}
      data-transition-hash={route.transition_hash ?? undefined}
      data-routing-authority={route.routing_authority}
      data-attention-routing-allowed={route.attention_routing_allowed}
      data-attention-ref-used={route.attention_ref_used}
      data-tree-candidate-set-or-order-changed={
        route.tree_candidate_set_or_order_changed
      }
      data-question-changed={route.question_changed}
      data-answer-changed={route.answer_changed}
      data-npc-choice-changed={route.npc_choice_changed}
      data-outcome-changed={route.outcome_changed}
      data-read-only={route.read_only}
      aria-label={
        complete
          ? `${route.title}，${route.chapter_label}`
          : `${route.chapter_label}，${route.title}`
      }
    >
      <small>{route.chapter_label}</small>
      <strong>{route.title}</strong>
      <span>{route.premise}</span>
      {complete && <em>暂时没有下一章可进入</em>}
    </span>
  );
}
