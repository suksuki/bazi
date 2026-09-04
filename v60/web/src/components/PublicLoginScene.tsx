import { useState, type FormEvent } from "react";

import type { RuntimeAssetDelivery } from "../publicRuntimeTypes";

export function PublicLoginScene({
  brand,
  busy,
  error,
  onLogin,
}: {
  brand: RuntimeAssetDelivery;
  busy: boolean;
  error: string | null;
  onLogin: (email: string, password: string) => Promise<void>;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void onLogin(email.trim(), password);
  };

  return (
    <main className="public-login">
      <section className="public-login-intro" aria-labelledby="login-title">
        <img className="public-login-logo" src={brand.url} alt="阿布知命" />
        <p className="public-kicker">八字 · 断命 · 阿布说</p>
        <h1 id="login-title">把复杂命理，讲成你听得懂的话。</h1>
        <p className="public-login-lead">
          输入自己的出生资料，先看清命局主线，再按性情、事业财富、感情家庭和近年趋势逐项细看。
        </p>
        <div className="public-login-promise" aria-label="产品特点">
          <span>一盘一档</span>
          <span>结论先行</span>
          <span>阿布陪你读</span>
        </div>
      </section>

      <section className="public-login-card" aria-label="登录阿布知命">
        <div>
          <p className="public-kicker">欢迎回来</p>
          <h2>进入我的命盘</h2>
          <p>你的出生资料和断命记录只在登录后的私密档案中展示。</p>
        </div>
        <form onSubmit={submit}>
          <label>
            <span>邮箱</span>
            <input
              autoComplete="email"
              inputMode="email"
              name="email"
              placeholder="name@example.com"
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            <span>密码</span>
            <input
              autoComplete="current-password"
              name="password"
              placeholder="请输入密码"
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && <p className="public-form-error" role="alert">{error}</p>}
          <button className="public-primary-button" disabled={busy} type="submit">
            {busy ? "正在进入…" : "查看我的命盘"}
          </button>
        </form>
        <small>命理内容用于传统文化探索与个人参考，不替代医疗、法律或投资建议。</small>
      </section>
    </main>
  );
}
