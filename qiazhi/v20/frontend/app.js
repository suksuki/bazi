const state = {
  latest: null,
  activeProfile: null,
  measureTimer: null,
  isMeasuring: false,
  pendingMeasure: false,
  lastMeasureKey: "",
  chatTurns: [],
  chatSeq: 0,
  activeLlmMode: "practitioner",
  practitionerSelections: [],
  latentManifest: null,
  latentAnswers: [],
  answeredQuestionIds: [],
  answeredQuestionKeys: [],
  chartMemoryKey: "",
  answerWriter: { timer: null, queue: "", displayed: "" },
  isBatchUpdating: false,
};

const STEM_META = {
  甲: { element: "wood", polarity: "yang" },
  乙: { element: "wood", polarity: "yin" },
  丙: { element: "fire", polarity: "yang" },
  丁: { element: "fire", polarity: "yin" },
  戊: { element: "earth", polarity: "yang" },
  己: { element: "earth", polarity: "yin" },
  庚: { element: "metal", polarity: "yang" },
  辛: { element: "metal", polarity: "yin" },
  壬: { element: "water", polarity: "yang" },
  癸: { element: "water", polarity: "yin" },
};

const BRANCH_META = {
  子: { element: "water", polarity: "yang" },
  丑: { element: "earth", polarity: "yin" },
  寅: { element: "wood", polarity: "yang" },
  卯: { element: "wood", polarity: "yin" },
  辰: { element: "earth", polarity: "yang" },
  巳: { element: "fire", polarity: "yin" },
  午: { element: "fire", polarity: "yang" },
  未: { element: "earth", polarity: "yin" },
  申: { element: "metal", polarity: "yang" },
  酉: { element: "metal", polarity: "yin" },
  戌: { element: "earth", polarity: "yang" },
  亥: { element: "water", polarity: "yin" },
};

const STEMS_LIST = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"];
const BRANCHES_LIST = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"];
const yearToGanZhi = (year) => {
  const y = Number(year);
  if (!y || y < 1900) return "";
  const stemIndex = (y - 4) % 10;
  const branchIndex = (y - 4) % 12;
  return STEMS_LIST[stemIndex < 0 ? stemIndex + 10 : stemIndex] + BRANCHES_LIST[branchIndex < 0 ? branchIndex + 12 : branchIndex];
};

const params = new URLSearchParams(window.location.search);

const form = document.querySelector("#measureForm");
const questionSelect = document.querySelector("#questionSelect");
const questionIdInput = document.querySelector("#questionId");
const roleSelect = document.querySelector("#roleSelect");
const localeSelect = document.querySelector("#localeSelect");
const chatText = document.querySelector("#chatText");
const chatButton = document.querySelector("#chatButton");
const chatTranscript = document.querySelector("#chatTranscript");
const logoutButton = document.querySelector("#logoutButton");

