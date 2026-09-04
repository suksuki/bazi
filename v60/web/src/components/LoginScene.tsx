import { type FormEvent, useState } from "react";

import { AbuIdle } from "../AbuIdle";
import type { PublicRuntimeMediaManifest } from "../publicRuntimeTypes";
import { BrandMark } from "./BrandMark";
import { LifeTreeBackdrop } from "./LifeTreeBackdrop";

interface LoginSceneProps {
  media: PublicRuntimeMediaManifest;
  busy: boolean;
  error: string | null;
  onLogin: (email: string, password: string) => Promise<void>;
}

export function LoginScene({
  media,
  busy,
  error,
  onLogin,
}: LoginSceneProps) {
  const [email, setEmail] = useState("jerrydidi@gmail.com");
  const [password, setPassword] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void onLogin(email, password);
  };

  return (
    <main className="v60-root v60-shell login-shell">
      <header className="app-header login-header">
        <BrandMark asset={media.assets.brand_logo} />
        <p className="login-world-mark">命盘 · 断命 · 阿布说</p>
      </header>

      <div className="login-layout">
        <section className="login-visual" aria-label="阿布知命 V60">
          <LifeTreeBackdrop asset={media.assets.login_life_tree_background} />
          <div className="login-visual-wash" aria-hidden="true" />
          <div className="login-intro">
            <p className="eyebrow">阿布知命 V60</p>
            <h1>
              回来时，
              <br />
              生命树仍在生长。
            </h1>
            <p>你的命盘、断语与每一次校准，都沿同一条生命线生长。</p>
          </div>
          <AbuIdle
            className="login-abu"
            cue={media.cues.abu_idle}
            label="阿布坐在生命树旁，安静地等待你回来"
          />
          <p className="login-scene-note">
            <span aria-hidden="true" />
            生命树入口已经亮起
          </p>
        </section>

        <section className="login-panel">
          <div>
            <p className="eyebrow">欢迎回来</p>
            <h2>进入你的生命现场</h2>
            <p>使用已有账号继续上一次尚未完成的命理解读。</p>
          </div>
          <form className="login-form" onSubmit={submit}>
            <label>
              <span>账号</span>
              <input
                autoComplete="username"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label>
              <span>密码</span>
              <input
                autoComplete="current-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoFocus
              />
            </label>
            <button type="submit" disabled={busy || !password}>
              {busy ? "正在进入" : "进入生命树"}
              <span aria-hidden="true">→</span>
            </button>
            {error && (
              <p className="login-error" role="alert">
                登录没有完成：{error}
              </p>
            )}
          </form>
          <p className="login-boundary">
            V60 使用独立生命档案，不读取旧系统运行状态。
          </p>
        </section>
      </div>
    </main>
  );
}
