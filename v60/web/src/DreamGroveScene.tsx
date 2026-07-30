import type { CSSProperties } from "react";

import { AbuCompanionMotion } from "./AbuCompanionMotion";
import type {
  DreamGrove,
  DreamGroveCandidate,
  RuntimeAssetDelivery,
  RuntimeMediaManifest,
} from "./api";
import { DreamReadingObservationLens } from "./components/DreamReadingObservationLens";
import { DreamPendingAttentionBadge } from "./components/DreamPendingAttentionBadge";
import { DreamReturnEchoCard } from "./components/DreamReturnEchoCard";
import {
  isDreamPendingAttentionDisplayable,
  isDreamPendingAttentionSupplied,
} from "./dreamAttentionFollowThroughTypes";
import { isDreamReturnEchoDisplayable } from "./dreamReturnEchoTypes";
import type { DreamReadingObservationLensModel } from "./homeDreamObservationLens";

const DOMAIN_LABELS = {
  career: "职责与位置",
  wealth: "交换与回流",
  relationship: "协作与边界",
} as const;

function treeStyle(candidate: DreamGroveCandidate): CSSProperties {
  const phenotype = candidate.tree.phenotype;
  const ratios = phenotype.element_membership_ratios;
  const warm = (ratios.fire ?? 0) + (ratios.earth ?? 0) * 0.45;
  const cool = (ratios.water ?? 0) + (ratios.metal ?? 0) * 0.35;
  const green = ratios.wood ?? 0;
  return {
    "--grove-crown-x": phenotype.crown_spread,
    "--grove-crown-y": 0.88 + (phenotype.branch_lift - 0.84) * 0.8,
    "--grove-root-x": phenotype.root_spread,
    "--grove-bark": phenotype.bark_definition,
    "--grove-moisture": phenotype.surface_moisture,
    "--grove-hue": `${Math.round(72 + green * 22 - warm * 28 + cool * 18)}deg`,
    "--grove-saturation": 0.66 + green * 0.38,
    "--grove-lightness": 0.8 + cool * 0.16,
  } as CSSProperties;
}

function PhenotypeTree({ candidate }: { candidate: DreamGroveCandidate }) {
  return (
    <svg
      className="grove-tree-art"
      viewBox="0 0 260 420"
      aria-hidden="true"
      focusable="false"
    >
      <g className="grove-tree-roots">
        <path d="M130 360 C107 372 80 383 48 391 C81 388 109 388 132 377" />
        <path d="M133 363 C160 374 188 384 220 390 C188 389 160 387 133 378" />
        <path d="M126 366 C116 385 108 398 94 410 C113 398 126 390 139 373" />
      </g>
      <path
        className="grove-tree-trunk"
        d="M111 369 C116 314 114 266 101 218 C112 205 121 186 123 157 C131 180 137 203 145 221 C146 184 154 151 168 124 C162 172 162 214 149 253 C145 293 145 333 153 368 Z"
      />
      <g className="grove-tree-branches">
        <path d="M123 254 C96 229 75 205 54 170" />
        <path d="M134 230 C151 205 175 184 205 163" />
        <path d="M125 194 C104 167 94 140 87 112" />
        <path d="M142 185 C155 150 172 120 194 94" />
      </g>
      <g className="grove-tree-crown">
        <ellipse cx="61" cy="157" rx="54" ry="52" />
        <ellipse cx="92" cy="108" rx="64" ry="61" />
        <ellipse cx="147" cy="86" rx="69" ry="68" />
        <ellipse cx="199" cy="139" rx="57" ry="56" />
        <ellipse cx="154" cy="153" rx="73" ry="62" />
      </g>
      <g className="grove-tree-highlights">
        <ellipse cx="114" cy="62" rx="34" ry="22" />
        <ellipse cx="51" cy="132" rx="24" ry="18" />
        <ellipse cx="187" cy="119" rx="28" ry="19" />
      </g>
    </svg>
  );
}

export function DreamGroveScene({
  background,
  busy,
  grove,
  lens,
  media,
  onSelect,
  onSelectAttention,
}: {
  background: RuntimeAssetDelivery;
  busy: boolean;
  grove: DreamGrove;
  lens: DreamReadingObservationLensModel;
  media: RuntimeMediaManifest;
  onSelect: (candidateRef: string) => void;
  onSelectAttention: (observationRef: string) => void;
}) {
  const returnEcho = grove.return_echo ?? null;
  const returnEchoDisplayable = isDreamReturnEchoDisplayable(returnEcho);
  const candidateRefs = grove.candidates.map(({ candidate_ref }) => candidate_ref);
  const pendingSupplied = isDreamPendingAttentionSupplied(
    grove.pending_attention,
  );
  const pending = isDreamPendingAttentionDisplayable(
    grove.pending_attention,
    { candidateRefs },
  )
    ? grove.pending_attention
    : null;

  return (
    <div
      className="dream-grove-scene"
      data-return-echo={returnEchoDisplayable}
    >
      <img
        className="dream-grove-background"
        data-asset-ref={background.asset_ref}
        src={background.url}
        alt=""
      />
      <div className="dream-grove-mist" aria-hidden="true" />
      <div className="dream-grove-title">
        <p>阿布梦境</p>
        <h1>三段人生正在林中继续</h1>
        <span>选择一棵树，先看已经发生的事，再留下你的判断。</span>
      </div>
      <DreamReadingObservationLens lens={lens} />
      <div
        className="dream-grove-trees"
        role="group"
        aria-label="选择一棵陌生生命树"
      >
        {grove.candidates.map((candidate) => (
          <button
            className="grove-tree-choice"
            data-candidate-ref={candidate.candidate_ref}
            data-domain={candidate.domain}
            data-pending-attention={
              pending?.source_candidate_ref === candidate.candidate_ref
            }
            data-tree-version={candidate.tree.version}
            disabled={busy}
            key={candidate.candidate_ref}
            onClick={() => onSelect(candidate.candidate_ref)}
            style={treeStyle(candidate)}
            type="button"
          >
            <DreamPendingAttentionBadge
              candidateRef={candidate.candidate_ref}
              pending={pending}
            />
            <PhenotypeTree candidate={candidate} />
            <span className="grove-tree-copy">
              <strong>{candidate.public_alias}</strong>
              <small>{DOMAIN_LABELS[candidate.domain]}</small>
              <em>{candidate.premise}</em>
            </span>
          </button>
        ))}
      </div>
      <DreamReturnEchoCard
        attention={pendingSupplied ? null : grove.next_attention}
        busy={busy}
        echo={returnEcho}
        followThrough={grove.attention_follow_through}
        candidateRefs={candidateRefs}
        onSelectAttention={onSelectAttention}
      />
      <AbuCompanionMotion
        className="dream-grove-abu"
        cueKey={`dream-grove:${grove.grove_version}`}
        guideLeft={false}
        guideLeftCue={media.cues.abu_guide_left}
        idleCue={media.cues.abu_idle}
        label="阿布安静坐在三棵生命树前"
      />
      <p className="dream-grove-abu-line">“我不替你选。先看哪一段人生让你停下来。”</p>
    </div>
  );
}