const UI_TEXT = {
  zh: {
    app_title: "命理测算台", nav_profiles: "档案", nav_measure: "测算", logout_button: "登出",
    pillars_form_title: "四柱", year_pillar: "年柱", month_pillar: "月柱", day_pillar: "日柱", hour_pillar: "时柱",
    user_focus: "用户关心", recommended_question: "推荐问题", flow_year: "流年", luck_pillar: "大运", flow_month: "流月",
    profile_title: "档案", profile_manage: "档案管理", selected_waiting: "等待测算",
    feature_metric: "特征态", intent_metric: "意图", evidence_metric: "证据", practitioner_title: "命理师校准",
    default_user_text: "我想看事业和财运",
    chart_title: "命盘结构", features_title: "八字特征状态", portrait_title: "主题投射画像",
    questions_title: "智能问题", hits_title: "规则命中", answer_title: "八字专业回复",
    evidence_title: "证据锚点", feedback_title: "反馈校准",
    run: "开始测算", running: "测算中",
    roles: { user: "普通用户", analyst: "命理师", admin: "管理员" },
    dm: "日主", visible: "透出", hidden: "藏干",
    pillars: { year: "年柱", month: "月柱", day: "日柱", hour: "时柱", luck: "大运", flow_year: "流年" },
    pillar_hints: { year: "原局", month: "原局", day: "日主", hour: "原局", luck: "运势背景", flow_year: "当前触发" },
    states: { active: "已入主链", available: "可用", evidence_gap: "补证", requires_review: "复核", blocked_or_countered: "被反证", confirmed: "成立", candidate: "候选", weak_candidate: "弱候选", volatile: "岁运引动", mixed: "成而不纯", _: "状态" },
    domains: { strength: "强弱", career: "事业", wealth: "财运", ten_god: "十神", useful_god: "用神", time: "时间", branch: "地支", element: "五行", pattern: "格局", relationship: "关系", health: "健康", _: "命理" },
    temps: { hot: "高关注", warm: "成形", mild: "待复核", cool: "线索" },
    attn: { high: "高关注", medium: "重点观察", normal: "常规画像", _: "画像" },
    tiers: { micro: "微观骨架", decision: "裁决路径", macro: "应用场景", time: "时序引动", _: "结构层" },
    axis_states: { confirmed: "已成", chain_review: "链式", mixed: "成而不纯", candidate: "候选", weak_candidate: "偏弱", volatile: "引动", requires_review: "需复核", countered: "反制", blocked: "受阻", _: "结构" },
    intents: { confirm_structure: "确认结构", explore_candidate: "展开候选", collect_evidence: "补齐证据", resolve_mixed_state: "裁决混合", inspect_timing_trigger: "岁运引动", ask_practitioner_review: "命理师复核", explain_boundary: "边界说明", explore_structure: "结构追问", suppress_output: "不输出", _: "智能意图" },
    latent: { wealth: "财务变化", career: "事业节点", relationship: "关系重心", relocation: "环境迁移", stress: "压力恢复", global: "行动节奏", _: "命主校准" },
    latent_fields: { year_option: "时间", result_option: "结果", intensity: "强度", confidence: "把握" },
    latent_intensity: { none: "无", mild: "轻微", clear: "明显", strong: "强烈" },
    latent_confidence: { low: "低", medium: "中", high: "高" },
    latent_years: { unknown: "不确定", birth_to_12: "0-12岁", "13_to_18": "13-18岁", "19_to_24": "19-24岁", "25_to_30": "25-30岁", "31_to_36": "31-36岁", "37_to_42": "37-42岁", "43_to_48": "43-48岁", "49_to_54": "49-54岁", "55_plus": "55岁以后" },
    latent_results: { no_clear_change: "没有明显变化", income_up: "收入/资源上升", income_down: "收入下降", resource_gain: "获得资源支持", resource_pressure: "资源或财务压力", role_up: "角色上升", role_down: "角色下降", platform_change: "平台变化", responsibility_change: "责任变化", relationship_stabilized: "关系稳定", relationship_changed: "关系变化", relationship_pressure: "关系压力", family_focus_shift: "家庭重心变化", city_change: "城市变化", work_environment_change: "工作环境变化", home_environment_change: "居住环境变化", travel_or_mobility_up: "流动增加", stable: "基本稳定", recovered_fast: "恢复较快", recovered_slow: "恢复较慢", repeated_pressure: "压力反复", support_helped: "外部支持有效", not_observed: "尚未观察", result_fast: "见效快", result_slow: "见效慢", needs_repeated_attempts: "需要反复尝试", external_help_decisive: "外部帮助关键", mixed: "混合" },
    wb: { waiting: "等待测算。", measuring: "正在根据当前问题重新测算。", failed: "测算失败：", generating: "生成中", send: "发送", enter_dir: "请输入想继续看的方向。", chat_ph: "输入想继续看的方向", auto_route: "自动路由", no_features: "当前尚未发现可展示的命理特征。", no_portrait: "当前视图隐藏画像投影。", no_evidence: "暂无可展示证据。", no_questions: "确认四柱后会生成建议问题。", no_hits: "当前暂无规则命中。", no_rules: "未触发规则", await_graph: "等待画像图谱。", graph_ready: "当前盘已形成图谱画像。", mainline: "主线", pressure: "压力", timing: "时间", graph_default: "暂按主题画像展开", anchor: "结构锚点：", match_rate: "匹配率", cond_hit: "条件命中", dec_state: "决策态：", expand: "展开", collapse: "收起", prac_title: "命理师校准", prac_expand: "展开命理师校准", prac_collapse: "收起命理师校准", obs_expand: "展开观测页面", obs_collapse: "收起观测页面", pending: "待裁决", accepted: "已接收", recording: "记录中", rec_fail: "记录失败", rec_ok: "已记录 · 刷新问题", acc_ok: "已接收 · 刷新问题", q_source: "推荐问题", followup: "继续追问", manual: "手动测算", queuing: "排队中", chat_pending: "正在生成回复...", chat_empty: "本轮没有生成可展示回复。", calibrated: "已校准", dyn_val: "动态裁决验证", feat_model: "特征状态模型", q_model: "问题意图模型", def_model: "可反证裁决模型", hit_traces: "条规则命中轨迹", bazi: "命理测算", score: "分数", reviewed: "已审", draft: "草稿", states_count: "状态", intents_count: "意图", arguments_count: "论点", ready: "就绪", config: "配置", status_error: "状态错误", manifest_error: "清单错误", profile_unavailable: "档案不可用", profile_chart: "档案命盘", choice_only: "仅选择" },
  },
  en: {
    app_title: "Bazi Workbench", nav_profiles: "Profiles", nav_measure: "Reading", logout_button: "Log Out",
    pillars_form_title: "Four Pillars", year_pillar: "Year", month_pillar: "Month", day_pillar: "Day", hour_pillar: "Hour",
    user_focus: "Your Focus", recommended_question: "Suggested Question", flow_year: "Flow Year", luck_pillar: "Luck Cycle", flow_month: "Flow Month",
    profile_title: "Profile", profile_manage: "Manage Profiles", selected_waiting: "Awaiting Reading",
    feature_metric: "features", intent_metric: "intents", evidence_metric: "evidence", practitioner_title: "Practitioner Calibration",
    default_user_text: "I want to read career and wealth",
    chart_title: "Chart Structure", features_title: "Bazi Feature States", portrait_title: "Topic Projection",
    questions_title: "Smart Questions", hits_title: "Rule Hits", answer_title: "Professional Bazi Reply",
    evidence_title: "Evidence Anchors", feedback_title: "Feedback Calibration",
    run: "Run Reading", running: "Reading",
    roles: { user: "Regular User", analyst: "Practitioner", admin: "Admin" },
    dm: "DM", visible: "Visible", hidden: "Hidden",
    pillars: { year: "Year", month: "Month", day: "Day", hour: "Hour", luck: "Luck", flow_year: "Flow Year" },
    pillar_hints: { year: "natal", month: "natal", day: "day master", hour: "natal", luck: "luck cycle", flow_year: "current trigger" },
    states: { active: "mainline", available: "available", evidence_gap: "evidence gap", requires_review: "review", blocked_or_countered: "countered", confirmed: "confirmed", candidate: "candidate", weak_candidate: "weak", volatile: "volatile", mixed: "mixed", _: "state" },
    domains: { strength: "Capacity", career: "Career", wealth: "Wealth", ten_god: "Ten Gods", useful_god: "Useful God", time: "Timing", branch: "Branches", element: "Elements", pattern: "Pattern", relationship: "Relationship", health: "Health", _: "Bazi" },
    temps: { hot: "high focus", warm: "forming", mild: "review", cool: "signal" },
    attn: { high: "High Focus", medium: "Key Watch", normal: "Standard", _: "Profile" },
    tiers: { micro: "Micro Spine", decision: "Decision Path", macro: "Applied Scenario", time: "Timing Trigger", _: "Structure" },
    axis_states: { confirmed: "Confirmed", chain_review: "Chain", mixed: "Mixed", candidate: "Candidate", weak_candidate: "Weak", volatile: "Volatile", requires_review: "Review", countered: "Countered", blocked: "Blocked", _: "Structure" },
    intents: { confirm_structure: "Confirm Structure", explore_candidate: "Explore Candidate", collect_evidence: "Collect Evidence", resolve_mixed_state: "Resolve Mixed", inspect_timing_trigger: "Timing Trigger", ask_practitioner_review: "Practitioner Review", explain_boundary: "Boundary", explore_structure: "Explore Structure", suppress_output: "Suppress", _: "Intent" },
    latent: { wealth: "Financial Change", career: "Career Node", relationship: "Relationship Focus", relocation: "Relocation", stress: "Stress Recovery", global: "Action Rhythm", _: "Subject Calibration" },
    latent_fields: { year_option: "Period", result_option: "Result", intensity: "Intensity", confidence: "Confidence" },
    latent_intensity: { none: "None", mild: "Mild", clear: "Clear", strong: "Strong" },
    latent_confidence: { low: "Low", medium: "Medium", high: "High" },
    latent_years: { unknown: "Uncertain", birth_to_12: "0–12", "13_to_18": "13–18", "19_to_24": "19–24", "25_to_30": "25–30", "31_to_36": "31–36", "37_to_42": "37–42", "43_to_48": "43–48", "49_to_54": "49–54", "55_plus": "55+" },
    latent_results: { no_clear_change: "No clear change", income_up: "Income up", income_down: "Income down", resource_gain: "Resource gained", resource_pressure: "Resource pressure", role_up: "Role up", role_down: "Role down", platform_change: "Platform change", responsibility_change: "Responsibility change", relationship_stabilized: "Relationship stable", relationship_changed: "Relationship changed", relationship_pressure: "Relationship pressure", family_focus_shift: "Family shift", city_change: "City change", work_environment_change: "Work env change", home_environment_change: "Home env change", travel_or_mobility_up: "Mobility up", stable: "Mostly stable", recovered_fast: "Fast recovery", recovered_slow: "Slow recovery", repeated_pressure: "Repeated pressure", support_helped: "Support helped", not_observed: "Not observed", result_fast: "Quick results", result_slow: "Slow results", needs_repeated_attempts: "Repeated attempts", external_help_decisive: "External help key", mixed: "Mixed" },
    wb: { waiting: "Awaiting reading.", measuring: "Re-reading based on current question.", failed: "Reading failed: ", generating: "Generating", send: "Send", enter_dir: "Enter a direction to explore.", chat_ph: "Enter a direction to explore", auto_route: "Auto Route", no_features: "No displayable Bazi features found yet.", no_portrait: "Portrait projection hidden in this view.", no_evidence: "No evidence to display.", no_questions: "Suggested questions appear after confirming four pillars.", no_hits: "No rule hits yet.", no_rules: "No rules fired", await_graph: "Awaiting portrait graph.", graph_ready: "Portrait graph ready.", mainline: "Mainline", pressure: "Pressure", timing: "Timing", graph_default: "Expand by topic portrait", anchor: "Structural anchor: ", match_rate: "match", cond_hit: "Conditions met", dec_state: "Decision: ", expand: "Expand", collapse: "Collapse", prac_title: "Practitioner Calibration", prac_expand: "Expand practitioner calibration", prac_collapse: "Collapse practitioner calibration", obs_expand: "Expand observation page", obs_collapse: "Collapse observation page", pending: "pending", accepted: "accepted", recording: "recording", rec_fail: "record failed", rec_ok: "recorded · refreshing", acc_ok: "accepted · refreshing", q_source: "Suggested", followup: "Follow-up", manual: "Manual Reading", queuing: "queuing", chat_pending: "Generating reply…", chat_empty: "No displayable reply this turn.", calibrated: "calibrated", dyn_val: "Decision Validation", feat_model: "Feature State Model", q_model: "Question Intent Model", def_model: "Defeasible Decision Model", hit_traces: "rule hit traces", bazi: "Bazi Reading", score: "score", reviewed: "reviewed", draft: "draft", states_count: "states", intents_count: "intents", arguments_count: "arguments", ready: "ready", config: "config", status_error: "status error", manifest_error: "manifest error", profile_unavailable: "profile unavailable", profile_chart: "profile chart", choice_only: "choice only" },
  },
  ko: {
    app_title: "사주 분석 작업대", nav_profiles: "프로필", nav_measure: "분석", logout_button: "로그아웃",
    pillars_form_title: "사주팔자", year_pillar: "연주", month_pillar: "월주", day_pillar: "일주", hour_pillar: "시주",
    user_focus: "관심 주제", recommended_question: "추천 질문", flow_year: "세운", luck_pillar: "대운", flow_month: "월운",
    profile_title: "프로필", profile_manage: "프로필 관리", selected_waiting: "분석 대기",
    feature_metric: "특징", intent_metric: "의도", evidence_metric: "근거", practitioner_title: "명리사 보정",
    default_user_text: "직업과 재운을 보고 싶어요",
    chart_title: "명식 구조", features_title: "사주 특징 상태", portrait_title: "주제 투사",
    questions_title: "지능형 질문", hits_title: "규칙 적중", answer_title: "전문 사주 답변",
    evidence_title: "근거 앵커", feedback_title: "피드백 보정",
    run: "분석 시작", running: "분석 중",
    roles: { user: "일반 사용자", analyst: "명리사", admin: "관리자" },
    dm: "일간", visible: "투출", hidden: "장간",
    pillars: { year: "연주", month: "월주", day: "일주", hour: "시주", luck: "대운", flow_year: "유년" },
    pillar_hints: { year: "원국", month: "원국", day: "일간", hour: "원국", luck: "운세 배경", flow_year: "현재 촉발" },
    states: { active: "주요 연결", available: "가용", evidence_gap: "근거 부족", requires_review: "검토", blocked_or_countered: "반증", confirmed: "성립", candidate: "후보", weak_candidate: "약후보", volatile: "세운 변동", mixed: "혼합", _: "상태" },
    domains: { strength: "강약", career: "직업", wealth: "재운", ten_god: "십성", useful_god: "용신", time: "시간", branch: "지지", element: "오행", pattern: "격국", relationship: "관계", health: "건강", _: "사주" },
    temps: { hot: "높은 관심", warm: "형성", mild: "검토", cool: "단서" },
    attn: { high: "높은 관심", medium: "주요 관찰", normal: "일반", _: "프로필" },
    tiers: { micro: "미시 구조", decision: "판정 경로", macro: "응용 시나리오", time: "시간 촉발", _: "구조층" },
    axis_states: { confirmed: "성립", chain_review: "연쇄", mixed: "혼합", candidate: "후보", weak_candidate: "약세", volatile: "변동", requires_review: "검토", countered: "반제", blocked: "차단", _: "구조" },
    intents: { confirm_structure: "구조 확인", explore_candidate: "후보 탐색", collect_evidence: "근거 보완", resolve_mixed_state: "혼합 판정", inspect_timing_trigger: "세운 촉발", ask_practitioner_review: "명리사 검토", explain_boundary: "경계 설명", explore_structure: "구조 추적", suppress_output: "출력 안 함", _: "의도" },
    latent: { wealth: "재무 변화", career: "직업 전환", relationship: "관계 중심", relocation: "환경 이동", stress: "스트레스 회복", global: "행동 리듬", _: "주체 보정" },
    latent_fields: { year_option: "시기", result_option: "결과", intensity: "강도", confidence: "확신" },
    latent_intensity: { none: "없음", mild: "경미", clear: "뚜렷", strong: "강함" },
    latent_confidence: { low: "낮음", medium: "중간", high: "높음" },
    latent_years: { unknown: "불확실", birth_to_12: "0-12세", "13_to_18": "13-18세", "19_to_24": "19-24세", "25_to_30": "25-30세", "31_to_36": "31-36세", "37_to_42": "37-42세", "43_to_48": "43-48세", "49_to_54": "49-54세", "55_plus": "55세 이후" },
    latent_results: { no_clear_change: "변화 없음", income_up: "수입 상승", income_down: "수입 감소", resource_gain: "자원 확보", resource_pressure: "자원 압력", role_up: "역할 상승", role_down: "역할 하락", platform_change: "플랫폼 변화", responsibility_change: "책임 변화", relationship_stabilized: "관계 안정", relationship_changed: "관계 변화", relationship_pressure: "관계 압력", family_focus_shift: "가정 변화", city_change: "도시 변경", work_environment_change: "근무 환경 변화", home_environment_change: "주거 환경 변화", travel_or_mobility_up: "이동 증가", stable: "안정", recovered_fast: "빠른 회복", recovered_slow: "느린 회복", repeated_pressure: "반복 압력", support_helped: "외부 지원 효과", not_observed: "미관찰", result_fast: "빠른 성과", result_slow: "느린 성과", needs_repeated_attempts: "반복 시도", external_help_decisive: "외부 도움 결정적", mixed: "혼합" },
    wb: { waiting: "분석 대기 중.", measuring: "현재 질문 기반으로 재분석 중.", failed: "분석 실패: ", generating: "생성 중", send: "보내기", enter_dir: "탐색 방향을 입력하세요.", chat_ph: "탐색 방향을 입력하세요", auto_route: "자동 라우팅", no_features: "표시 가능한 사주 특징이 없습니다.", no_portrait: "현재 뷰에서 투사가 숨겨져 있습니다.", no_evidence: "표시할 근거가 없습니다.", no_questions: "사주 확인 후 추천 질문이 생성됩니다.", no_hits: "규칙 적중 없음.", no_rules: "촉발된 규칙 없음", await_graph: "프로필 그래프 대기 중.", graph_ready: "그래프가 준비되었습니다.", mainline: "주요 축", pressure: "압력", timing: "시간", graph_default: "주제별로 전개", anchor: "구조 앵커: ", match_rate: "일치율", cond_hit: "조건 충족", dec_state: "판정: ", expand: "열기", collapse: "닫기", prac_title: "명리사 보정", prac_expand: "명리사 보정 열기", prac_collapse: "명리사 보정 닫기", obs_expand: "관측 열기", obs_collapse: "관측 닫기", pending: "대기 중", accepted: "접수됨", recording: "기록 중", rec_fail: "기록 실패", rec_ok: "기록됨 · 질문 갱신", acc_ok: "접수됨 · 질문 갱신", q_source: "추천 질문", followup: "추가 질문", manual: "수동 분석", queuing: "대기 중", chat_pending: "답변 생성 중…", chat_empty: "표시할 답변이 없습니다.", calibrated: "보정 완료", dyn_val: "동적 판정 검증", feat_model: "특징 상태 모델", q_model: "질문 의도 모델", def_model: "반증 판정 모델", hit_traces: "규칙 적중 이력", bazi: "사주 분석", score: "점수", reviewed: "검토됨", draft: "초안", states_count: "상태", intents_count: "의도", arguments_count: "논점", ready: "준비됨", config: "설정", status_error: "상태 오류", manifest_error: "목록 오류", profile_unavailable: "프로필을 불러올 수 없음", profile_chart: "프로필 명식", choice_only: "선택만" },
  },
};

