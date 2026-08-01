import { logout } from "../api";
import type { HomeSnapshot } from "../homeApi";

const PILLARS = ["year", "month", "day", "hour"] as const;

export function HomeWorldSettings({
  home,
  onClose,
  onEnterDream,
  onOpenLab,
}: {
  home: HomeSnapshot;
  onClose: () => void;
  onEnterDream: () => void;
  onOpenLab: () => void;
}) {
  const exitAccount = async () => {
    await logout();
    window.location.reload();
  };

  return (
    <div className="v108-world-overlay" role="presentation" onMouseDown={onClose}>
      <aside
        aria-label="档案、足迹与显示设置"
        className="v108-settings-panel"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header>
          <span>
            <small>我的生命世界</small>
            <strong>档案与足迹</strong>
          </span>
          <button aria-label="关闭" onClick={onClose} type="button">×</button>
        </header>

        <section className="v108-settings-profile">
          <i aria-hidden="true">{home.profile.display_name.slice(0, 1)}</i>
          <div>
            <small>当前档案</small>
            <strong>{home.profile.display_name}的生命树</strong>
            <span>版本 {home.life_case.revision} · 私密档案</span>
          </div>
        </section>

        <section className="v108-settings-pillars" aria-label="当前四柱">
          {PILLARS.map((slot) => (
            <span key={slot}>
              <small>{{ year: "年", month: "月", day: "日", hour: "时" }[slot]}</small>
              <strong>{home.chart.pillars[slot]}</strong>
            </span>
          ))}
        </section>

        <section className="v108-world-footprints">
          <article>
            <i aria-hidden="true">叶</i>
            <span><strong>命理档案已生长</strong><small>Reading 与证据继续由当前 LifeCase 承载</small></span>
          </article>
          <article>
            <i aria-hidden="true">梦</i>
            <span><strong>树洞可以进入</strong><small>梦境进度随账号延续，不随档案叶切换</small></span>
          </article>
          <article>
            <i aria-hidden="true">中</i>
            <span><strong>中文为本轮正式语言</strong><small>多语言接口保留，不提前扩写长内容</small></span>
          </article>
        </section>

        <footer>
          <button onClick={onOpenLab} type="button">进入命理 Lab</button>
          <button onClick={onEnterDream} type="button">进入阿布梦境</button>
          <button className="v108-quiet-command" onClick={() => void exitAccount()} type="button">退出当前账号</button>
        </footer>
      </aside>
    </div>
  );
}
