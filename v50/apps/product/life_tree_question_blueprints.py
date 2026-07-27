from __future__ import annotations

from experience.life_tree_questions import (
    LIFE_TREE_QUESTION_BANK_VERSION,
    QuestionBlueprint,
    QuestionEvidenceRequirement,
    QuestionOptionBlueprint,
)


QUESTION_BLUEPRINT_PROVENANCE = [
    "owner-program:REAL-LIFECASE-LIFE-TREE:question-bank-v1",
    "contract:deepbazi.relation-fact.rgm02.v1",
    "contract:deepbazi.work-path-candidate.wpm01.v1",
    "contract:deepbazi.relation-work-projection.p0.v1",
]
RELATION_LAB_QUESTION_BANK_VERSION = "deepbazi.life-tree-question-bank.p0.v1"


def load_life_tree_question_blueprints() -> list[QuestionBlueprint]:
    """Reality-observation flowers admitted from current structural candidates."""

    return [
        _life_blueprint(
            "LQ-REAL-OUTPUT-WEALTH-01",
            "产出会不会真正落成收入",
            (
                "在你选定的下一次具体产出窗口里，这份成果最终更接近"
                "哪一种可核验的现实结果？"
            ),
            life_domain="career_wealth",
            path_labels=["食伤生财"],
            distinguishes=[
                "completed_with_attributable_revenue",
                "completed_without_attributable_revenue",
                "no_material_completion",
            ],
            options=[
                (
                    "completed_with_revenue",
                    "成果完成，并在窗口内形成可归因收入",
                    "封存了“产出完成且形成可归因收入”的现实观察。",
                ),
                (
                    "completed_without_revenue",
                    "成果完成，但没有形成可归因收入",
                    "封存了“完成产出但未形成可归因收入”的现实观察。",
                ),
                (
                    "no_material_completion",
                    "窗口内没有形成可核验的完成成果",
                    "封存了“尚未形成可核验完成成果”的现实观察。",
                ),
            ],
            observation_window="绑定一项具体产出后观察 30 天；以明确开始日与截止日为准。",
            future_evidence=[
                "具体产出的范围、开始时间与完成记录",
                "窗口内可归因的合同、收款或收入凭证",
                "截止日仍未完成时的状态记录",
            ],
        ),
        _life_blueprint(
            "LQ-REAL-OUTPUT-PRESSURE-01",
            "一次表达能否改变现实要求",
            (
                "面对下一项有明确要求或评审标准的任务，你提交的方案"
                "最终会怎样改变那项要求？"
            ),
            life_domain="career",
            path_labels=["食伤制杀"],
            distinguishes=[
                "requirement_materially_changed",
                "requirement_partially_relaxed",
                "requirement_not_changed",
            ],
            options=[
                (
                    "material_change",
                    "要求被明确调整，方案成为实际执行依据",
                    "封存了“表达或方案实质改变要求”的观察。",
                ),
                (
                    "partial_change",
                    "只缓解一部分要求，核心约束仍在",
                    "封存了“局部缓解但核心约束仍在”的观察。",
                ),
                (
                    "no_change",
                    "没有形成可核验的要求变化",
                    "封存了“没有形成可核验变化”的观察。",
                ),
            ],
            observation_window="绑定一项有书面要求或评审标准的任务，观察至最终决定。",
            future_evidence=[
                "封存时的原始任务要求或评审标准",
                "提交的方案、表达或可检查成果",
                "最终决定及要求变更记录",
            ],
        ),
        _life_blueprint(
            "LQ-REAL-RESOURCE-RESPONSIBILITY-01",
            "获得的资源能否承接一项责任",
            (
                "下一次你获得一笔明确资源并同时承担具体责任时，"
                "这项责任最终会完成到什么程度？"
            ),
            life_domain="career_wealth",
            path_labels=["财生杀"],
            distinguishes=[
                "resource_supports_completion",
                "resource_supports_partial_completion",
                "resource_does_not_support_completion",
            ],
            options=[
                (
                    "complete",
                    "资源到位，责任按约完成",
                    "封存了“资源对责任完成形成实际支持”的观察。",
                ),
                (
                    "partial",
                    "资源到位，但只完成一部分或过程不稳定",
                    "封存了“有限支持且完成不稳定”的观察。",
                ),
                (
                    "not_completed",
                    "没有形成可核验的责任完成",
                    "封存了“资源未转化为责任完成”的观察。",
                ),
            ],
            observation_window="绑定一项资源与责任均可确认的事件，观察至责任截止日。",
            future_evidence=[
                "资源到账、授权或可使用状态的记录",
                "责任范围、截止时间与验收条件",
                "最终完成或未完成的验收记录",
            ],
        ),
        _life_blueprint(
            "LQ-REAL-OUTPUT-DESTINATION-01",
            "同一份成果会先落向哪里",
            (
                "下一次你交付一份可检查成果时，最先出现的可核验反馈"
                "更接近哪一种？"
            ),
            life_domain="career",
            path_labels=["食伤生财", "食伤制杀"],
            minimum_path_count=2,
            minimum_competing_path_count=2,
            distinguishes=[
                "first_feedback_is_revenue",
                "first_feedback_is_requirement_change",
                "neither_feedback_is_verified",
            ],
            options=[
                (
                    "revenue_first",
                    "先形成合同、收款或可归因收入",
                    "封存了“现实反馈先落向收入”的比较观察。",
                ),
                (
                    "requirement_change_first",
                    "先改变要求、评审或约束条件",
                    "封存了“现实反馈先落向要求变化”的比较观察。",
                ),
                (
                    "neither",
                    "窗口内两种反馈都没有被核验",
                    "封存了“窗口内两种反馈均未核验”的观察。",
                ),
            ],
            observation_window="绑定一次成果交付，观察其后 30 天内最先出现的正式反馈。",
            future_evidence=[
                "成果交付时间与可检查内容",
                "合同、收款或可归因收入的发生时间",
                "要求、评审或约束变化的正式记录与发生时间",
            ],
        ),
    ]