const setText = (selector, value) => {
  const node = document.querySelector(selector);
  if (node) node.textContent = value ?? "";
};

const requestJson = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${detail}`);
  }
  return response.json();
};

const clear = (node) => {
  while (node.firstChild) node.removeChild(node.firstChild);
};

const el = (tag, className = "", text = "") => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
};

const plainAnswerText = (value) => {
  const text = String(value || "").trim();
  if (!text) return "";
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed.text === "string") return parsed.text.trim();
  } catch (_) {
    // Keep streaming text if it is not a complete JSON object yet.
  }
  return text
    .replace(/^\s*\{\s*"text"\s*:\s*"?/, "")
    .replace(/"?\s*\}\s*$/, "")
    .trim();
};

const startAnswerTypewriter = () => {
  stopAnswerTypewriter();
  state.answerWriter = { timer: null, queue: "", displayed: "" };
  setText("#answerText", "");
  state.answerWriter.timer = window.setInterval(tickAnswerTypewriter, 14);
};

const queueAnswerText = (text) => {
  if (!state.answerWriter.timer) startAnswerTypewriter();
  const combined = `${state.answerWriter.displayed}${state.answerWriter.queue}${text || ""}`;
  const cleaned = plainAnswerText(combined);
  state.answerWriter.queue = cleaned.slice(state.answerWriter.displayed.length);
};

const finishAnswerTypewriter = () => {
  if (state.answerWriter.queue) {
    window.setTimeout(finishAnswerTypewriter, 40);
    return;
  }
  stopAnswerTypewriter();
};

const stopAnswerTypewriter = () => {
  if (state.answerWriter?.timer) window.clearInterval(state.answerWriter.timer);
  state.answerWriter = { timer: null, queue: state.answerWriter?.queue || "", displayed: state.answerWriter?.displayed || "" };
};

const tickAnswerTypewriter = () => {
  const writer = state.answerWriter;
  if (!writer.queue) return;
  const take = Math.min(3, writer.queue.length);
  writer.displayed += writer.queue.slice(0, take);
  writer.queue = writer.queue.slice(take);
  setText("#answerText", writer.displayed);
};

const requestMeasureStream = async (url, payload, handlers = {}) => {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok || !response.body) {
    const detail = await response.text();
    throw new Error(`${response.status} ${detail}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let latestResult = null;
  let finalAnswer = "";
  const handleBlock = (block) => {
    const event = (block.match(/^event:\s*(.+)$/m) || [])[1] || "message";
    const data = block
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart())
      .join("\n");
    if (!data) return;
    const payload = JSON.parse(data);
    if (event === "runtime") {
      latestResult = payload.result || null;
      handlers.onRuntime?.(latestResult);
    } else if (event === "delta") {
      const text = payload.text || "";
      finalAnswer += text;
      handlers.onDelta?.(text);
    } else if (event === "done") {
      finalAnswer = plainAnswerText(payload.answer_text || finalAnswer);
      handlers.onDone?.({ ...payload, answer_text: finalAnswer });
    } else if (event === "error") {
      throw new Error(payload.message || "stream_error");
    }
  };
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    blocks.forEach((block) => block.trim() && handleBlock(block));
  }
  if (buffer.trim()) handleBlock(buffer);
  if (latestResult && finalAnswer) latestResult.answer_text = finalAnswer;
  if (latestResult && finalAnswer) latestResult.answer_text = plainAnswerText(finalAnswer);
  return latestResult;
};

const measure = async ({ force = false, interactionText = "", interactionSource = "", llmMode = "deterministic" } = {}) => {
  syncQuestionIdFromSelect();
  const text = currentText();
  const payload = payloadFromForm();
  syncQuestionMemory(payload);
  payload.llm_mode = llmMode;
  payload.practitioner_selections = state.practitionerSelections;
  payload.latent_event_answers = state.latentAnswers;
  payload.answered_question_ids = state.answeredQuestionIds;
  payload.answered_question_keys = state.answeredQuestionKeys;
  const key = JSON.stringify(payload);
  if (!force && key === state.lastMeasureKey) return;
  if (!hasCompletePillars(payload)) return;
  if (state.isMeasuring) {
    state.pendingMeasure = true;
    setText("#llmStatus", text.wb.queuing);
    return;
  }
  state.isMeasuring = true;
  state.lastMeasureKey = key;
  state.activeLlmMode = llmMode;
  const turnId = interactionText ? appendChatTurn(interactionText, interactionSource || text.wb.q_source) : "";
  setMeasureBusy(true, text, llmMode);
  setText("#answerText", text.wb.measuring);
  try {
    const role = measurementRole(payload.role_key);
    delete payload.role_key;
    const endpoint = `/api/v20/measure/view/${role}`;
    const isStreaming = llmMode === "practitioner";
    const result = isStreaming
      ? await requestMeasureStream(`${endpoint}/stream`, payload, {
          onRuntime: (runtime) => {
            state.latest = runtime;
            renderRuntime(runtime);
            startAnswerTypewriter();
            setText("#llmStatus", "llm streaming");
          },
          onDelta: (text) => queueAnswerText(text),
          onDone: () => finishAnswerTypewriter(),
        })
      : await requestJson(endpoint, {
          method: "POST",
          body: JSON.stringify(payload),
        });
    if (!result) throw new Error("stream returned no runtime result");
    finishAnswerTypewriter();
    state.latest = result;
    if (!isStreaming) renderRuntime(result);
    if (turnId) completeChatTurn(turnId, result.answer_text || "", result);
  } catch (error) {
    console.error("Measurement execution failed:", error);
    stopAnswerTypewriter();
    setText("#answerText", `${currentText().wb.failed}${error.message}`);
    if (turnId) failChatTurn(turnId, error.message);
    state.lastMeasureKey = "";
  } finally {
    state.isMeasuring = false;
    setMeasureBusy(false, currentText(), state.activeLlmMode);
    if (state.pendingMeasure) {
      state.pendingMeasure = false;
      scheduleMeasure({ force: true });
    }
  }
};

const scheduleMeasure = ({ force = false } = {}) => {
  if (state.isBatchUpdating && !force) return;
  clearTimeout(state.measureTimer);
  state.measureTimer = setTimeout(() => measure({ force }), 280);
};

const interactiveLlmMode = () => (params.get("llm") === "deterministic" ? "deterministic" : "practitioner");

