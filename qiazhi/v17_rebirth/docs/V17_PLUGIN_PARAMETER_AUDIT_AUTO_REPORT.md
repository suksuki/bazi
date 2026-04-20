# V17 插件参数来源与默认值审计（自动版）

生成时间：2026-04-20 11:45:45

## 总览
- 插件数：55
- 参数项数：162
- 配置文件缺失：0

## 风险清单
- 未落地参数（声明未接线）：
  - 无
- 高风险默认值：
  - 无

## 明细（Top 400）
| 插件 | 参数 | 默认值 | 来源 | 分类 | 风险 |
| --- | --- | --- | --- | --- | --- |
| classical.blind.response_chain.v1 | MATCH_RATIO_BASE | 0.57 | pattern_defaults | used_and_configurable | - |
| classical.blind.response_chain.v1 | MATCH_RATIO_CAP | 0.8 | pattern_defaults | used_and_configurable | - |
| classical.blind.summary.v1 | MATCH_RATIO_BASE | 0.49 | pattern_defaults | used_and_configurable | - |
| classical.blind.summary.v1 | MATCH_RATIO_CAP | 0.71 | pattern_defaults | used_and_configurable | - |
| classical.blind.symbol_trigger.v1 | MATCH_RATIO_BASE | 0.58 | pattern_defaults | used_and_configurable | - |
| classical.blind.symbol_trigger.v1 | MATCH_RATIO_CAP | 0.8 | pattern_defaults | used_and_configurable | - |
| classical.blind.timing_window.v1 | MATCH_RATIO_BASE | 0.53 | pattern_defaults | used_and_configurable | - |
| classical.blind.timing_window.v1 | MATCH_RATIO_CAP | 0.75 | pattern_defaults | used_and_configurable | - |
| classical.blind.work_axis.v1 | MATCH_RATIO_BASE | 0.68 | pattern_defaults | used_and_configurable | - |
| classical.blind.work_axis.v1 | MATCH_RATIO_CAP | 0.88 | pattern_defaults | used_and_configurable | - |
| classical.pattern.axis.v1 | AXIS_DOMINANT_DIVISOR | 1.5 | pattern_defaults | used_and_configurable | - |
| classical.pattern.axis.v1 | AXIS_DOMINANT_WEIGHT | 0.25 | pattern_defaults | used_and_configurable | - |
| classical.pattern.axis.v1 | AXIS_MATCH_BASE | 0.42 | pattern_defaults | used_and_configurable | - |
| classical.pattern.axis.v1 | AXIS_ORIGIN_SCALE_MIN | 0.92 | pattern_defaults | used_and_configurable | - |
| classical.pattern.axis.v1 | AXIS_TOP_SHARE_WEIGHT | 0.5 | pattern_defaults | used_and_configurable | - |
| classical.pattern.axis.v1 | CANDIDATE_FOLLOWER_RATIO | 2.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.axis.v1 | CANDIDATE_FOLLOWER_SCORE | 35.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.axis.v1 | CANDIDATE_OFFICER_WEALTH | 25.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.axis.v1 | FINANCE_STRONG_MATCH_RATIO | 0.6 | pattern_defaults | used_and_configurable | - |
| classical.pattern.axis.v1 | FORMATION_STRENGTH_RATIO | 2.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congcai.v1 | CONGCAI_MATCH_BASE | 0.74 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congcai.v1 | CONGCAI_MAX_PEER | 12.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congcai.v1 | CONGCAI_MIN_WEALTH | 22.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.conger.v1 | CONGER_MATCH_BASE | 0.74 | pattern_defaults | used_and_configurable | - |
| classical.pattern.conger.v1 | CONGER_MAX_SEAL | 12.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.conger.v1 | CONGER_MIN_OUTPUT | 24.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congge.v1 | SPECIALIZED_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congge.v1 | SPECIALIZED_MAX_OTHER | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congge.v1 | SPECIALIZED_MIN_SCORE | 26.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congqiang.v1 | CONGQIANG_MATCH_BASE | 0.75 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congqiang.v1 | CONGQIANG_MAX_OTHER | 15.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congqiang.v1 | CONGQIANG_MIN_PEER | 28.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congruo.v1 | CONGRUO_MATCH_BASE | 0.72 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congruo.v1 | CONGRUO_MAX_PEER | 10.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congruo.v1 | CONGRUO_MIN_OTHER | 24.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congsha.v1 | CONGSHA_MATCH_BASE | 0.74 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congsha.v1 | CONGSHA_MAX_PEER | 12.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congsha.v1 | CONGSHA_MIN_SHA | 22.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congshi.v1 | CONGSHI_ORIGIN_SCALE_MIN | 0.92 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congshi.v1 | CONGSHI_RATIO_DIVISOR | 2.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congshi.v1 | CONGSHI_RATIO_THRESHOLD | 2.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congshi.v1 | CONGSHI_SCORE_THRESHOLD | 35.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congshi.v1 | CONGSHI_STRONG_RATIO | 2.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congwang.v1 | CONGWANG_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congwang.v1 | CONGWANG_MAX_OTHER | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.congwang.v1 | CONGWANG_MIN_PEER | 30.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.dynamic_scope.v1 | SCOPE_MATCH_BASE | 0.62 | pattern_defaults | used_and_configurable | - |
| classical.pattern.dynamic_scope.v1 | SCOPE_MIN_WEIGHT | 0.06 | pattern_defaults | used_and_configurable | - |
| classical.pattern.dynamic_scope.v1 | SCOPE_MIX_LABEL_BOOST | 1.1 | pattern_defaults | used_and_configurable | - |
| classical.pattern.finance_officer.v1 | FINANCE_MATCH_MIN_ORIGIN_SCALE | 0.92 | pattern_defaults | used_and_configurable | - |
| classical.pattern.finance_officer.v1 | FINANCE_MIN_GOD_SUM | 25.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.guanyin.v1 | GUANYIN_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.guanyin.v1 | GUANYIN_MIN_GUAN | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.guanyin.v1 | GUANYIN_MIN_SEAL | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.huaqi.v1 | HUAQI_MIN_MATCH | 0.72 | pattern_defaults | used_and_configurable | - |
| classical.pattern.jianlu_yuejie.v1 | JIANLU_MATCH_BASE | 0.82 | pattern_defaults | used_and_configurable | - |
| classical.pattern.jianlu_yuejie.v1 | JIANLU_ORIGIN_SCALE_MIN | 0.92 | pattern_defaults | used_and_configurable | - |
| classical.pattern.jiase.v1 | SPECIALIZED_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.jiase.v1 | SPECIALIZED_MAX_OTHER | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.jiase.v1 | SPECIALIZED_MIN_SCORE | 26.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.liangshen.v1 | LIANGSHEN_MATCH_BASE | 0.72 | pattern_defaults | used_and_configurable | - |
| classical.pattern.liangshen.v1 | LIANGSHEN_MIN_PAIR | 18.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.quzhi.v1 | SPECIALIZED_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.quzhi.v1 | SPECIALIZED_MAX_OTHER | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.quzhi.v1 | SPECIALIZED_MIN_SCORE | 26.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.runxia.v1 | SPECIALIZED_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.runxia.v1 | SPECIALIZED_MAX_OTHER | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.runxia.v1 | SPECIALIZED_MIN_SCORE | 26.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.seal_star.v1 | SEAL_MATCH_BASE | 0.74 | pattern_defaults | used_and_configurable | - |
| classical.pattern.seal_star.v1 | SEAL_MIN_SCORE | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.seal_star.v1 | SEAL_ORIGIN_SCALE_MIN | 0.92 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shangguan_peiyin.v1 | SHANGGUAN_PEIYIN_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shangguan_peiyin.v1 | SHANGGUAN_PEIYIN_MIN_HURT | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shangguan_peiyin.v1 | SHANGGUAN_PEIYIN_MIN_SEAL | 15.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shangguan_shengcai.v1 | SHANGGUAN_SHENGCAI_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shangguan_shengcai.v1 | SHANGGUAN_SHENGCAI_MIN_HURT | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shangguan_shengcai.v1 | SHANGGUAN_SHENGCAI_MIN_WEALTH | 15.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shayin.v1 | SHAYIN_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shayin.v1 | SHAYIN_MIN_SEAL | 15.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shayin.v1 | SHAYIN_MIN_SHA | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shishen_shengcai.v1 | SHISHEN_SHENGCAI_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shishen_shengcai.v1 | SHISHEN_SHENGCAI_MIN_SHISHEN | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shishen_shengcai.v1 | SHISHEN_SHENGCAI_MIN_WEALTH | 15.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shishen_zhisha.v1 | SHISHEN_ZHISHA_MATCH_BASE | 0.78 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shishen_zhisha.v1 | SHISHEN_ZHISHA_MIN_SHA | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.shishen_zhisha.v1 | SHISHEN_ZHISHA_MIN_SHISHEN | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.tianyuan.v1 | TIANYUAN_MATCH_BASE | 0.7 | pattern_defaults | used_and_configurable | - |
| classical.pattern.tianyuan.v1 | TIANYUAN_MIN_SAME | 3.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.wealth_star.v1 | WEALTH_MATCH_BASE | 0.72 | pattern_defaults | used_and_configurable | - |
| classical.pattern.wealth_star.v1 | WEALTH_MIN_SCORE | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.wealth_star.v1 | WEALTH_ORIGIN_SCALE_MIN | 0.92 | pattern_defaults | used_and_configurable | - |
| classical.pattern.yangren.v1 | YANGREN_MATCH_BASE | 0.8 | pattern_defaults | used_and_configurable | - |
| classical.pattern.yangren.v1 | YANGREN_MIN_SCORE | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.yangren.v1 | YANGREN_ORIGIN_SCALE_MIN | 0.92 | pattern_defaults | used_and_configurable | - |
| classical.pattern.yangren_jiasha.v1 | YANGREN_JIASHA_MATCH_BASE | 0.78 | pattern_defaults | used_and_configurable | - |
| classical.pattern.yangren_jiasha.v1 | YANGREN_JIASHA_MIN_REN | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.yangren_jiasha.v1 | YANGREN_JIASHA_MIN_SHA | 16.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.yanshang.v1 | SPECIALIZED_MATCH_BASE | 0.76 | pattern_defaults | used_and_configurable | - |
| classical.pattern.yanshang.v1 | SPECIALIZED_MAX_OTHER | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.yanshang.v1 | SPECIALIZED_MIN_SCORE | 26.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.zaqi_caiguan.v1 | ZAQI_CAIGUAN_MATCH_BASE | 0.72 | pattern_defaults | used_and_configurable | - |
| classical.pattern.zaqi_caiguan.v1 | ZAQI_CAIGUAN_MIN_SCORE | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.zaqi_qisha.v1 | ZAQI_QISHA_MATCH_BASE | 0.72 | pattern_defaults | used_and_configurable | - |
| classical.pattern.zaqi_qisha.v1 | ZAQI_QISHA_MIN_SCORE | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.pattern.zaqi_yin.v1 | ZAQI_YIN_MATCH_BASE | 0.72 | pattern_defaults | used_and_configurable | - |
| classical.pattern.zaqi_yin.v1 | ZAQI_YIN_MIN_SCORE | 14.0 | pattern_defaults | used_and_configurable | - |
| classical.ziping.balance.v1 | BALANCE_MODERATE_RATIO | 1.3 | pattern_defaults | used_and_configurable | - |
| classical.ziping.balance.v1 | BALANCE_STRONG_RATIO | 1.8 | pattern_defaults | used_and_configurable | - |
| classical.ziping.balance.v1 | MATCH_RATIO_GAIN | 0.22 | pattern_defaults | used_and_configurable | - |
| classical.ziping.balance.v1 | MATCH_RATIO_MAX | 0.9 | pattern_defaults | used_and_configurable | - |
| classical.ziping.balance.v1 | MATCH_RATIO_MIN | 0.45 | pattern_defaults | used_and_configurable | - |
| classical.ziping.month_command.v1 | MATCH_RATIO_OTHER | 0.72 | pattern_defaults | used_and_configurable | - |
| classical.ziping.month_command.v1 | MATCH_RATIO_TOP | 0.88 | pattern_defaults | used_and_configurable | - |
| classical.ziping.yongshen.v1 | MATCH_RATIO_BASE | 0.58 | pattern_defaults | used_and_configurable | - |
| classical.ziping.yongshen.v1 | MATCH_RATIO_GAIN | 0.14 | pattern_defaults | used_and_configurable | - |
| classical.ziping.yongshen.v1 | MATCH_RATIO_MAX | 0.84 | pattern_defaults | used_and_configurable | - |
| kong_wang | EFFICIENCY | 0.3 | DECLARED_PARAMS | used_and_configurable | - |
| kong_wang | PRIORITY | 0.82 | DECLARED_PARAMS | used_and_configurable | - |
| kong_wang | VOID_THRESHOLD | 0.75 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.full_bandwidth | PRIORITY_FIERCE | 0.65 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.full_bandwidth | PRIORITY_NORMAL | 0.62 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_liuhai | CLASH_LOSS_RATIO | "ref(global.CLASH_LOSS_RATIO)" | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_liuhai | PENETRATION_RATIO | 0.45 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_liuhe | HARMONY_GAIN | 1.15 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_liuhe | STABILITY_WEIGHT | 0.85 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_liupo | BREAK_LOSS | 0.08 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_liupo | FRICTION_COEFF | 0.25 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_muku | OPEN_GATE_BOOST | 1.5 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_muku | STORAGE_EFFICIENCY | 0.35 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_sanhe | FUSION_MID_GAIN | 1.45 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_sanhe | LOCK_RATIO | 0.35 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_sanhe | MIN_HARMONY_STRESS | 0.4 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_sanxing | ENTROPY_LOSS | 0.12 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_branch_sanxing | PENALTY_PRIORITY | 0.93 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_status | RESISTANCE_HIGH | 1.2 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_status | RESISTANCE_LOW | 0.7 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_status | STAGE_PRIORITY | 0.85 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_stem_fusion | STUCK_DAMPING | 0.35 | DECLARED_PARAMS | used_and_configurable | - |
| l1.physics.op_stem_fusion | TRANSFORM_EFFICIENCY | 0.85 | DECLARED_PARAMS | used_and_configurable | - |
| l2.risk.risk_matrix | BLADE_CLASH_IMPULSE | 2.2 | DECLARED_PARAMS | used_and_configurable | - |
| l2.risk.risk_matrix | OFFICER_CRUSH_LIMIT | 0.5 | DECLARED_PARAMS | used_and_configurable | - |
| l2.risk.risk_matrix | OWL_FOOD_CAP | 0.4 | DECLARED_PARAMS | used_and_configurable | - |
| narrative_clip | PRIORITY_AGGRESSIVE | 0.86 | DECLARED_PARAMS | used_and_configurable | - |
| narrative_clip | PRIORITY_STABLE | 0.85 | DECLARED_PARAMS | used_and_configurable | - |
| narrative_clip | SEAL_THRESHOLD | 30.0 | DECLARED_PARAMS | used_and_configurable | - |
| narrative_clip | WEALTH_THRESHOLD | 20.0 | DECLARED_PARAMS | used_and_configurable | - |
| officer_see_hurt | DEFENSE_CAP | 0.5 | DECLARED_PARAMS | used_and_configurable | - |
| officer_see_hurt | HURTING_THRESHOLD | 16.0 | DECLARED_PARAMS | used_and_configurable | - |
| officer_see_hurt | OFFICER_THRESHOLD | 20.0 | DECLARED_PARAMS | used_and_configurable | - |
| officer_see_hurt | PRIORITY | 0.94 | DECLARED_PARAMS | used_and_configurable | - |
| shensha | PRIORITY_BASE | 0.94 | DECLARED_PARAMS | used_and_configurable | - |
| shensha | RESISTANCE_BUFF | 0.1 | DECLARED_PARAMS | used_and_configurable | - |
| shensha | TENSION_MULTIPLIER | 1.4 | DECLARED_PARAMS | used_and_configurable | - |
| shensha | TIAN_YI_THRESHOLD | 40.0 | DECLARED_PARAMS | used_and_configurable | - |
| shensha | YANG_REN_THRESHOLD | 45.0 | DECLARED_PARAMS | used_and_configurable | - |
| ten_god_pattern | AXIS_ORIGIN_SCALE_MIN | 0.92 | 未声明 | used_and_configurable | - |
| ten_god_pattern | CAI_THRESHOLD | 35.0 | DECLARED_PARAMS | used_and_configurable | - |
| ten_god_pattern | GUAN_THRESHOLD | 40.0 | DECLARED_PARAMS | used_and_configurable | - |
| ten_god_pattern | PATTERN_PRIORITY | 0.78 | DECLARED_PARAMS | used_and_configurable | - |
| ten_god_pattern | PROFILE_MIN_SCORE | 10.0 | 未声明 | used_and_configurable | - |
| ten_god_pattern | PROFILE_TOP_GODS | 3 | 未声明 | used_and_configurable | - |
| ten_god_pattern | SHI_SHANG_THRESHOLD | 35.0 | DECLARED_PARAMS | used_and_configurable | - |

## 下一步建议
- 按清单处理 `declared_but_unused`，优先确认是否确为历史冗余参数。
- 对 `used_but_no_config_file` 类项立即补齐配置文件，避免回退到硬编码。
- 优先把关键风险项纳入 `V17_PLUGIN_DEFAULT_VALUE_AUDIT`，并设置变更审计。