def load_relation_lab_question_blueprints() -> list[QuestionBlueprint]:
    """Structural learning questions shown only inside canonical Mingli Lab."""

    return [
        _blueprint(
            "LT-F01",
            "factual_observation",
            "先看见一条“生”关系",
            "{participant_a}与{participant_b}之间，当前投影确实呈现了哪类结构事实？",
            relation_families=["generates"],
            distinguishes=["relation_present", "relation_absent"],
            options=_relation_presence_options(),
        ),
        _blueprint(
            "LT-F02",
            "factual_observation",
            "先看见一条“克”关系",
            "{participant_a}与{participant_b}之间的结构关系，哪种描述最贴近当前事实层？",
            relation_families=["controls"],
            distinguishes=["controls_present", "controls_not_observed"],
            options=_relation_presence_options(),
        ),
        _blueprint(
            "LT-F03",
            "factual_observation",
            "辨认子午关系",
            "当前树中出现的{relation_family}，准确落在哪两个坐标参与者之间？",
            relation_families=["clashes"],
            distinguishes=["exact_coordinate_pair", "same_glyph_other_coordinate"],
            options=[
                ("exact_pair", "{participant_a} 与 {participant_b}", "选择了投影中的精确坐标对。"),
                ("glyph_only", "只看子午字样，不区分坐标", "选择了脱离坐标的字样概括。"),
                ("effect_guess", "直接视为已经产生结果", "把关系存在误当成了效果成立。"),
            ],
        ),
        _blueprint(
            "LT-F04",
            "factual_observation",
            "坐标比字样更重要",
            "为什么这道题同时保留{participant_a}和{participant_b}的完整坐标？",
            distinguishes=["coordinate_identity", "glyph_identity_only"],
            options=[
                ("coordinate_identity", "同字在不同位置仍是不同参与者", "注意到了六柱坐标身份。"),
                ("glyph_identity", "同字出现就可以合并成一个节点", "选择了会丢失坐标的概括。"),
                ("visual_only", "只是为了画面更丰富", "把权威坐标误解为装饰。"),
            ],
        ),
        _blueprint(
            "LT-F05",
            "factual_observation",
            "关系状态不等于作用结果",
            "在{temporal_stage}层看到关系存在时，最稳妥的第一步是什么？",
            requires_unresolved_effect=True,
            distinguishes=["fact_present", "professionally_resolved"],
            options=[
                ("record_fact", "先记录关系事实与激活层", "保持事实、激活与效果分离。"),
                ("declare_effect", "直接判为有效做功", "把事实存在越级成专业效果。"),
                ("rank_path", "马上给所有路径排强弱", "引入了未授权的专业排名。"),
            ],
        ),
        _blueprint(
            "LT-C01",
            "candidate_comparison",
            "同一食伤的两种去向",
            "{path_a}与{path_b}共享参与者时，你更想先比较哪一类证据？",
            path_labels=["食伤生财", "食伤制杀"],
            minimum_competing_path_count=2,
            distinguishes=["food_output_to_wealth", "food_output_to_killing"],
            options=[
                ("effect_receipts", "两条关系各自缺少的效果证据", "选择比较两条候选的效果缺口。"),
                ("capacity", "共同参与者能否同时承接两条结构", "选择比较共享资源与承载问题。"),
                ("visual_prominence", "哪条线在图上更粗", "选择了非权威的视觉显著性。"),
            ],
        ),
        _blueprint(
            "LT-C02",
            "candidate_comparison",
            "直接路径与经财路径",
            "比较{path_a}与{path_b}时，哪项最能说明两者不是同一候选？",
            path_labels=["食伤生财", "财生杀"],
            minimum_path_count=2,
            distinguishes=["different_actor_receiver", "same_chart_presence"],
            options=[
                ("roles", "生产者、动作与接收者不同", "用角色身份区分候选。"),
                ("same_chart", "都在同一命盘，所以视为同一路径", "把共盘存在误当成同一路径。"),
                ("rank", "线更短的一条必然更强", "用图指标冒充专业结论。"),
            ],
        ),
        _blueprint(
            "LT-C03",
            "candidate_comparison",
            "共享参与者形成竞争",
            "当{path_a}和{path_b}共享同一生产者时，当前最多能确认什么？",
            minimum_path_count=2,
            minimum_competing_path_count=2,
            distinguishes=["competition_present", "dominant_path"],
            options=[
                ("competition", "存在需要进一步分辨的结构竞争", "确认竞争但不指定胜者。"),
                ("dominant", "自动选出更显眼的一条为主线", "越级声明了主线。"),
                ("both_effective", "两条都自动成为有效做功", "越级声明了效果。"),
            ],
        ),
        _blueprint(
            "LT-C04",
            "candidate_comparison",
            "路径是有序事实段",
            "{path_a}为什么不能只用一个名称代替它的证据？",
            path_labels=["食伤生财"],
            minimum_path_count=1,
            distinguishes=["ordered_fact_segments", "label_only"],
            options=[
                ("ordered_segments", "它必须引用有序的关系事实段", "保留了路径的可追溯结构。"),
                ("label_only", "名称本身已经证明效果", "把标签当成专业证据。"),
                ("color", "树叶颜色即可证明", "把视觉隐喻当成事实。"),
            ],
        ),
        _blueprint(
            "LT-C05",
            "candidate_comparison",
            "三条候选仍不等于主线",
            "此树同时出现三条结构候选时，下一步最不应省略什么？",
            minimum_path_count=3,
            distinguishes=["candidate_set", "unsupported_mainline"],
            options=[
                ("blockers", "逐条查看阻断、承载与未解效果", "保留独立状态轴。"),
                ("mainline", "按节点数量直接选主线", "使用诊断数量冒充专业重要性。"),
                ("merge", "把三条合并成一个泛化结论", "丢失了候选角色和顺序。"),
            ],
        ),
        _blueprint(
            "LT-D01",
            "discriminating",
            "食伤生财还缺什么",
            "{path_a}已经结构连续，但要进一步判定作用，最需要补哪类证据？",
            path_labels=["食伤生财"],
            minimum_path_count=1,
            requires_unresolved_effect=True,
            distinguishes=["structural_candidate", "effective_mechanism"],
            options=_effect_gap_options(),
        ),
        _blueprint(
            "LT-D02",
            "discriminating",
            "食伤制杀还缺什么",
            "{path_a}成立为候选后，哪一项仍不能从结构连续性自动推出？",
            path_labels=["食伤制杀"],
            minimum_path_count=1,
            requires_unresolved_effect=True,
            distinguishes=["path_identity", "effect_and_usability"],
            options=_effect_gap_options(),
        ),
        _blueprint(
            "LT-D03",
            "discriminating",
            "财生杀的承载问题",
            "{path_a}要从候选进入专业判定，哪条轴必须保持独立核验？",
            path_labels=["财生杀"],
            minimum_path_count=1,
            requires_unresolved_effect=True,
            distinguishes=["capacity_unresolved", "presence_only"],
            options=[
                ("capacity", "承载与可用性证据", "选择了独立的承载/可用性轴。"),
                ("presence", "关系出现本身", "把存在当成承载成立。"),
                ("adjacency", "节点画得相邻", "把画面邻接当成效果。"),
            ],
        ),
        _blueprint(
            "LT-D04",
            "discriminating",
            "竞争候选靠什么分辨",
            "{path_a}与{path_b}都可见时，哪类新证据真正有区分力？",
            minimum_path_count=2,
            minimum_competing_path_count=2,
            distinguishes=["candidate_a", "candidate_b"],
            options=[
                ("different_receipts", "分别对应的效果、承载与反事实证据", "寻找能区分候选的独立证据。"),
                ("same_actor", "它们共享同一参与者", "共同事实不能区分两条候选。"),
                ("line_count", "哪条线连接更多", "使用诊断图指标做专业排名。"),
            ],
        ),
        _blueprint(
            "LT-D05",
            "discriminating",
            "子午冲只确认到哪里",
            "{participant_a}与{participant_b}的冲关系已经存在，当前专业边界停在哪里？",
            relation_families=["clashes"],
            requires_unresolved_effect=True,
            distinguishes=["clash_fact", "unsupported_clash_effect"],
            options=[
                ("fact_only", "确认精确关系，具体作用仍待定", "遵守子午冲有界解析。"),
                ("damage", "自动判定冲坏", "越过了尚未准入的效果原子。"),
                ("event", "直接预测现实事件", "越过了禁止的事件推断。"),
            ],
        ),
        _blueprint(
            "LT-T01",
            "temporal_change",
            "原局存在与时序激活分开看",
            "当前{relation_family}事实处于{temporal_stage}层，哪种记录最准确？",
            activation_states=["natal_present"],
            distinguishes=["natal_presence", "temporal_activation"],
            options=[
                ("natal", "原局关系存在", "准确记录当前原局事实。"),
                ("activated", "已经被特定流年激活", "把原局存在误写为时序激活。"),
                ("effective", "已经形成专业效果", "把层级状态越级。"),
            ],
        ),
        _blueprint(
            "LT-T02",
            "temporal_change",
            "子午冲的时序问题",
            "若未来出现新的时序参与者，第一项应重新核验什么？",
            relation_families=["clashes"],
            distinguishes=["temporal_identity", "automatic_effect"],
            options=[
                ("identity", "参与者坐标与激活快照", "先核验时序身份。"),
                ("reuse", "直接复用原局效果结论", "假定了尚不存在的效果结论。"),
                ("event", "先给出现实事件判断", "绕过了证据链。"),
            ],
        ),
        _blueprint(
            "LT-T03",
            "temporal_change",
            "候选路径的时序轴",
            "{path_a}在原局可见时，时序变化首先应该更新哪一项？",
            minimum_path_count=1,
            distinguishes=["timing_axis", "path_identity"],
            options=[
                ("timing_axis", "独立的 timing_state 与时间证据", "保持路径身份和时序轴分离。"),
                ("identity", "重造一条无来源的新路径", "丢失原路径身份。"),
                ("rank", "提高专业排名", "引入了未授权的评分。"),
            ],
        ),
        _blueprint(
            "LT-T04",
            "temporal_change",
            "竞争不会因流年字样自动消失",
            "{path_a}与{path_b}在原局竞争时，流年出现相关字样能直接决定胜负吗？",
            minimum_path_count=2,
            minimum_competing_path_count=2,
            distinguishes=["temporal_evidence", "automatic_winner"],
            options=[
                ("no", "不能；需新增事实与效果证据", "拒绝由字样直接选胜者。"),
                ("yes", "能；出现就自动成为主线", "把时序出现当成专业胜负。"),
            ],
        ),
        _blueprint(
            "LT-T05",
            "temporal_change",
            "恢复原局必须可重放",
            "结束临时时序观察后，系统应如何回到此树原局？",
            requires_unresolved_effect=True,
            distinguishes=["exact_restore", "mutated_natal"],
            options=[
                ("replay", "按原快照与事实修订精确恢复", "选择可重放恢复。"),
                ("keep", "把临时关系写回原局", "污染了原局权威。"),
                ("guess", "由前端猜一个相近状态", "让消费者制造事实。"),
            ],
        ),
        _blueprint(
            "LT-X01",
            "counterfactual",
            "拿走食伤节点",
            "若暂时移除{participant_a}，{path_a}的结构连续性应怎样处理？",
            path_labels=["食伤生财"],
            minimum_path_count=1,
            requires_counterfactual_subject=True,
            distinguishes=["path_breaks", "path_survives"],
            options=_counterfactual_options(),
        ),
        _blueprint(
            "LT-X02",
            "counterfactual",
            "拿走制杀关系段",
            "若移除{path_a}所依赖的一段关系事实，系统应保留什么结果？",
            path_labels=["食伤制杀"],
            minimum_path_count=1,
            requires_counterfactual_subject=True,
            distinguishes=["candidate_break", "professional_rejection"],
            options=_counterfactual_options(),
        ),
        _blueprint(
            "LT-X03",
            "counterfactual",
            "拿走财节点",
            "若{participant_a}不再参与，{path_a}是否仍是同一个候选？",
            path_labels=["财生杀"],
            minimum_path_count=1,
            requires_counterfactual_subject=True,
            distinguishes=["identity_changed", "label_survives"],
            options=_counterfactual_options(),
        ),
        _blueprint(
            "LT-X04",
            "counterfactual",
            "拿走子午冲事实",
            "若撤回{participant_a}与{participant_b}之间的冲事实，专业效果层应发生什么？",
            relation_families=["clashes"],
            requires_counterfactual_subject=True,
            distinguishes=["fact_withdrawn", "effect_persists_without_fact"],
            options=[
                ("withdraw", "相关效果解析失去事实前提", "保持效果对事实修订的依赖。"),
                ("persist", "即使事实撤回，效果仍自动保留", "让效果脱离事实来源。"),
                ("event", "改写成新的现实事件", "引入了未授权事件。"),
            ],
        ),
        _blueprint(
            "LT-X05",
            "counterfactual",
            "共享节点是竞争的切点",
            "若移除{participant_a}，{path_a}与{path_b}的竞争信息应怎样变化？",
            minimum_path_count=2,
            minimum_competing_path_count=2,
            requires_counterfactual_subject=True,
            distinguishes=["both_affected", "one_unrelated"],
            options=[
                ("recompute", "分别重算两条候选的连续性与共享声明", "执行可追溯的反事实重算。"),
                ("choose", "保留更显眼的一条并称为主线", "借反事实越级选主线。"),
                ("mutate", "直接修改原局事实", "把实验写回权威状态。"),
            ],
        ),
    ]