const renderRuntime = (result) => {
  const selected = result.selected_question || {};
  const chart = result.chart_facts || {};
  const featureLayer = result.feature_layer || {};
  const decisionReport = result.decision_report || {};
  const featureStateModel = result.feature_state_model || {};
  const questionIntentModel = result.question_intent_model || {};
  const portraitProjection = decisionReport.portrait_projection || {};
  const role = result.role?.role_key || measurementRole(roleSelect.value);
  const selectedQuestionId = selected.question_id || "";
  if (questionIdInput) questionIdInput.value = selectedQuestionId;

  // Preserve guest role on body for CSS layout; use measurement role for access control
  if (params.get("role") !== "guest") document.body.dataset.role = role;
  renderObservationAccess(role);
  renderFeatureStateAccess(role);
  setText("#selectedQuestion", selected.title || selected.question_key || currentText().running);
  setText("#selectedBoundary", selected.boundary || result.prediction_policy?.core_focus || "");
  setText("#featureCount", featureStateModel.feature_state_count ?? decisionReport.decision_count ?? featureLayer.feature_count ?? 0);
  setText("#questionCount", questionIntentModel.intent_count ?? (result.questions || []).length);
  setText("#knowledgeCount", result.knowledge_report?.count ?? 0);
  setText("#coreCapacity", featureStateModel.algorithm || result.core_inference?.day_master_capacity || "fusion");
  setText("#intentSummary", intentSummary(questionIntentModel));
  const t = currentText();
  setText("#dayMasterBadge", `${t.dm} ${chart.day_master || "-"}`);
  setText("#llmStatus", llmStatusLabel(result));
  setText("#answerText", result.answer_text || "");

  renderPillars(chart, result.time_context || {});
  renderTenGods(chart);
  renderFeatures(
    featureStateModel.priority_features ||
      featureStateModel.states ||
      decisionReport.mainlines ||
      decisionReport.decisions ||
      featureLayer.macro_features ||
      featureLayer.features ||
      []
  );
  renderPortraitGraph(result.portrait_graph_summary || {});
  renderPortrait(portraitProjection.axes || []);
  renderPractitionerCalibration(decisionReport.practitioner_controls || [], result.input_id || "", role);
  renderLatentCalibration(result.input_id || "", role);
  renderQuestions(result.questions || [], selectedQuestionId || selected.question_key || "", questionIntentModel);
  const runtimeDecisionHits = Array.isArray(decisionReport.rule_runtime_hits) ? decisionReport.rule_runtime_hits : [];
  renderDecisionHits(runtimeDecisionHits.length ? runtimeDecisionHits : (decisionReport.hits || []));
  renderQuestionSelect(result.questions || [], selectedQuestionId || selected.question_key || "");
  renderEvidence(
    result.knowledge_refs || [],
    result.decision_validation || {},
    {
      featureStateModel,
      questionIntentModel,
      decisionModel: decisionReport.defeasible_decision_model || {},
    }
  );
};

const renderObservationAccess = (role) => {
  const page = document.querySelector("#observationPage");
  const status = document.querySelector("#observationStatus");
  if (!page) return;
  const isAdmin = role === "admin";
  page.hidden = !isAdmin;
  if (status) status.textContent = isAdmin ? "管理员可见" : "仅管理员";
  setObservationCollapsed(page.classList.contains("collapsed"));
};

const renderFeatureStateAccess = (role) => {
  const panel = document.querySelector("#featureStatePanel");
  if (!panel) return;
  panel.hidden = role === "user";
};

const setObservationCollapsed = (collapsed) => {
  const page = document.querySelector("#observationPage");
  const body = document.querySelector("#observationBody");
  const toggle = document.querySelector("#observationToggle");
  const label = document.querySelector("#observationCollapseLabel");
  if (!page || !body || !toggle) return;
  page.classList.toggle("collapsed", collapsed);
  body.hidden = collapsed;
  toggle.setAttribute("aria-expanded", String(!collapsed));
  toggle.title = collapsed ? currentText().wb.obs_expand : currentText().wb.obs_collapse;
  if (label) label.textContent = collapsed ? currentText().wb.expand : currentText().wb.collapse;
};

const setMeasureBusy = (busy, text = currentText(), llmMode = "deterministic") => {
  const button = form.querySelector("button[type='submit']");
  button.disabled = busy;
  button.textContent = busy ? text.running : text.run;
  chatButton.disabled = busy;
  chatButton.textContent = busy ? text.wb.generating : text.wb.send;
  document.querySelectorAll(".question-row").forEach((node) => {
    node.disabled = busy;
  });
  if (busy) setText("#llmStatus", llmMode === "practitioner" ? "llm practitioner" : text.running);
};

const renderPillars = (chart = {}, timeContext = {}) => {
  const root = document.querySelector("#pillarPanel");
  clear(root);
  const keys = ["year", "month", "day", "hour"];
  const hasRealData = keys.some(k => chart.pillars?.[k]);
  const hasFallbackData = keys.some(k => {
    const v = String(form.elements[k]?.value || "").trim();
    return v.length >= 2 && !/^\d+$/.test(v);
  });
  if (!hasRealData && !hasFallbackData) return;

  const text = currentText();
  const pillars = chart.pillars || {};
  const timePillars = Object.fromEntries((timeContext.layers || []).map((layer) => [layer.layer_key, layer.pillar || {}]));
  ["year", "month", "day", "hour", "luck", "flow_year"].forEach((key) => {
    const pillar = pillars[key] || timePillars[key] || fallbackPillar(key);
    const card = el("div", `pillar-card ${key === "day" ? "active" : ""}`);
    const pillarLabel = (text.pillars && text.pillars[key]) ? text.pillars[key] : key;
    card.append(el("span", "", pillarLabel));
    card.append(pillarGlyph(pillar));
    card.append(el("em", "", text.pillar_hints[key] || ""));
    root.append(card);
  });
};

const pillarGlyph = (pillar) => {
  const stem = String(pillar.stem || "-").slice(0, 1);
  const branch = String(pillar.branch || "-").slice(0, 1);
  const glyph = el("strong", "pillar-glyph");
  glyph.append(pillarSymbol(stem, STEM_META[stem], "stem"));
  glyph.append(pillarSymbol(branch, BRANCH_META[branch], "branch"));
  return glyph;
};

const pillarSymbol = (value, meta = {}, layer) => {
  const node = el("b", "pillar-symbol", value || "-");
  node.dataset.layer = layer;
  node.dataset.element = meta.element || "unknown";
  node.dataset.polarity = meta.polarity || "neutral";
  return node;
};

const renderTenGods = (chart) => {
  const text = currentText();
  const visible = (chart.visible_ten_gods || []).map((row) => row.label).filter(Boolean);
  const hidden = (chart.hidden_ten_gods || []).map((row) => row.label).filter(Boolean);
  setText("#tenGodLine", `${text.visible} ${unique(visible).join(" / ") || "-"} · ${text.hidden} ${unique(hidden).slice(0, 6).join(" / ") || "-"}`);
};

const renderFeatures = (features) => {
  const root = document.querySelector("#featureChips");
  clear(root);
  if (!features.length) {
    root.append(el("div", "empty-note", currentText().wb.no_features));
    return;
  }
  features.slice(0, 10).forEach((feature) => {
    const card = el("div", "feature-card");
    card.dataset.domain = feature.domain || "general";
    card.dataset.state = feature.state || feature.status || "available";
    card.append(el("strong", "", feature.label || feature.title || feature.feature_id || feature.macro_id || "feature"));
    const score = feature.priority ?? feature.score ?? feature.discovery_score ?? feature.peak_confidence ?? feature.confidence ?? "-";
    const label = feature.domain || "domain";
    const stateLabel = featureStateLabel(feature.state || feature.status || feature.readiness);
    card.append(el("span", "", `${portraitDomainLabel(label)} · ${stateLabel} · ${currentText().wb.score} ${score}`));
    const links = [
      ...(feature.decision_keys || []),
      ...(feature.mainline_keys || []),
      ...(feature.portrait_axis_ids || []),
    ].filter(Boolean);
    if (links.length) card.append(el("p", "", links.slice(0, 3).join(" / ")));
    else if (feature.support) card.append(el("p", "", feature.support.slice(0, 3).join(" / ")));
    else if (feature.reason) card.append(el("p", "", feature.reason));
    else if (feature.summary) card.append(el("p", "", feature.summary));
    const hook = (feature.question_hooks || [feature.question_seed]).filter(Boolean)[0];
    if (hook) card.append(el("p", "feature-question-seed", hook));
    root.append(card);
  });
};

const renderPortraitGraph = (summary) => {
  const root = document.querySelector("#portraitGraphSummary");
  const status = document.querySelector("#portraitGraphStatus");
  if (!root) return;
  clear(root);
  if (status) status.textContent = summary.status || "profile";
  if (!summary || summary.status !== "ready") {
    root.append(el("div", "empty-note", currentText().wb.await_graph));
    return;
  }
  const wb = currentText().wb;
  root.append(el("p", "portrait-graph-headline", summary.headline || wb.graph_ready));
  const tagLine = el("div", "portrait-tag-line");
  (summary.profile_tags || []).slice(0, 8).forEach((tag) => tagLine.append(el("span", "portrait-tag-chip", tag)));
  if (tagLine.childNodes.length) root.append(tagLine);

  const columns = el("div", "portrait-graph-columns");
  [
    [wb.mainline, summary.strength_lines || []],
    [wb.pressure, summary.pressure_lines || []],
    [wb.timing, summary.timing_triggers || []],
  ].forEach(([title, rows]) => {
    const box = el("div", "portrait-graph-box");
    box.append(el("strong", "", title));
    const list = el("ul");
    (rows.length ? rows : [wb.graph_default]).slice(0, 3).forEach((row) => {
      const item = el("li", "", row);
      list.append(item);
    });
    box.append(list);
    columns.append(box);
  });
  root.append(columns);

  const questionLine = el("div", "portrait-graph-questions");
  (summary.suggested_questions || []).slice(0, 3).forEach((question) => {
    questionLine.append(el("span", "portrait-question-chip", question.title || question.question_key || currentText().recommended_question));
  });
  if (questionLine.childNodes.length) root.append(questionLine);
};

