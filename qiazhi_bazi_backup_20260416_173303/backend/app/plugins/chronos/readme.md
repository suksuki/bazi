# Chronos（`base.chronos`）

时空权重在 **meta 层** 记账，与 `physics_calculations` 中的季节因子解耦：此处强调 **月令本气（司令）** 与 **余气 / 进气** 的可分审计。

## 符号

- \(b\)：月令地支；\(\mathrm{Hidden}(b,s)\)：支 \(b\) 藏干 \(s\) 的原始权重（与 `BRANCH_HIDDEN_STEMS` 同源）。
- \(T=\sum_s \mathrm{Hidden}(b,s)\)，本气天干 \(s^\*=\arg\max_s \mathrm{Hidden}(b,s)\)。
- \(r_{\mathrm{main}} = \mathrm{Hidden}(b,s^\*)/T\)，\(r_{\mathrm{res}} = 1-r_{\mathrm{main}}\)。

## 司令（Skill `mp_chronos_command`）

\[
W_{\mathrm{cmd}} = \mathrm{clamp}\Bigl(r_{\mathrm{main}}\cdot(1+\lambda_{\mathrm{cmd}}),\,0.25,\,1.35\Bigr)
\]

其中 \(\lambda_{\mathrm{cmd}}=\) `CHRONOS_COMMAND_LEVER`（默认 0）。

## 余气 / 进气（Skill `mp_chronos_residual`）

\[
\Delta_{\mathrm{res}} = r_{\mathrm{res}}\cdot\lambda_{\mathrm{res}} + \beta(b)
\]

- \(\lambda_{\mathrm{res}}=\) `CHRONOS_RESIDUAL_LEVER`（默认 0.12）。
- \(\beta(b)\) 为交季支偏置（辰/戌/丑/未），见 `core._INTAKE_BRANCH_BIAS`。

## 合成（仅 meta 展示）

\[
W_{\mathrm{eff}} = \mathrm{clamp}(W_{\mathrm{cmd}}+\Delta_{\mathrm{res}},\,0.25,\,1.35)
\]
