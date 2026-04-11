# Base Physics（L1 原子算子）

本目录承载 **生 / 克 / 合绊 / 维轴** 等 L1 算子实现与 `manifests/l1_physics_manifest.json`、`skill_manifest.json` 对齐。

## 相生（`l1_prod_01`）

\[
\mathrm{abs\_gain}' = \mathrm{round}\bigl(\mathrm{abs\_gain}\cdot\mathrm{clamp}(\eta_{\mathrm{prod}},0,3),\,4\bigr)
\]

## 相克（`l1_dest_01`）

\[
\mathrm{abs\_loss}' = \mathrm{round}\bigl(\mathrm{abs\_loss}\cdot\mathrm{clamp}(\eta_{\mathrm{dest}},0,3),\,4\bigr)
\]

（若存在 `impact_torque`，同因子缩放。）

## 合绊（`l1_conn_01`）

\[
\mathrm{abs\_locked}' = \mathrm{round}\bigl(\mathrm{abs\_locked}\cdot\mathrm{clamp}(\eta_{\mathrm{conn}},0,3),\,4\bigr)
\]

## 维轴盖头截脚（`l1_interdim_vert_01`）

同柱干克支或支克干时：

\[
\mathrm{abs\_loss} = \mathrm{round}\bigl(E_{\mathrm{pillar}}\cdot\eta_{\mathrm{crush}}\cdot0.12,\,4\bigr)
\]

\(E_{\mathrm{pillar}}\) 为柱上 `raw_energy`，\(\eta_{\mathrm{crush}}=\) `MANGPAI_ETA_DIMENSIONAL_CRUSH`。

## 十二长生（`l1_status_01` / `op_status`）

对十神 \(D\) 的每个所属天干，在 **月支**、**日支** 查表得长生阶段 \(s\)，由 `l1_status_manifest.json` 的 `stage_strength` 得 \(t\in[0,1]\)，再

\[
m = \mathrm{clamp}\bigl(\lambda_{\mathrm{drain}} + t\cdot(\lambda_{\mathrm{boost}}-\lambda_{\mathrm{drain}}),\,0.05,\,2.5\bigr)
\]

\(E_D' = \mathrm{round}(E_D\cdot m,4)\)，并重算 `relative_percentage`。