const featureStateLabel = (state) => {
  const t = currentText().states;
  return t[state] || state || t._ || "state";
};

const renderPortrait = (axes) => {
  const root = document.querySelector("#portraitAxes");
  clear(root);
  if (!axes.length) {
    root.append(el("div", "empty-note", currentText().wb.no_portrait));
    return;
  }
  axes.slice(0, 8).forEach((axis) => {
    const row = el("div", "axis-row");
    row.dataset.domain = axis.domain || "general";
    const axisTier = String(axis.axis_tier || "macro");
    row.dataset.tier = axisTier;
    const score = axis.score ?? axis.intelligence_score ?? axis.peak_confidence ?? axis.alignment_score ?? 0;
    const temperature = portraitTemperature(score);
    row.dataset.temperature = temperature.key;
    const title = el("div", "axis-title-line");
    title.append(el("strong", "", axis.label || axis.axis_id || currentText().wb.bazi));
    title.append(el("span", "axis-tag", axis.profile_tag || portraitDomainLabel(axis.domain)));
    title.append(el("span", `axis-temp ${temperature.key}`, portraitAttentionLabel(axis.attention_level, temperature.label)));
    const tierLabel = String(axis.axis_tier || "");
    if (tierLabel) {
      title.append(el("span", "axis-tier", axisTierLabel(tierLabel)));
    }
    const stateLabel = String(axis.axis_state || "");
    if (stateLabel) {
      title.append(el("span", "axis-state", axisStateLabel(stateLabel)));
    }
    row.append(title);
    row.append(el("span", "", axis.profile_summary || axis.summary || `${portraitDomainLabel(axis.domain)} · score ${score}`));
    const tags = (axis.profile_tags || []).filter(Boolean).slice(0, 5);
    if (tags.length) {
      const tagLine = el("div", "portrait-tag-line");
      tags.forEach((tag) => tagLine.append(el("span", "portrait-tag-chip", tag)));
      row.append(tagLine);
    }
    const seeds = (axis.question_seeds || []).filter(Boolean).slice(0, 2);
    const boundaries = (axis.evidence_boundaries || []).filter(Boolean).slice(0, 2);
    if (boundaries.length) row.append(el("p", "", boundaries.join(" / ")));
    else if (seeds.length) row.append(el("p", "", seeds.join(" / ")));
    const meter = el("i");
    meter.style.width = `${Math.round(Number(score || 0) * 100)}%`;
    const bar = el("div", "meter");
    bar.append(meter);
    row.append(bar);
    const anchor = String(axis.structural_anchor || "").trim();
    if (anchor) {
      row.append(el("p", "axis-anchor-line", `${currentText().wb.anchor}${anchor}`));
    }
    root.append(row);
  });
};

const portraitDomainLabel = (domain) => {
  const t = currentText().domains;
  return t[domain] || t._ || domain;
};

const portraitTemperature = (score) => {
  const t = currentText().temps;
  const value = Number(score || 0);
  if (value >= 0.78) return { key: "hot", label: t.hot };
  if (value >= 0.58) return { key: "warm", label: t.warm };
  if (value >= 0.38) return { key: "mild", label: t.mild };
  return { key: "cool", label: t.cool };
};

const portraitAttentionLabel = (level, fallback) => {
  const t = currentText().attn;
  return t[level] || fallback || t._ || "profile";
};

const axisTierLabel = (tier) => {
  const t = currentText().tiers;
  return t[tier] || t._ || tier;
};

const axisStateLabel = (state) => {
  const t = currentText().axis_states;
  return t[state] || t._ || state;
};

const renderPractitionerCalibration = (controls, inputId, role) => {
  const root = document.querySelector("#practitionerCalibration");
  const list = document.querySelector("#calibrationControls");
  const status = document.querySelector("#calibrationStatus");
  if (!root || !list || !status) return;
  clear(list);
  if (!["analyst", "admin"].includes(role) || !controls.length) {
    root.hidden = true;
    return;
  }
  root.hidden = false;
  status.textContent = practitionerSessionStatus();
  setPractitionerCollapsed(root.classList.contains("collapsed"));
  controls.slice(0, 4).forEach((control) => {
    const row = el("div", "calibration-control");
    row.append(el("strong", "", control.label || control.control_key || currentText().wb.prac_title));
    const options = el("div", "calibration-options");
    const selected = state.practitionerSelections.find((item) => item.control_key === control.control_key);
    (control.options || []).forEach((option) => {
      const button = el("button", "", option);
      button.type = "button";
      button.dataset.controlKey = control.control_key || "";
      button.dataset.option = option;
      if (option === control.default) button.classList.add("default");
      if (selected?.option === option) button.classList.add("selected");
      button.addEventListener("click", () => recordPractitionerCalibration(control, option, inputId, button));
      options.append(button);
    });
    row.append(options);
    list.append(row);
  });
};

const setPractitionerCollapsed = (collapsed) => {
  const root = document.querySelector("#practitionerCalibration");
  const body = document.querySelector("#calibrationControls");
  const toggle = document.querySelector("#practitionerToggle");
  const label = document.querySelector("#practitionerCollapseLabel");
  if (!root || !body || !toggle) return;
  root.classList.toggle("collapsed", collapsed);
  body.hidden = collapsed;
  toggle.setAttribute("aria-expanded", String(!collapsed));
  toggle.title = collapsed ? currentText().wb.prac_expand : currentText().wb.prac_collapse;
  if (label) label.textContent = collapsed ? currentText().wb.expand : currentText().wb.collapse;
};

const recordPractitionerCalibration = async (control, option, inputId, activeButton) => {
  const status = document.querySelector("#calibrationStatus");
  const sourceDecisionKeys = control.source_decision_keys || [];
  if (status) status.textContent = currentText().wb.recording;
  try {
    const result = await requestJson("/api/v20/practitioner/calibration/record", {
      method: "POST",
      body: JSON.stringify({
        input_id: inputId || state.latest?.input_id || "",
        source_role: "analyst",
        locale: localeSelect.value,
        selections: [{
          control_key: control.control_key,
          option,
          source_decision_keys: sourceDecisionKeys,
        }],
      }),
    });
    document.querySelectorAll(`.calibration-options button[data-control-key="${control.control_key}"]`).forEach((button) => {
      button.classList.toggle("selected", button === activeButton);
    });
    upsertPractitionerSelection(control, option);
    questionSelect.value = "";
    if (questionIdInput) questionIdInput.value = "";
    if (status) status.textContent = result.storage?.status === "stored" ? currentText().wb.rec_ok : currentText().wb.acc_ok;
    measure({ force: true, llmMode: "deterministic" });
  } catch (error) {
    if (status) status.textContent = currentText().wb.rec_fail;
  }
};

const upsertPractitionerSelection = (control, option) => {
  const selection = {
    control_key: control.control_key,
    option,
    source_decision_keys: control.source_decision_keys || [],
  };
  state.practitionerSelections = [
    ...state.practitionerSelections.filter((item) => item.control_key !== control.control_key),
    selection,
  ];
};

const renderLatentCalibration = (inputId, role) => {
  const root = document.querySelector("#latentCalibration");
  const list = document.querySelector("#latentCalibrationControls");
  const status = document.querySelector("#latentCalibrationStatus");
  if (!root || !list || !status) return;
  clear(list);
  const scenarios = state.latentManifest?.scenarios || [];
  if (role !== "admin" || !document.body.classList.contains("profile-reading") || !scenarios.length) {
    root.hidden = true;
    return;
  }
  root.hidden = false;
  status.textContent = state.latentAnswers.length ? `${currentText().wb.calibrated} ${state.latentAnswers.length}` : currentText().wb.choice_only;
  scenarios.slice(0, 4).forEach((scenario) => {
    const saved = state.latentAnswers.find((answer) => answer.scenario_id === scenario.scenario_id) || {};
    const row = el("div", "latent-calibration-row");
    const title = el("div", "latent-calibration-title");
    title.append(el("strong", "", latentScenarioTitle(scenario)));
    title.append(el("span", "", scenario.prompt || ""));
    row.append(title);
    const fields = el("div", "latent-calibration-fields");
    fields.append(latentSelect(scenario, "year_option", saved.year_option || "unknown", scenario.year_options || [], latentYearLabel));
    fields.append(latentSelect(scenario, "result_option", saved.result_option || (scenario.result_options || ["no_clear_change"])[0], scenario.result_options || [], latentResultLabel));
    fields.append(latentSelect(scenario, "intensity", saved.intensity || "clear", scenario.intensity_options || [], latentIntensityLabel));
    fields.append(latentSelect(scenario, "confidence", saved.confidence || "medium", scenario.confidence_options || [], latentConfidenceLabel));
    const button = el("button", "mini-action", saved.scenario_id ? currentText().wb.accepted : currentText().wb.recording);
    button.type = "button";
    button.addEventListener("click", () => recordLatentCalibration(scenario, inputId || state.latest?.input_id || "", role, row));
    fields.append(button);
    row.append(fields);
    list.append(row);
  });
};

const latentSelect = (scenario, key, selected, options, labeler) => {
  const label = el("label", "latent-field");
  label.append(el("span", "", latentFieldLabel(key)));
  const select = document.createElement("select");
  select.dataset.scenarioId = scenario.scenario_id || "";
  select.dataset.field = key;
  options.forEach((option) => {
    const node = document.createElement("option");
    node.value = option;
    node.textContent = labeler(option);
    select.append(node);
  });
  select.value = selected;
  label.append(select);
  return label;
};