def _life_blueprint(
    blueprint_id: str,
    title: str,
    prompt: str,
    *,
    life_domain: str,
    path_labels: list[str],
    distinguishes: list[str],
    options: list[tuple[str, str, str]],
    observation_window: str,
    future_evidence: list[str],
    minimum_path_count: int = 1,
    minimum_competing_path_count: int = 0,
) -> QuestionBlueprint:
    return QuestionBlueprint(
        blueprint_id=blueprint_id,
        category="life_observation",
        purpose="life_observation",
        title=title,
        prompt_template=prompt,
        options=[
            QuestionOptionBlueprint(
                option_id=option_id,
                label_template=label,
                exploration_meaning=meaning,
            )
            for option_id, label, meaning in options
        ],
        requirements=QuestionEvidenceRequirement(
            fact_states=[
                "RELATION_STRUCTURALLY_PRESENT",
                "TARGETS_IDENTIFIED",
            ],
            path_labels=path_labels,
            minimum_path_count=minimum_path_count,
            minimum_competing_path_count=minimum_competing_path_count,
            requires_unresolved_effect=True,
        ),
        relevance_reason=(
            "当前冻结投影只确认了结构候选 {path_a} / {path_b}；"
            "它为现实观察提供缘由，但不预告哪种结果会发生。"
            "封存前的命盘事实不会在未来揭盲时计作结果证据。"
        ),
        distinguishes=distinguishes,
        permitted_exploration_writes=[
            "selected_option",
            "observation",
            "open_question",
            "candidate_preference",
        ],
        prohibited_truth_writes=[
            "RelationEffectResolution",
            "PathAssertion",
            "main_work",
            "LifeCase",
            "OutcomeEvidence",
        ],
        provenance_refs=[
            *QUESTION_BLUEPRINT_PROVENANCE,
            "boundary:structural-candidate-not-reality-outcome",
            f"question-blueprint:{blueprint_id}@{LIFE_TREE_QUESTION_BANK_VERSION}",
        ],
        life_domain=life_domain,
        observation_window=observation_window,
        reveal_policy="REALITY_FEEDBACK",
        future_evidence_requirements=future_evidence,
        professional_status="STRUCTURAL_CANDIDATE_ONLY",
        baseline_credit_allowed=False,
    )


