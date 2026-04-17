"""终判 User 消息小节标题与说明文的语言切片（与 system 契约解耦；VF/插件键名保持 ASCII 技术锚点）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FinalVerdictUserLocale:
    """按请求 language（ZH/EN/KO）输出 User 拼装层自然语言；括号协议如 [Verified Facts] 保持英文键。"""

    lang: str

    def t(self, zh: str, en: str, ko: str) -> str:
        u = (self.lang or "ZH").upper()
        if u == "EN":
            return en
        if u == "KO":
            return ko
        return zh

    def banner_verdict_skeleton(self) -> str:
        return "[VerdictSkeleton]\n"

    def banner_confirmed_decisions(self) -> str:
        return self.t(
            "[ConfirmedDecisions · 用户意志]\n",
            "[ConfirmedDecisions · user will]\n",
            "[ConfirmedDecisions · 사용자 의지]\n",
        )

    def banner_user_will(self) -> str:
        return self.t(
            "[User Will · persistence_layer · 终审最高权重]\n",
            "[User Will · persistence_layer · final_verdict_max_priority]\n",
            "[User Will · persistence_layer · 최종판정_최고가중치]\n",
        )

    def skeleton_empty_fallback(self) -> str:
        return self.t(
            "（暂无物理定论骨架；仍以 [Verified Facts] 为准）",
            "(No verdict skeleton yet; follow [Verified Facts].)",
            "(물리 골격 없음; [Verified Facts]를 기준으로 하십시오.)",
        )

    def no_structured_will_items(self) -> str:
        return self.t(
            "- （无结构化 UPDATE_PHYSICS_PARAM 意志项）",
            "- (No structured UPDATE_PHYSICS_PARAM will entries.)",
            "- (구조화된 UPDATE_PHYSICS_PARAM 의지 항목 없음)",
        )

    def user_will_empty_bullet(self) -> str:
        return self.t(
            "- （暂无已归档意志断语；事实边界仍以 [Verified Facts] 与插件证据为准。）",
            "- (No archived will lines yet; facts still follow [Verified Facts] and plugin evidence.)",
            "- (보관된 의지 문구 없음; 사실 경계는 [Verified Facts] 및 플러그인 증거를 따릅니다.)",
        )

    def user_will_intro(self) -> str:
        return self.t(
            "下列为用户已绑定当前生辰并已明示采纳的语义意志；终审判词须优先与此对齐，不得与之矛盾；"
            "若与下列之外的插件推论冲突，以本块为准进行叙述折衷并在 verdict_body 中温和说明取舍。\n",
            "Below are user-bound, explicitly adopted semantic will lines for this birth chart; the final verdict must align "
            "with them first and must not contradict them. If plugin inferences outside this list conflict, reconcile the "
            "narrative using this block as authority and briefly explain trade-offs in verdict_body.\n",
            "아래는 현재 생시에 바인딩되고 사용자가 명시 채택한 의미적 의지 문장입니다. 최종 판시는 이를 최우선으로 맞추고 "
            "이와 모순되어서는 안 됩니다. 이 목록 밖의 플러그인 추론과 충돌하면 본 블록을 우선으로 서술을 조정하고 "
            "verdict_body에서 완충 설명을 덧붙이십시오.\n",
        )

    def vf_narrative_rules(self, *, contract_polish: bool) -> str:
        base = self.t(
            "你必须仅基于 VF 标签与 [User Decisions] 重组叙事；禁止编造未出现在 VF 中的定量细节。\n"
            "你必须显式响应 [User Decisions] 的最新勾选与归档状态（意志优先于模型先验）。\n",
            "You must reorganize narrative using only VF tags and [User Decisions]; do not invent quantitative details "
            "absent from VF.\n"
            "You must explicitly honor the latest [User Decisions] selections and archived state (will overrides model priors).\n",
            "VF 태그와 [User Decisions]만으로 서사를 재구성하십시오. VF에 없는 정량 세부를 발명하지 마십시오.\n"
            "[User Decisions]의 최신 선택·보관 상태를 명시적으로 반영하십시오(의지가 모델 선행보다 우선).\n",
        )
        polish = ""
        if contract_polish:
            polish = self.t(
                "终审语义整合模式：不得改变 [VerdictSkeleton] 中的事实结构与 VF 引用集合；仅做子平化润色。\n",
                "Final-verdict polish mode: do not change factual structure or the set of VF references in [VerdictSkeleton]; "
                "Ziping-style wording polish only.\n",
                "최종 판시 다듬기 모드: [VerdictSkeleton]의 사실 구조와 VF 인용 집합을 바꾸지 마십시오. 자평 톤으로만 문장을 다듬으십시오.\n",
            )
        return base + polish + "\n"

    def verified_facts_empty(self) -> str:
        return self.t("- （无）\n", "- (none)\n", "- (없음)\n")

    def user_decisions_empty(self) -> str:
        return self.t(
            "- （无用户勾选或归档判词）\n",
            "- (No inbox selections or archived verdict lines.)\n",
            "- (사용자 선택 또는 보관 판문 없음)\n",
        )

    def banner_l1_gate(self) -> str:
        return self.t("\n[L1·结构闸口]\n", "\n[L1·structure_gate]\n", "\n[L1·구조_게이트]\n")

    def banner_narrative_weight(self) -> str:
        return self.t("\n[叙述权重]\n", "\n[narrative_weight]\n", "\n[서술_가중치]\n")

    def banner_pattern_router(self) -> str:
        return self.t("\n[格局路由 PatternRouter]\n", "\n[pattern_router]\n", "\n[pattern_router]\n")

    def banner_pattern_keywords(self) -> str:
        return self.t("\n[格局断言关键词]\n", "\n[pattern_assertion_keywords]\n", "\n[pattern_assertion_keywords]\n")

    def pattern_keywords_empty(self) -> str:
        return self.t("- （无）\n", "- (none)\n", "- (없음)\n")

    def pattern_xiji_line(self, line: str) -> str:
        prefix = self.t("喜忌反转: ", "xi/ji reversal: ", "희기 반전: ")
        return f"- {prefix}{line.strip()}"

    def banner_auxiliary_trace(self) -> str:
        return self.t("\n[Auxiliary·溯源]\n", "\n[Auxiliary·trace]\n", "\n[Auxiliary·trace]\n")

    def banner_learning_annotation(self) -> str:
        return self.t(
            "\n[LearningAnnotation·裁决者修正上下文]\n",
            "\n[LearningAnnotation·arbiter_revision_context]\n",
            "\n[LearningAnnotation·중재자_수정_맥락]\n",
        )

    def learning_hint(self, *, high_reasoning: bool) -> str:
        if high_reasoning:
            return self.t(
                "对齐历史语气；事实边界仍以 [Verified Facts] 为准。",
                "Align historical tone; facts still follow [Verified Facts].",
                "역사적 톤에 맞추되, 사실 경계는 [Verified Facts]를 따릅니다.",
            )
        return self.t(
            "仅调节语气与折中；事实以 [Verified Facts] 为准。",
            "Adjust tone and compromise wording only; facts follow [Verified Facts].",
            "어조·절충만 조절하고, 사실은 [Verified Facts]를 따릅니다.",
        )

    def tone_blind_dominant(self) -> str:
        return self.t(
            "叙述权重：盲派主轴占优；语气偏冷酷、利己，重资源与成败。",
            "Narrative weight: blind-school axis dominant; colder, self-interested tone; resources and outcomes first.",
            "서술 가중: 맹파 축 우세; 냉정·이기적 톤, 자원과 성패 우선.",
        )

    def tone_wangshuai_dominant(self) -> str:
        return self.t(
            "叙述权重：旺衰主轴占优；语气偏平和关怀，重健康与系统平衡。",
            "Narrative weight: strength/weakness axis dominant; calmer, caring tone; health and systemic balance first.",
            "서술 가중: 왕쇠 축 우세; 온화·배려 톤, 건강과 시스템 균형 우선.",
        )

    def tone_balanced(self) -> str:
        return self.t(
            "叙述权重：盲派与旺衰并重；仲裁式语气，兼顾收益与代价。",
            "Narrative weight: blind school and strength/weakness balanced; arbitral tone; balance gains and costs.",
            "서술 가중: 맹파·왕쇠 균형; 중재 톤, 이익과 대가 병행.",
        )

    def chip_conflict_row(self, kind: str, detail: str) -> str:
        prefix = self.t("芯片·冲突点·", "chip·conflict·", "칩·충돌·")
        return f"{prefix}[{kind}] {detail}"

    def shensha_row(self, name: str, branch: str) -> str:
        at = self.t("@支", "@branch", "@지지")
        return f"{name} {at}{branch}"

    def shensha_prefix(self) -> str:
        return self.t("神煞·", "shensha·", "신살·")

    def causal_flow_prefix(self) -> str:
        return self.t("因果流通·", "causal_flow·", "인과_유통·")

    def causal_flow_empty(self) -> str:
        return self.t("（无审计数据）", "(no audit rows)", "(감사 행 없음)")

    def causal_segment_generation(self) -> str:
        return self.t(" 生 ", " generates ", " 생 ")

    def plugin_slice_prefix(self) -> str:
        return self.t("插件切片·", "plugin_slice·", "플러그인_슬라이스·")

    def pillar_snapshot_label(self) -> str:
        return self.t("四柱快照=", "pillars_snapshot=", "사주_스냅샷=")

    def knowledge_line_host_guest(self) -> str:
        return self.t(
            "知识.主宾=年/月为宾，日/时为主",
            "knowledge.host_guest=year/month as guest, day/hour as host",
            "knowledge.host_guest=연/월=빈, 일/시=주",
        )

    def knowledge_line_body_use(self) -> str:
        return self.t(
            "知识.体用=BODY(比劫印) USE(食伤财官)",
            "knowledge.body_use=BODY (peer/rob/resource) USE (output/wealth/officer)",
            "knowledge.body_use=BODY(비겁인) USE(식상재관)",
        )

    def knowledge_line_xufu(self) -> str:
        return self.t(
            "知识.虚浮阈值=Self_Abs<1.0且无根 -> 虚浮",
            "knowledge.float_threshold=Self_Abs<1.0 and no root -> floating",
            "knowledge.float_threshold=Self_Abs<1.0 & 무근 -> 허부",
        )

    def knowledge_encyclopedia_prefix(self, idx: int) -> str:
        return self.t(
            f"知识.百科.{idx + 1}=",
            f"knowledge.digest.{idx + 1}=",
            f"knowledge.digest.{idx + 1}=",
        )

    def blind_work_vector(self, idx: int, t: str, d: str) -> str:
        return self.t(
            f"盲派做功·矢量{idx}·类型={t}·向度={d}",
            f"blind_work·vector{idx}·type={t}·direction={d}",
            f"맹파_작업·벡터{idx}·유형={t}·방향={d}",
        )

    def blind_net_effect(self, net: str) -> str:
        return self.t(
            f"盲派·净效应标签={net}",
            f"blind_school·net_effect={net}",
            f"맹파·순효과={net}",
        )

    def blind_morph_hints(self, joined: str) -> str:
        return self.t(
            f"盲派·形变提示={joined}",
            f"blind_school·morph_hints={joined}",
            f"맹파·형변_힌트={joined}",
        )

    def blind_llm_hint(self, hint: str) -> str:
        return self.t(
            f"盲派·语气提示={hint}",
            f"blind_school·tone_hint={hint}",
            f"맹파·톤_힌트={hint}",
        )

    def blind_spatial_gate(self, lw: str) -> str:
        return self.t(
            f"盲派·空间闸口={lw}",
            f"blind_school·spatial_gate={lw}",
            f"맹파·공간_게이트={lw}",
        )

    def mandatory_synthesis_role(self) -> str:
        return self.t(
            "【终审语义素材 · 内化专用】\n"
            "下列块仅供压缩写入你最终 JSON 的 verdict_body（### 核心气象 / ### 裁决共识 / ### 行为指引 之下）；\n"
            "禁止在本轮回答中单独输出下列 Markdown 长文或脱离 JSON 的先导段落；整轮回答仍须仅为一颗 JSON 对象。\n"
            "素材范围仅限块内已出现的干支与标签句，不得发明未出现事实。\n",
            "[MANDATORY_FINAL_SYNTHESIS · internal]\n"
            "The blocks below are only to be compressed into your final JSON verdict_body (under ### Core climate / "
            "### Verdict consensus / ### Behavioral guidance);\n"
            "do not emit standalone Markdown essays or preambles outside JSON; the entire reply must remain a single JSON object.\n"
            "Use only stems/branches and tag lines already present in the blocks; do not invent unseen facts.\n",
            "[MANDATORY_FINAL_SYNTHESIS · 내부용]\n"
            "아래 블록은 최종 JSON verdict_body(### 핵심 기상 / ### 판정 합의 / ### 행동 지침 하위)에 압축 반영할 재료일 뿐입니다.\n"
            "이번 응답에서 아래를 단독 Markdown 장문으로 출력하거나 JSON 밖 서문을 두지 마십시오. 전체 응답은 JSON 객체 하나여야 합니다.\n"
            "블록에 이미 있는 간지·태그 문장만 사용하고, 미등장 사실을 발명하지 마십시오.\n",
        )

    def mandatory_pillars_title(self) -> str:
        return self.t(
            "[核心四柱 pillars JSON]\n",
            "[core_pillars · pillars JSON]\n",
            "[핵심_사주 · pillars JSON]\n",
        )

    def mandatory_conflict_title(self) -> str:
        return self.t(
            "[物理芯片冲突点 conflict_matrix.points]\n",
            "[physics_chip_conflicts · conflict_matrix.points]\n",
            "[물리_칩_충돌 · conflict_matrix.points]\n",
        )

    def mandatory_conflict_empty(self) -> str:
        return self.t("- （无结构化冲突点）\n", "- (no structured conflict points)\n", "- (구조화된 충돌점 없음)\n")

    def mandatory_semantic_verdicts_title(self) -> str:
        return self.t(
            "[用户已确认语义断言 persistence_layer.semantic_verdicts]\n",
            "[user_confirmed_semantic_assertions · persistence_layer.semantic_verdicts]\n",
            "[사용자_확인_의미_단언 · persistence_layer.semantic_verdicts]\n",
        )

    def mandatory_semantic_verdicts_empty(self) -> str:
        return self.t(
            "- （暂无已归档断语；仍须基于标签材料给出终审式整合结论）\n",
            "- (no archived lines yet; still produce a final-style integrated conclusion from tag materials.)\n",
            "- (보관 문구 없음; 태그 재료로 최종형 통합 결론을 제시하십시오.)\n",
        )

    def mandatory_physics_audit_title(self) -> str:
        return self.t(
            "[物理审计摘要（physics_tensor 顶层）]\n",
            "[physics_audit_digest · physics_tensor top-level]\n",
            "[물리_감사_요약 · physics_tensor 최상위]\n",
        )

    def structure_physics_constraint(self) -> str:
        return self.t(
            "[PHYSICS_CONSTRAINT] 必须推荐泄耗（克/泄），严禁推荐生扶（印比）",
            "[PHYSICS_CONSTRAINT] Prefer drain (control/output); forbid recommending nourish (resource/peer).",
            "[PHYSICS_CONSTRAINT] 설·극(克/泄)로 소모 우선; 인·비(印比) 생보 추천 금지.",
        )

    def structure_blind_work_constraint(self) -> str:
        return self.t(
            "[BLIND_WORK_CONSTRAINT] 必须判定做功效率低下，强调内耗风险与开库/冲动机会",
            "[BLIND_WORK_CONSTRAINT] State low work efficiency; stress inner-loss risk and tomb/unlock opportunities.",
            "[BLIND_WORK_CONSTRAINT] 작업 효율 저하를 판정하고 내부 소모·개고/충동 기회를 강조.",
        )

    def structure_body_damage_constraint(self) -> str:
        return self.t(
            "[BODY_DAMAGE_CONSTRAINT] 存在CRITICAL_STRESS节点，必须说明“贪财坏印/禄神受损”的物理代价",
            "[BODY_DAMAGE_CONSTRAINT] CRITICAL_STRESS present; explain physical cost (e.g. wealth-hurts-resource / lu damage).",
            "[BODY_DAMAGE_CONSTRAINT] CRITICAL_STRESS 존재; 탐재환인/록신 손상 등 물리 대가를 설명.",
        )

    def school_balance_fallback(self) -> str:
        return self.t("[BALANCE_SCHOOL] 未提供", "[BALANCE_SCHOOL] missing", "[BALANCE_SCHOOL] 없음")

    def school_work_fallback(self) -> str:
        return self.t("[WORK_SCHOOL] 未提供", "[WORK_SCHOOL] missing", "[WORK_SCHOOL] 없음")

    def school_logic_conflict_fallback(self) -> str:
        return self.t("[LOGIC_CONFLICT_WARNING]", "[LOGIC_CONFLICT_WARNING]", "[LOGIC_CONFLICT_WARNING]")

    def structure_self_abs_redacted(self) -> str:
        return self.t(
            "structure.self_abs=(Self_Abs 数值已省略；档位见 Verified Facts)",
            "structure.self_abs=(Self_Abs omitted; band in Verified Facts)",
            "structure.self_abs=(Self_Abs 생략; 구간은 Verified Facts)",
        )

    def structure_root_redacted(self) -> str:
        return self.t(
            "structure.root_score=(数值已省略)",
            "structure.root_score=(numeric omitted)",
            "structure.root_score=(수치 생략)",
        )

    def strategic_breakthrough_recommendation(self, first_action: str, old_rec: str) -> str:
        prefix = self.t("先破局：", "Break first: ", "선제 돌파:")
        then = self.t(" 然后：", " Then: ", " 이후:")
        return prefix + first_action + (then + old_rec if old_rec else "")