const recordLatentCalibration = async (scenario, inputId, role, row) => {
  const status = document.querySelector("#latentCalibrationStatus");
  const answer = {
    scenario_id: scenario.scenario_id,
    year_option: row.querySelector('[data-field="year_option"]').value,
    result_option: row.querySelector('[data-field="result_option"]').value,
    intensity: row.querySelector('[data-field="intensity"]').value,
    confidence: row.querySelector('[data-field="confidence"]').value,
  };
  if (status) status.textContent = currentText().wb.recording;
  try {
    const result = await requestJson("/api/v20/latent-event/calibration/record", {
      method: "POST",
      body: JSON.stringify({
        input_id: inputId,
        source_role: ["analyst", "admin"].includes(role) ? "analyst" : "user",
        locale: localeSelect.value,
        answers: [answer],
      }),
    });
    upsertLatentAnswer(answer);
    questionSelect.value = "";
    if (questionIdInput) questionIdInput.value = "";
    if (status) status.textContent = result.storage?.status === "stored" ? currentText().wb.rec_ok : currentText().wb.acc_ok;
    measure({ force: true, llmMode: "deterministic" });
  } catch (error) {
    if (status) status.textContent = currentText().wb.rec_fail;
  }
};

const upsertLatentAnswer = (answer) => {
  state.latentAnswers = [
    ...state.latentAnswers.filter((item) => item.scenario_id !== answer.scenario_id),
    answer,
  ];
};

const renderQuestions = (questions, selectedId, questionIntentModel = {}) => {
  const root = document.querySelector("#questionList");
  clear(root);
  if (!questions.length) {
    root.append(el("div", "empty-note", currentText().wb.no_questions));
    return;
  }
  const activeId = String(selectedId || "");
  questions.slice(0, 8).forEach((question) => {
    root.append(questionButton(question, activeId, "question-row"));
  });
};

const renderDecisionHits = (hits = []) => {
  const root = document.querySelector("#decisionHits");
  const hitCount = document.querySelector("#decisionHitCount");
  const summary = document.querySelector("#decisionHitSummary");
  clear(root);
  if (summary) {
    clear(summary);
  }
  if (!hits.length) {
    if (hitCount) hitCount.textContent = `0 ${currentText().wb.hit_traces}`;
    if (summary) {
      summary.append(el("span", "small-pill", currentText().wb.no_rules));
    }
    root.append(el("div", "empty-note", currentText().wb.no_hits));
    return;
  }
  const statusBuckets = {};
  for (const hit of hits) {
    const status = String(hit.status || hit.match_status || "candidate");
    statusBuckets[status] = (statusBuckets[status] || 0) + 1;
  }
  const matched = hits.filter((hit) => hit.status === "matched" || hit.match_status === "matched");
  const partial = hits.filter((hit) => hit.status === "partial" || hit.match_status === "partial");
  const uncertain = hits.filter(
    (hit) => !["matched", "partial"].includes(hit.status) && !["matched", "partial"].includes(hit.match_status)
  );
  const orderedHits = [...matched, ...partial, ...uncertain]
    .sort((a, b) => {
      const scoreA = Number(a.match_score ?? a.score ?? 0);
      const scoreB = Number(b.match_score ?? b.score ?? 0);
      if (scoreA !== scoreB) return scoreB - scoreA;
      return String(a.rule_key || "").localeCompare(String(b.rule_key || ""));
    });
  if (hitCount) hitCount.textContent = `${orderedHits.length} ${currentText().wb.hit_traces}`;
  if (summary) {
    const orderedStatus = Object.entries(statusBuckets).sort((a, b) => b[1] - a[1]);
    orderedStatus.forEach(([label, count]) => {
      summary.append(el("span", "small-pill", `${label}: ${count}`));
    });
  }
  orderedHits.slice(0, 200).forEach((hit) => {
    const row = el("div", "rule-hit-row");
    const source = String(hit.source || "rulespec");
    const rawStatus = hit.status || hit.match_status || "candidate";
    const status = rawStatus === "candidate" ? (hit.match_status === "partial" ? "部分成立" : rawStatus) : rawStatus;
    const score = Number(hit.match_score ?? hit.score ?? 0);
    const matchText = `${currentText().wb.match_rate} ${(score * 100).toFixed(0)}%`;
    const statusText = `${status} · ${source}`;
    row.append(el("strong", "", hit.label || hit.rule_key || "规则"));
    const detail = `${hit.domain || "domain"} · ${statusText} · ${matchText}`;
    row.append(el("span", "", detail));
    if (hit.decision_key) {
      row.append(el("span", "rule-key", hit.decision_key));
    }
    if (hit.rule_key) {
      row.append(el("span", "rule-key", hit.rule_key));
    }
    const conditionInfo = Number.isFinite(Number(hit.matched_condition_count)) && Number(hit.condition_count)
      ? `${hit.matched_condition_count}/${hit.condition_count}`
      : "";
    if (conditionInfo) {
      row.append(el("span", "", `${currentText().wb.cond_hit} ${conditionInfo}`));
    }
    if (hit.missing_evidence && hit.missing_evidence.length) {
      row.append(el("p", "", hit.missing_evidence.filter(Boolean).slice(0, 2).join(" · ")));
    } else if (hit.evidence && hit.evidence.length) {
      row.append(el("p", "", hit.evidence.filter(Boolean).slice(0, 2).join(" · ")));
    }
    if (hit.decision_state && hit.decision_state !== "confirmed" && hit.domain) {
      row.append(el("p", "", `${currentText().wb.dec_state}${hit.decision_state}`));
    }
    root.append(row);
  });
};

const questionButton = (question, selectedId, className) => {
  const questionId = question.question_id || question.question_key || "";
  const isActive = String(selectedId) === String(questionId);
  const button = el("button", `${className}${isActive ? " active" : ""}`);
  button.type = "button";
  button.dataset.questionId = questionId;
  button.dataset.questionKey = question.question_key || "";
  button.append(el("strong", "", question.title || question.question_key || questionId || currentText().recommended_question));
  button.addEventListener("click", () => runQuestion(question));
  return button;
};

const intentSummary = (questionIntentModel = {}) => {
  const counts = questionIntentModel.intent_type_counts || {};
  const top = Object.entries(counts).sort((a, b) => Number(b[1]) - Number(a[1]))[0];
  return top ? `${intentTypeLabel(top[0])} ${top[1]}` : "intent";
};

const intentTypeLabel = (intentType) => {
  const t = currentText().intents;
  return t[intentType] || intentType || t._ || "intent";
};

const runQuestion = (question) => {
  const title = question.title || question.question_key || "";
  const questionId = question.question_id || "";
  rememberAnsweredQuestion(question);
  if (questionSelect) questionSelect.value = question.question_id || question.question_key || "";
  if (questionIdInput) questionIdInput.value = questionId;
  setInquiryText(title, { syncOnly: true });
  measure({
    force: true,
    interactionText: title,
    interactionSource: currentText().wb.q_source,
    llmMode: interactiveLlmMode(),
  });
};

const renderQuestionSelect = (questions, selectedId, selectedKey = "") => {
  const currentId = String(questionIdInput?.value || selectedId || "").trim();
  const optionValues = new Set();
  questionSelect.innerHTML = `<option value="">${currentText().wb.auto_route}</option>`;
  questions.forEach((question) => {
    const value = question.question_id || question.question_key || "";
    if (!value || optionValues.has(value)) return;
    optionValues.add(value);
    const option = document.createElement("option");
    option.value = value;
    option.dataset.questionId = value;
    option.dataset.questionKey = question.question_key || "";
    option.textContent = question.title || question.question_key;
    questionSelect.append(option);
  });
  const hasExactMatch = [...questionSelect.options].some((option) => option.value === currentId);
  if (currentId && hasExactMatch) {
    questionSelect.value = currentId;
    if (questionIdInput) questionIdInput.value = currentId;
    return;
  }
  if (selectedKey) {
    const byKey = [...questionSelect.options].find((option) => option.dataset.questionKey === selectedKey);
    if (byKey) {
      questionSelect.value = byKey.value;
      if (questionIdInput) questionIdInput.value = byKey.dataset.questionId || "";
      return;
    }
  }
  questionSelect.value = "";
  if (questionIdInput) questionIdInput.value = "";
};

const syncQuestionIdFromSelect = () => {
  if (!questionSelect || !questionIdInput) return;
  if (!questionSelect.value) {
    questionIdInput.value = "";
    return;
  }
  const selectedOption = questionSelect.selectedOptions[0];
  questionIdInput.value = selectedOption?.dataset?.questionId || questionSelect.value;
};

const renderEvidence = (refs, decisionValidation = {}, runtimeModels = {}) => {
  const root = document.querySelector("#evidenceList");
  clear(root);
  refs.slice(0, 5).forEach((ref) => {
    const row = el("div", "evidence-row");
    row.append(el("strong", "", ref.title || ref.knowledge_id || "knowledge"));
    row.append(el("span", "", `${portraitDomainLabel(ref.domain)} · ${ref.reviewed ? currentText().wb.reviewed : currentText().wb.draft}`));
    root.append(row);
  });
  if (decisionValidation.status) {
    const row = el("div", "evidence-row validation");
    row.append(el("strong", "", currentText().wb.dyn_val));
    row.append(el("span", "", `${decisionValidation.status} · ${decisionValidation.decision_count ?? 0}`));
    root.append(row);
  }
  const featureStateModel = runtimeModels.featureStateModel || {};
  const questionIntentModel = runtimeModels.questionIntentModel || {};
  const decisionModel = runtimeModels.decisionModel || {};
  [
    [currentText().wb.feat_model, featureStateModel.status, `${featureStateModel.feature_state_count ?? 0} ${currentText().wb.states_count}`],
    [currentText().wb.q_model, questionIntentModel.status, `${questionIntentModel.intent_count ?? 0} ${currentText().wb.intents_count}`],
    [currentText().wb.def_model, decisionModel.status, `${decisionModel.argument_count ?? 0} ${currentText().wb.arguments_count}`],
  ].forEach(([title, status, detail]) => {
    if (!status) return;
    const row = el("div", "evidence-row model");
    row.append(el("strong", "", title));
    row.append(el("span", "", `${status} · ${detail}`));
    root.append(row);
  });
  if (!refs.length && !decisionValidation.status && !featureStateModel.status) root.append(el("div", "empty-note", currentText().wb.no_evidence));
};

