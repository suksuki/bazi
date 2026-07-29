import type { DreamSnapshot, RuntimeAssetDelivery } from "../api";
import type { HomeSnapshot } from "../homeApi";
import { BrandMark } from "./BrandMark";

export function ExperienceHeader({
  accountName,
  brand,
  home,
  onLogout,
  onReturnHome,
  scope,
  snapshot,
  inGrove,
}: {
  accountName: string;
  brand: RuntimeAssetDelivery;
  home: HomeSnapshot;
  onLogout: () => void;
  onReturnHome: () => void;
  scope: "home" | "dream";
  snapshot: DreamSnapshot | null;
  inGrove: boolean;
}) {
  const inDream = scope === "dream";
  return (
    <header className="app-header">
      <BrandMark asset={brand} />
      {inDream ? (
        <button
          className="life-thread-mark scope-return-command"
          type="button"
          onClick={onReturnHome}
        >
          <span aria-hidden="true">←</span>
          <span>梦境中的生命线</span>
          <strong>
            {snapshot?.projections.dream.journey_title ?? "三棵陌生生命树"}
          </strong>
        </button>
      ) : (
        <div className="life-thread-mark" aria-label="当前生命线">
          <span className="status-seed" aria-hidden="true" />
          <span>我的生命线</span>
          <strong>{home.profile.display_name}的生命树</strong>
        </div>
      )}
      <div className="account-area">
        <div className="world-context">
          <strong>
            {snapshot?.actor.display_name ?? (inGrove ? "雾林入口" : home.profile.display_name)}
          </strong>
          <span>
            {snapshot
              ? `梦境仍在运行 · ${snapshot.world.current_tick}`
              : inGrove
                ? "三段人生 · 等待选择"
              : `私密档案 · 版本 ${home.life_case.revision}`}
          </span>
        </div>
        <button
          className="account-command"
          type="button"
          title="退出当前账号"
          onClick={onLogout}
        >
          {accountName.slice(0, 1)}
        </button>
      </div>
    </header>
  );
}
