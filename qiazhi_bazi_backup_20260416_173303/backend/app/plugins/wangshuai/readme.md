# 旺衰（`classical.wangshuai.v1`）

在 **L1 流水线**（含 `op_status` 缩放）之后读取 `deity_energy_axes` 与 `deity_trace_details`，将 **印比阵营**（比肩、劫财、正印、偏印）的 Raw 通道拆为三维 Skill，并与 `self_abs` 对齐。

## 得令 `ws_season`（令）

对任意印比十神 \(D\)，令通道能量：

\[
W_{\mathrm{season}} = \sum_{D \in \mathcal{S}} \sum_{s \in \mathrm{Src}(D),\, s \,\text{以}\,\texttt{month.}\text{为前缀}} e(s)
\]

其中 \(e(s)\) 为 `contribution_sources[].contribution_energy`。

## 得地 `ws_root`（地）

\[
W_{\mathrm{root}} = \sum_{D \in \mathcal{S}} \sum_{s:\, \texttt{.branch:}\in s,\, s \not\sim \texttt{month.}} e(s)
\]

## 得助 `ws_support`（助）

\[
W_{\mathrm{support}} = \sum_{D \in \mathcal{S}} \sum_{s:\, \texttt{.stem:}\in s,\, s \not\sim \texttt{month.}} e(s)
\]

## 与 `self_abs` 对齐（审计展示）

令 \(S = W_{\mathrm{season}}+W_{\mathrm{root}}+W_{\mathrm{support}}\)，`self_abs` 为印比 `absolute_energy` 之和。审计项中的 `abs_contribution` 取：

\[
\texttt{abs\_contribution}_k \approx \texttt{self\_abs} \times \frac{W_k}{S}\quad (S>0)
\]

否则退回 Raw 通道值，避免除零。
