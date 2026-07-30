import type { HomeSnapshot } from "../homeApi";
import { RelationEffectAdmissionReview } from "./RelationEffectAdmissionReview";
import { RelationEffectEvidencePacket } from "./RelationEffectEvidencePacket";
import { RelationEffectResearchFrontier } from "./RelationEffectResearchFrontier";

export function RelationEffectReviewStack({
  home,
  mode,
}: {
  home: HomeSnapshot;
  mode: "summary" | "detailed";
}) {
  return (
    <>
      <RelationEffectResearchFrontier
        frontier={home.mingli.relation_effect_frontier}
        mode={mode}
      />
      <RelationEffectAdmissionReview home={home} mode={mode} />
      <RelationEffectEvidencePacket home={home} mode={mode} />
    </>
  );
}