const appendChatTurn = (questionText, source) => {
  const id = `turn-${++state.chatSeq}`;
  state.chatTurns.push({
    id,
    source,
    questionText,
    answerText: currentText().wb.chat_pending,
    status: "pending",
    llmStatus: "llm generating",
  });
  renderChatTranscript();
  return id;
};

const completeChatTurn = (id, answerText, result) => {
  const turn = state.chatTurns.find((item) => item.id === id);
  if (!turn) return;
  turn.answerText = answerText || currentText().wb.chat_empty;
  turn.status = "ready";
  turn.llmStatus = llmStatusLabel(result);
  renderChatTranscript();
};

const failChatTurn = (id, message) => {
  const turn = state.chatTurns.find((item) => item.id === id);
  if (!turn) return;
  turn.answerText = `${currentText().wb.failed}${message}`;
  turn.status = "error";
  turn.llmStatus = "error";
  renderChatTranscript();
};

const renderChatTranscript = () => {
  if (!chatTranscript) return;
  clear(chatTranscript);
  if (!state.chatTurns.length) {
    chatTranscript.hidden = true;
    return;
  }
  chatTranscript.hidden = false;
  state.chatTurns.slice(-4).forEach((turn) => {
    const row = el("article", `chat-turn ${turn.status}`);
    const question = el("div", "chat-bubble user");
    question.append(el("span", "", turn.source || currentText().wb.q_source));
    question.append(el("strong", "", turn.questionText));
    const answer = el("div", "chat-bubble assistant");
    answer.append(el("span", "", turn.llmStatus || turn.status));
    answer.append(el("p", "", turn.answerText));
    row.append(question);
    row.append(answer);
    chatTranscript.append(row);
  });
};

const llmStatusLabel = (result) => {
  const assist = result?.llm_assist || {};
  const practitioner = assist.practitioner_answer || {};
  if (practitioner.status && practitioner.status !== "not_requested") return `llm practitioner ${practitioner.status}`;
  const rewrite = assist.answer_rewrite || {};
  if (rewrite.status && rewrite.status !== "not_requested") return `llm ${rewrite.status}`;
  return `llm ${assist.status || "idle"}`;
};

const latentScenarioTitle = (scenario) => {
  const t = currentText().latent;
  return t[scenario.domain] || t._ || scenario.domain;
};

const latentFieldLabel = (key) => {
  const t = currentText().latent_fields;
  return t[key] || key;
};

const latentYearLabel = (value) => {
  const t = currentText().latent_years;
  return t[value] || value;
};

const latentResultLabel = (value) => {
  const t = currentText().latent_results;
  return t[value] || value;
};

const latentIntensityLabel = (value) => {
  const t = currentText().latent_intensity;
  return t[value] || value;
};

const latentConfidenceLabel = (value) => {
  const t = currentText().latent_confidence;
  return t[value] || value;
};

const loadLatentCalibrationManifest = async () => {
  try {
    state.latentManifest = await requestJson("/api/v20/learning/latent-event-calibration");
    renderLatentCalibration(state.latest?.input_id || "", measurementRole(roleSelect.value));
  } catch (error) {
    const status = document.querySelector("#latentCalibrationStatus");
    if (status) status.textContent = currentText().wb.manifest_error;
  }
};



const loadCurrentSession = async () => {
  try {
    const result = await requestJson("/api/v20/auth/me");
    const session = result.session || {};
    if (result.authenticated && session.role) {
      const role = measurementRole(session.role);
      roleSelect.value = role;
      // Preserve guest role on body for CSS layout
      if (params.get("role") !== "guest") document.body.dataset.role = role;
      renderObservationAccess(role);
      renderFeatureStateAccess(role);
    }
    document.querySelectorAll(".admin-nav-link").forEach((node) => {
      node.hidden = session.role !== "admin";
    });
    if (logoutButton) logoutButton.hidden = !result.authenticated || params.get("role") === "guest";
  } catch (error) {
    document.querySelectorAll(".admin-nav-link").forEach((node) => {
      node.hidden = true;
    });
    if (logoutButton) logoutButton.hidden = true;
  }
};

const logout = async () => {
  await requestJson("/api/v20/auth/logout", {
    method: "POST",
    body: JSON.stringify({}),
  });
  window.location.href = `/v20/ui/?locale=${encodeURIComponent(localeSelect.value || "zh")}`;
};

const practitionerSessionStatus = () => {
  const session = state.latest?.practitioner_session || {};
  const wb = currentText().wb;
  if (!state.practitionerSelections.length) return wb.pending;
  if (session.questions_refreshed) return `${wb.accepted} ${session.selection_count || state.practitionerSelections.length}`;
  return wb.accepted;
};

const applyLocale = (locale) => {
  const text = UI_TEXT[locale] || UI_TEXT.zh;
  document.documentElement.lang = locale === "ko" ? "ko" : locale === "en" ? "en" : "zh-CN";
  document.querySelectorAll("[data-ui]").forEach((node) => {
    const key = node.dataset.ui;
    if (text[key]) node.textContent = text[key];
  });
  document.querySelectorAll("[data-ui-placeholder]").forEach((node) => {
    const key = node.dataset.uiPlaceholder;
    const value = text[key] || text.wb?.[key];
    if (value) node.setAttribute("placeholder", value);
  });
  const submit = form.querySelector("button[type='submit']");
  submit.textContent = text.run;
  chatButton.textContent = text.wb.send;
  if (chatText && !chatText.value.trim()) chatText.value = "";
  const userText = form.elements.user_text;
  if (userText && (!userText.value.trim() || Object.values(UI_TEXT).some((row) => row.default_user_text === userText.value.trim()))) {
    userText.value = text.default_user_text;
    if (chatText) chatText.value = text.default_user_text;
  }
  setText("#answerText", state.latest ? (state.latest.answer_text || text.wb.waiting) : text.wb.waiting);
  if (!state.latest) {
    setText("#selectedQuestion", text.selected_waiting);
  }
};

const renderInitialPanels = () => {
  renderObservationAccess(measurementRole(roleSelect.value));
  renderFeatureStateAccess(measurementRole(roleSelect.value));
  renderPillars({});
  renderFeatures([]);
  renderPortrait([]);
  renderPractitionerCalibration([], "", measurementRole(roleSelect.value));
  renderLatentCalibration("", measurementRole(roleSelect.value));
  renderQuestions([], "", {});
  renderEvidence([], {}, {});
};

const loadActiveProfile = async () => {
  const profileId = params.get("profile_id") || "";
  if (!profileId) return;
  document.querySelector("#selectedProfileCard").hidden = false;
  document.querySelector("#inputId").value = `profile:${profileId}`;
  setText("#selectedProfileName", params.get("profile_name") || profileId);
  const backParams = new URLSearchParams({ role: measurementRole(roleSelect.value), locale: localeSelect.value });
  document.querySelector("#backToProfiles").href = `/v20/ui/profiles.html?${backParams.toString()}`;
  try {
    const result = await requestJson(`/api/v20/profiles/${encodeURIComponent(profileId)}`);
    const profile = result.profile || {};
    state.activeProfile = profile;
    applyProfileDefaults(profile);
    setText("#selectedProfileName", profile.display_name || profile.profile_id || profileId);
    setText("#selectedProfileMeta", profileMeta(profile));
  } catch (error) {
    setText("#selectedProfileMeta", currentText().wb.profile_unavailable);
  }
};

const applyProfileDefaults = (profile) => {
  if (!profile) return;
  const f = document.querySelector("#measureForm");
  if (!f) {
    console.error("applyProfileDefaults: #measureForm not found!");
    return;
  }
  
  state.isBatchUpdating = true;
  try {
    const birth = profile.birth_input || {};
    const defaults = profile.chart_defaults || {};
    const pillars = defaults.pillars || {};
    const timePillars = defaults.time_pillars || {};

    const blackList = ["甲子", "戊辰", "甲午", "辛酉", "庚子", "乙亥", "辛丑"];
    const cleanPillar = (p) => (p && !blackList.includes(p)) ? p : "";

    const fields = [
      ["calendar", birth.calendar || birth.calendar_type || "solar"],
      ["lunar_is_leap", String(Boolean(birth.lunar_is_leap_month || birth.is_lunar_leap_month || birth.lunar_is_leap))],
      ["gender", birth.gender || "male"],
      ["year", birth.year || cleanPillar(pillars.year)],
      ["month", birth.month || cleanPillar(pillars.month)],
      ["day", birth.day || cleanPillar(pillars.day)],
      ["hour", birth.hour || cleanPillar(pillars.hour)],
      ["flow_year_pillar", cleanPillar(timePillars.flow_year)],
      ["luck_pillar", cleanPillar(timePillars.luck)],
    ];

    fields.forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (f.elements[key]) {
          const el = f.elements[key];
          // Only overwrite if profile provides a real value or current field is empty
          const current = String(el.value || "").trim();
          if (String(value).trim() || !current) {
            el.value = String(value);
          }
          el.dispatchEvent(new Event("change"));
        }
        // Sync segment controls
        if (key === "calendar") {
          document.querySelectorAll("[data-calendar]").forEach(btn => {
            btn.classList.toggle("active", btn.dataset.calendar === value);
          });
          const leapToggle = document.querySelector("#leapToggle");
          if (leapToggle) leapToggle.style.display = value === "lunar" ? "flex" : "none";
        } else if (key === "gender") {
          document.querySelectorAll("[data-gender]").forEach(btn => {
            btn.classList.toggle("active", btn.dataset.gender === value);
          });
        } else if (key === "lunar_is_leap") {
          const cb = document.querySelector("#lunarIsLeapCheckbox");
          if (cb) cb.checked = (value === "true" || value === true);
        }
      }
    });

    if (defaults.status === "ready") {
      setText("#profileBadge", currentText().wb.profile_chart);
    }
  } catch (err) {
    console.error("applyProfileDefaults error:", err);
  } finally {
    state.isBatchUpdating = false;
  }
};