def _blueprint(
    blueprint_id: str,
    category: str,
    title: str,
    prompt: str,
    *,
    relation_families: list[str] | None = None,
    path_labels: list[str] | None = None,
    minimum_path_count: int = 0,
    minimum_competing_path_count: int = 0,
    activation_states: list[str] | None = None,
    requires_unresolved_effect: bool = False,
    requires_counterfactual_subject: bool = False,
    distinguishes: list[str],
    options: list[tuple[str, str, str]],
) -> QuestionBlueprint:
    return QuestionBlueprint(
        blueprint_id=blueprint_id,
        version=RELATION_LAB_QUESTION_BANK_VERSION,
        category=category,
        title=title,
        prompt_template=prompt,
        options=[
            QuestionOptionBlueprint(
                option_id=option_id,
                label_template=label,
                exploration_meaning=meaning,
            )
            for option_id, label, meaning in options
        ],
        requirements=QuestionEvidenceRequirement(
            relation_families=relation_families or [],
            fact_states=["RELATION_STRUCTURALLY_PRESENT", "TARGETS_IDENTIFIED"],
            activation_states=activation_states or [],
            path_labels=path_labels or [],
            minimum_path_count=minimum_path_count,
            minimum_competing_path_count=minimum_competing_path_count,
            requires_unresolved_effect=requires_unresolved_effect,
            requires_counterfactual_subject=requires_counterfactual_subject,
        ),
        relevance_reason=(
            "此题只因当前树的关系事实与候选路径满足蓝图证据要求而出现；"
            "它帮助区分 {path_a} / {path_b}，不替代专业效果判定。"
        ),
        distinguishes=distinguishes,
        permitted_exploration_writes=[
            "selected_option",
            "observation",
            "open_question",
            "candidate_preference",
        ],
        prohibited_truth_writes=[
            "RelationEffectResolution",
            "PathAssertion",
            "main_work",
            "LifeCase",
        ],
        provenance_refs=[
            *QUESTION_BLUEPRINT_PROVENANCE,
            f"question-blueprint:{blueprint_id}@{LIFE_TREE_QUESTION_BANK_VERSION}",
        ],
    )


def _relation_presence_options() -> list[tuple[str, str, str]]:
    return [
        ("fact_present", "关系事实已出现，作用仍待定", "区分了事实与效果。"),
        ("effective", "已经形成有效做功", "把事实存在越级成专业效果。"),
        ("none", "没有任何关系", "忽略了当前可见事实。"),
    ]


def _effect_gap_options() -> list[tuple[str, str, str]]:
    return [
        ("effect", "独立的效果解析与证据回执", "选择了缺失的专业效果证据。"),
        ("identity", "再次确认还是同一条路径", "只重复身份验证。"),
        ("adjacency", "节点在画面上相邻", "把视觉邻接当成效果。"),
    ]


def _counterfactual_options() -> list[tuple[str, str, str]]:
    return [
        ("recompute", "仅重算候选连续性并保留原局", "执行诊断性反事实。"),
        ("upgrade", "把剩余候选自动升级为主线", "越级声明主线。"),
        ("rewrite", "把移除结果写回 LifeCase", "让实验污染权威事实。"),
    ]


__all__ = [
    "QUESTION_BLUEPRINT_PROVENANCE",
    "load_life_tree_question_blueprints",
    "load_relation_lab_question_blueprints",
]
