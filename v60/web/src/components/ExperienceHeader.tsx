import type { DreamSnapshot, RuntimeAssetDelivery } from "../api";
import type { HomeSnapshot } from "../homeApi";
import type { MingliStageViewContext } from "../mingliStageTypes";
import { BrandMark } from "./BrandMark";

export function ExperienceHeader({
  accountName,
  brand,
  home,
  mingliContext,
  onLogout,
  onReturnHome,
  scope,
  snapshot,
  inGrove,
}: {
  accountName: string;
  brand: RuntimeAssetDelivery;
  home: HomeSnapshot;
  mingliContext: MingliStageViewContext | null;
  onLogout: () => void;
  onReturnHome: () => void;
  scope: "home" | "dream";
  snapshot: DreamSnapshot | null;
  inGrove: boolean;
}) {
  const inDream = scope === "dream";
  const activeSnapshot = inDream && !inGrove ? snapshot : null;
  const stage = mingliContext?.projection ?? null;
  const pendingSubject =
    mingliContext?.subjectId === "abu"
      ? "阿布"
      : mingliContext?.subjectId === "duoduo"
        ? "多多"
        : "当前档案";
  return (
    <header
      className="app-header"
      data-mingli-projection-ref={stage?.projection_ref}
      data-mingli-subject-id={mingliContext?.subjectId}
    >
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
            {activeSnapshot?.projections.dream.journey_title ?? "三棵生命树"}
          </strong>
        </button>
      ) : mingliContext ? (
        <div className="life-thread-mark" aria-label="当前命理舞台">
          <span className="status-seed" aria-hidden="true" />
          <span>{stage?.identity_badge ?? "命理档案读取中"}</span>
          <strong>{stage ? `${stage.display_name}的命理舞台` : `${pendingSubject}命理舞台`}</strong>
        </div>
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
            {activeSnapshot?.actor.display_name ??
              (inGrove
                ? "雾林入口"
                : mingliContext
                  ? (stage?.display_name ?? pendingSubject)
                  : home.profile.display_name)}
          </strong>
          <span>
            {activeSnapshot
              ? `梦境仍在运行 · ${activeSnapshot.world.current_tick}`
              : inGrove
                ? "三段人生 · 等待选择"
                : mingliContext
                  ? stage
                    ? `${stage.identity_badge} · ${stage.stage_mode === "NATAL_4" ? "本命四柱" : "四柱、大运与流年"}`
                    : mingliContext.status === "ERROR"
                      ? "命理档案 · 读取未完成"
                      : "命理档案 · 正在锁定版本"
                : `私密档案 · 版本 ${home.life_case.revision}`}
          </span>
        </div>
        <button
          className="account-command"
          type="button"
          title="退出当前账号"
          onClick={onLogout}
        >
          {mingliContext ? (stage?.display_name.slice(0, 1) ?? "退") : accountName.slice(0, 1)}
        </button>
      </div>
    </header>
  );
}