const payloadFromForm = () => {
  const data = new FormData(form);
  return Object.fromEntries(data.entries());
};

const syncQuestionMemory = (payload) => {
  const key = [
    payload.year,
    payload.month,
    payload.day,
    payload.hour,
    payload.flow_year_pillar || "",
    payload.luck_pillar || "",
    payload.flow_month_pillar || "",
  ].join("|");
  if (state.chartMemoryKey && state.chartMemoryKey !== key) {
    state.answeredQuestionIds = [];
    state.answeredQuestionKeys = [];
    state.chatTurns = [];
  }
  state.chartMemoryKey = key;
};

const rememberAnsweredQuestion = (question) => {
  const questionId = String(question.question_id || question.question_key || "").trim();
  const questionKey = String(question.question_key || "").trim();
  if (questionId) state.answeredQuestionIds = unique([...state.answeredQuestionIds, questionId]).slice(-32);
  if (!question.question_id && questionKey) {
    state.answeredQuestionKeys = unique([...state.answeredQuestionKeys, questionKey]).slice(-32);
  }
};

const hasCompletePillars = (payload) => {
  const keys = ["year", "month", "day", "hour"];
  return keys.every((key) => {
    const val = String(payload[key] || "").trim();
    // Simply ensure it's not empty. Let the backend handle the rest.
    return val.length >= 1;
  });
};

const fallbackPillar = (key) => {
  const fieldByKey = {
    year: "year",
    month: "month",
    day: "day",
    hour: "hour",
    luck: "luck_pillar",
    flow_year: "flow_year_pillar",
  };
  const value = String(form.elements[fieldByKey[key]]?.value || "").trim();
  if (value.length < 2) return {};
  // Blacklist only applies to natal pillars (year/month/day/hour) from profile defaults,
  // NOT to time pillars (luck/flow_year) which are always explicit user selections.
  const isTimePillar = key === "luck" || key === "flow_year";
  if (!isTimePillar) {
    const blackList = ["甲子", "戊辰", "甲午", "辛酉", "庚子", "乙亥", "辛丑"];
    if (blackList.includes(value)) return {};
  }
  // If it's a numeric value (like 1982), don't treat it as a GanZhi pillar for glyph rendering
  if (/^\d+$/.test(value)) return {};
  return { stem: value.slice(0, 1), branch: value.slice(1, 2) };
};

const setInquiryText = (value, { syncOnly = false } = {}) => {
  const text = String(value || "");
  form.elements.user_text.value = text;
  if (chatText && chatText.value !== text) chatText.value = text;
  if (!syncOnly) scheduleMeasure({ force: true });
};

const hydrateFormFromParams = () => {
  [
    "year",
    "month",
    "day",
    "hour",
    "flow_year_pillar",
    "luck_pillar",
    "flow_month_pillar",
    "user_text",
    "question_key",
    "question_id",
    "calendar",
    "gender",
    "lunar_is_leap",
  ].forEach((key) => {
    const value = params.get(key);
    if (value !== null && form.elements[key]) form.elements[key].value = value;
  });
  // Guest mode: convert numeric flow_year (e.g. "2026") to GanZhi pillar (e.g. "丙午")
  const flowYearRaw = params.get("flow_year");
  if (flowYearRaw && /^\d{4}$/.test(flowYearRaw) && form.elements.flow_year_pillar) {
    const gz = yearToGanZhi(flowYearRaw);
    if (gz) form.elements.flow_year_pillar.value = gz;
  }
  if (chatText) chatText.value = form.elements.user_text.value || "";
};

const unique = (items) => Array.from(new Set(items));
const currentText = () => UI_TEXT[localeSelect.value] || UI_TEXT.zh;
const measurementRole = (role) => (role === "user" || role === "guest" ? "user" : role === "admin" ? "admin" : "analyst");
const profileMeta = (profile) => {
  const birth = profile.birth_input || {};
  const date = [birth.year, String(birth.month || "").padStart(2, "0"), String(birth.day || "").padStart(2, "0")]
    .filter((value) => value && value !== "00")
    .join("-");
  const time = birth.hour !== undefined ? `${String(birth.hour).padStart(2, "0")}:${String(birth.minute || 0).padStart(2, "0")}` : "";
  return [date, time, profile.owner_id || "", profile.status || ""].filter(Boolean).join(" · ");
};

form.addEventListener("submit", (event) => {
  event.preventDefault();
  measure({
    force: true,
    interactionText: form.elements.user_text.value.trim(),
    interactionSource: currentText().wb.manual,
    llmMode: interactiveLlmMode(),
  });
});
localeSelect.addEventListener("change", () => {
  applyLocale(localeSelect.value);
  scheduleMeasure({ force: true });
});
form.querySelectorAll("input, textarea, select").forEach((node) => {
  node.addEventListener("change", () => scheduleMeasure({ force: true }));
  if (node.tagName === "INPUT" || node.tagName === "TEXTAREA") {
    node.addEventListener("input", () => scheduleMeasure());
  }
  if (node.name === "user_text") {
    node.addEventListener("input", () => {
      if (chatText && chatText.value !== node.value) chatText.value = node.value;
    });
  }
});
document.querySelectorAll(".segment-control button").forEach(btn => {
  btn.addEventListener("click", () => {
    const parent = btn.parentElement;
    parent.querySelectorAll("button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    if (btn.dataset.calendar) {
      document.querySelector("#calendarHidden").value = btn.dataset.calendar;
      const leapToggle = document.querySelector("#leapToggle");
      if (leapToggle) leapToggle.style.display = btn.dataset.calendar === "lunar" ? "flex" : "none";
    } else if (btn.dataset.gender) {
      document.querySelector("#genderHidden").value = btn.dataset.gender;
    }
    scheduleMeasure({ force: true });
  });
});
document.querySelector("#lunarIsLeapCheckbox")?.addEventListener("change", (e) => {
  document.querySelector("#lunarIsLeapHidden").value = e.target.checked;
  scheduleMeasure({ force: true });
});
// Initialization sequence
state.isBatchUpdating = true;
["year", "month", "day", "hour", "flow_year_pillar", "luck_pillar", "flow_month_pillar"].forEach(k => {
  if (form.elements[k]) form.elements[k].value = "";
});
chatButton.addEventListener("click", () => {
  const value = chatText.value.trim();
  if (!value) {
    setText("#answerText", currentText().wb.enter_dir);
    return;
  }
  questionSelect.value = "";
  if (questionIdInput) questionIdInput.value = "";
  setInquiryText(value, { syncOnly: true });
  measure({
    force: true,
    interactionText: value,
    interactionSource: currentText().wb.followup,
    llmMode: interactiveLlmMode(),
  });
});
chatText.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    const value = chatText.value.trim();
    if (!value) {
      setText("#answerText", currentText().wb.enter_dir);
      return;
    }
    questionSelect.value = "";
    if (questionIdInput) questionIdInput.value = "";
    setInquiryText(value, { syncOnly: true });
    measure({
      force: true,
      interactionText: value,
      interactionSource: currentText().wb.followup,
      llmMode: interactiveLlmMode(),
    });
  }
});
document.querySelector("#practitionerToggle")?.addEventListener("click", () => {
  const root = document.querySelector("#practitionerCalibration");
  setPractitionerCollapsed(!root?.classList.contains("collapsed"));
});
document.querySelector("#observationToggle")?.addEventListener("click", () => {
  const root = document.querySelector("#observationPage");
  setObservationCollapsed(!root?.classList.contains("collapsed"));
});
logoutButton?.addEventListener("click", () => logout().catch((error) => setText("#runtimeStatus", error.message)));

if (params.get("locale")) localeSelect.value = params.get("locale");
roleSelect.value = measurementRole(params.get("role") || roleSelect.value);
document.body.classList.toggle("profile-reading", Boolean(params.get("profile_id")));
if (params.get("role") === "guest") {
  document.body.dataset.role = "guest";
  if (logoutButton) logoutButton.hidden = true;
}
hydrateFormFromParams();
applyLocale(localeSelect.value);
// Guest nav: replace "档案" with "入口" AFTER applyLocale to avoid overwrite
if (params.get("role") === "guest") {
  const entryText = { zh: "入口", en: "Entry", ko: "입구" }[localeSelect.value] || "入口";
  const profilesLink = document.querySelector('[data-ui="nav_profiles"]');
  if (profilesLink) {
    profilesLink.textContent = entryText;
    profilesLink.href = `/v20/ui/?locale=${encodeURIComponent(localeSelect.value || "zh")}`;
  }
}
renderInitialPanels();
loadCurrentSession();

loadLatentCalibrationManifest();
state.isBatchUpdating = false;
if (params.get("role") === "guest" || params.get("auto_measure") === "true") {
  scheduleMeasure({ force: true });
} else if (params.get("profile_id")) {
  // If loading a profile, DON'T measure until applyProfileDefaults is DONE
  loadActiveProfile().then(() => {
    console.log("Profile loaded, triggering initial measure.");
    scheduleMeasure({ force: true });
  });
} else {
  // Static state, just render
  renderInitialPanels();
}

