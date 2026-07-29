import type { CSSProperties } from "react";

import { AbuCompanionMotion } from "../AbuCompanionMotion";
import type {
  RuntimeAssetDelivery,
  RuntimeMediaManifest,
} from "../api";
import type { HomeSnapshot } from "../homeApi";

const ELEMENTS = [
  ["wood", "木"],
  ["fire", "火"],
  ["earth", "土"],
  ["metal", "金"],
  ["water", "水"],
] as const;
const PILLAR_ORDER = ["year", "month", "day", "hour"] as const;

export function HomeLifeTreeScene({
  background,
  busy,
  home,
  media,
  onEnterDream,
}: {
  background: RuntimeAssetDelivery;
  busy: boolean;
  home: HomeSnapshot;
  media: RuntimeMediaManifest;
  onEnterDream: () => void;
}) {
  const phenotype = home.tree.phenotype;
  const style = {
    "--home-crown": phenotype.crown_spread,
    "--home-lift": phenotype.branch_lift,
    "--home-root": phenotype.root_spread,
    "--home-bark": phenotype.bark_definition,
    "--home-moisture": phenotype.surface_moisture,
    "--home-saturation": 0.86 + (phenotype.surface_moisture - 0.8) * 0.35,
    "--home-contrast": 0.95 + (phenotype.bark_definition - 0.82) * 0.18,
    "--home-resonance": 0.16 + (phenotype.branch_lift - 0.84) * 0.34,
  } as CSSProperties;

  return (
    <div
      className="home-tree-experience"
      data-tree-ref={home.tree.tree_ref}
      style={style}
    >
      <div className="home-tree-stage" aria-label={`${home.profile.display_name}的生命树`}>
        <img
          className="home-tree-base"
          data-asset-ref={background.asset_ref}
          src={background.url}
          alt=""
        />
        <div className="home-paper-light" aria-hidden="true" />
        <div className="home-tree-breath" aria-hidden="true" />
        <div className="home-tree-copy">
          <p className="eyebrow">我的生命树</p>
          <h1>{home.profile.display_name}，这里先记住你。</h1>
          <p>
            这棵树来自你当前版本的命盘事实。进入梦境后，我们会观察另一条正在继续的人生。
          </p>
          <div className="home-pillar-line" aria-label="当前四柱">
            {PILLAR_ORDER.map((slot) => (
              <span key={slot}>{home.chart.pillars[slot]}</span>
            ))}
          </div>
          <button
            className="home-dream-command"
            type="button"
            disabled={busy}
            onClick={onEnterDream}
          >
            跟阿布进入梦境
            <span aria-hidden="true">→</span>
          </button>
        </div>

        <div className="home-phenotype-key" aria-label="生命树事实纹理">
          <p>当前生命纹理</p>
          <div>
            {ELEMENTS.map(([key, label]) => (
              <span key={key}>
                <i
                  aria-hidden="true"
                  style={{
                    opacity: Math.max(
                      0.28,
                      phenotype.element_membership_ratios[key] * 2.6,
                    ),
                  }}
                />
                {label}
                <small>
                  {Math.round(phenotype.element_membership_ratios[key] * 100)}
                </small>
              </span>
            ))}
          </div>
          <small>视觉隐喻，不代表旺衰或有效做功</small>
        </div>

        <AbuCompanionMotion
          className="home-abu-actor"
          cueKey={`home:${home.context_ref}`}
          guideLeft={false}
          guideLeftCue={media.cues.abu_guide_left}
          idleCue={media.cues.abu_idle}
          label="阿布安静坐在你的生命树与梦境入口之间"
        />
      </div>
    </div>
  );
}
