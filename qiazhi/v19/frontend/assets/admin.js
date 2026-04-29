const $ = (id) => document.getElementById(id);

let current = null;
let models = [];
let chatModels = [];

loadSettings();
loadKnowledge();
loadSourceArchive();
loadLab();

["dbUrl", "dbHost", "dbPort", "dbDatabase", "dbUsername", "dbPassword", "dbSslmode", "dbDriver"].forEach((id) => {
  $(id).addEventListener("input", updateDerivedLabels);
});
["llmBaseUrl", "llmHost", "llmPort"].forEach((id) => {
  $(id).addEventListener("input", updateDerivedLabels);
});
$("llmModelSelect").addEventListener("change", () => {
  if ($("llmModelSelect").value) {
    setSelectedModel($("llmModelSelect").value);
  }
});
$("llmModel").addEventListener("input", renderModels);

$("saveDb").addEventListener("click", async () => {
  await saveSettings({ db: readDb() });
  $("dbStatus").textContent = "DB bridge 配置已保存";
});

$("saveLlm").addEventListener("click", async () => {
  await saveSettings({ llm: readLlm() });
  $("llmStatus").textContent = "LLM node 配置已保存";
});

$("testDb").addEventListener("click", async () => {
  setBusy("testDb", true);
  try {
    const result = await postJson("/api/admin/db/test", { db: readDb() });
    $("dbStatus").textContent = `${result.status}: ${result.message}${result.resolved_url ? " · " + result.resolved_url : ""}`;
  } finally {
    setBusy("testDb", false);
  }
});

$("ensureDb").addEventListener("click", async () => {
  setBusy("ensureDb", true);
  try {
    const result = await postJson("/api/admin/db/ensure-database", { db: readDb() });
    const schema = result.schema ? ` · schema: ${result.schema.status}` : "";
    $("dbStatus").textContent = `${result.status}: ${result.message}${schema}${result.resolved_url ? " · " + result.resolved_url : ""}`;
  } finally {
    setBusy("ensureDb", false);
  }
});

$("testLlm").addEventListener("click", async () => {
  setBusy("testLlm", true);
  try {
    const result = await postJson("/api/admin/llm/test", { llm: readLlm() });
    $("llmStatus").textContent = `${result.status}: ${result.message || ""}`;
  } finally {
    setBusy("testLlm", false);
  }
});

$("loadModels").addEventListener("click", async () => {
  setBusy("loadModels", true);
  try {
    const result = await postJson("/api/admin/llm/models", { llm: readLlm() });
    models = Array.isArray(result.models) ? result.models : [];
    chatModels = models.filter(isChatModel);
    if ((!$("llmModel").value || !isChatModel($("llmModel").value)) && chatModels.length) {
      setSelectedModel(chatModels[0]);
    }
    renderModels();
    $("llmStatus").textContent = `${result.status}: ${result.message || ""}${result.models_url ? " · " + result.models_url : ""}`;
  } finally {
    setBusy("loadModels", false);
  }
});

$("testLlmChat").addEventListener("click", async () => {
  setBusy("testLlmChat", true);
  try {
    const result = await postJson("/api/admin/llm/chat-test", { llm: readLlm(), prompt: $("llmPrompt").value });
    $("llmStatus").textContent = `${result.status}: ${result.message || ""}${result.endpoint ? " · " + result.endpoint : ""}`;
    $("llmReply").textContent = result.reply || "无回复";
  } finally {
    setBusy("testLlmChat", false);
  }
});

$("seedKnowledge").addEventListener("click", async () => {
  const result = await postJson("/api/admin/knowledge/seed", { force: false });
  $("knowledgeStatus").textContent = `${result.status}: ${result.count} unit(s) · ${storageText(result.storage)}`;
  await loadKnowledge();
});

$("reloadKnowledge").addEventListener("click", () => loadKnowledge());

$("searchKnowledge").addEventListener("click", async () => {
  const q = $("knowledgeQuery").value;
  const result = await postJson("/api/admin/knowledge/search", { q, context: { chart: true, time_context: { flow_year: true, luck_cycle: true } }, limit: 8 });
  renderKnowledge(result.items || []);
  $("knowledgeStatus").textContent = `search: ${(result.items || []).length} unit(s) · ${result.runtime_scope || ""}`;
});

$("seedBaziSources").addEventListener("click", async () => {
  const result = await postJson("/api/admin/bazi-source-archive/seed", { force: false });
  $("sourceArchiveStatus").textContent = `seeded: +${result.imported_count || 0} / updated ${result.updated_count || 0} · total ${result.count || 0} · no runtime inference change`;
  await loadSourceArchive();
});

$("reloadBaziSources").addEventListener("click", () => loadSourceArchive());

$("filterBaziSources").addEventListener("click", () => loadSourceArchive());

$("loadSourceGovernanceOverview").addEventListener("click", () => loadSourceGovernanceOverview());

$("createSourceExcerpt").addEventListener("click", async () => {
  const result = await postJson("/api/admin/bazi-source-archive/excerpts", {
    actor_role: "admin",
    source_id: $("sourceExcerptSourceId").value,
    locator: $("sourceExcerptLocator").value,
    risk_level: $("sourceExcerptRisk").value,
    keywords: $("sourceExcerptKeywords").value,
    original_excerpt_short: $("sourceExcerptOriginal").value,
    normalized_summary: $("sourceExcerptSummary").value,
  });
  if (result.ok === false) {
    $("sourceArchiveStatus").textContent = `${result.code || "EXCERPT_ERROR"}: ${result.message || ""}`;
    return;
  }
  $("sourceArchiveStatus").textContent = `excerpt created: ${result.item?.excerpt_id || ""} · short excerpt only · no rule creation`;
  await loadSourceExcerpts();
});

$("reloadSourceExcerpts").addEventListener("click", () => loadSourceExcerpts());

$("createKnowledgeDraft").addEventListener("click", async () => {
  const result = await postJson("/api/admin/bazi-source-archive/knowledge-drafts", {
    actor_role: "admin",
    knowledge_id: $("sourceDraftKnowledgeId").value,
    domain: $("sourceDraftDomain").value,
    category: $("sourceDraftCategory").value,
    risk_level: $("sourceDraftRisk").value,
    source_excerpt_ids: $("sourceDraftExcerptIds").value,
    statement: $("sourceDraftStatement").value,
    structured_facts: parseSourceJsonField("sourceDraftFacts", {}),
    confidence_prior: 0.5,
  });
  if (result.ok === false) {
    $("sourceArchiveStatus").textContent = `${result.code || "DRAFT_ERROR"}: ${result.message || ""}`;
    return;
  }
  $("sourceArchiveStatus").textContent = `knowledge draft created: ${result.item?.draft_id || ""} · draft only · requires proposal`;
  await loadKnowledgeDrafts();
});

$("reloadKnowledgeDrafts").addEventListener("click", () => loadKnowledgeDrafts());

$("seedCurrentKnowledgeDrafts").addEventListener("click", async () => {
  const result = await postJson("/api/admin/bazi-source-archive/knowledge-drafts/seed-current", { force: false });
  $("sourceArchiveStatus").textContent = `current knowledge drafts: +${result.imported_count || 0} / updated ${result.updated_count || 0} · total ${result.count || 0} · draft only`;
  await loadKnowledgeDrafts();
});

$("reviewKnowledgeDraft").addEventListener("click", async () => {
  const id = $("sourceDraftReviewId").value.trim();
  if (!id) {
    $("sourceArchiveStatus").textContent = "请先填写 Draft ID 或 Knowledge ID。";
    return;
  }
  const result = await postJson(`/api/admin/bazi-source-archive/knowledge-drafts/${encodeURIComponent(id)}/review`, {
    actor_role: "admin",
    review_status: $("sourceDraftReviewStatus").value,
    note: $("sourceDraftReviewNote").value,
  });
  if (result.ok === false) {
    $("sourceArchiveStatus").textContent = `${result.code || "REVIEW_ERROR"}: ${result.message || ""}`;
    return;
  }
  $("sourceArchiveStatus").textContent = `draft review: ${result.item?.knowledge_id || id} · ${result.item?.review_status || ""} · no runtime inference change`;
  await loadKnowledgeDrafts();
});

$("createRuleProposalFromDraft").addEventListener("click", async () => {
  const id = $("sourceDraftProposalId").value.trim();
  if (!id) {
    $("sourceArchiveStatus").textContent = "请先填写已标记 proposal_ready 的 Draft ID 或 Knowledge ID。";
    return;
  }
  const result = await postJson(`/api/admin/bazi-source-archive/knowledge-drafts/${encodeURIComponent(id)}/create-rule-proposal`, {
    actor_role: "admin",
    domain: $("sourceDraftProposalDomain").value,
    rationale: $("sourceDraftProposalRationale").value,
  });
  if (result.ok === false) {
    $("sourceArchiveStatus").textContent = `${result.code || "PROPOSAL_ERROR"}: ${result.message || ""}`;
    return;
  }
  $("sourceArchiveStatus").textContent = `rule proposal created: ${result.item?.proposal_id || ""} · validation required · no runtime inference mutation`;
  await Promise.all([loadKnowledgeDrafts(), loadBaziRuleProposals()]);
});

$("importV17Profiles").addEventListener("click", async () => {
  setBusy("importV17Profiles", true);
  try {
    const result = await postJson("/api/admin/profiles/import-v17", { owner_id: "admin" });
    $("profileImportStatus").textContent = `scanned: ${result.scanned || 0} · imported: ${result.imported_count || 0} · skipped: ${result.skipped_count || 0} · geo preserved`;
  } finally {
    setBusy("importV17Profiles", false);
  }
});

$("submitFeedback").addEventListener("click", async () => {
  const result = await postJson("/api/lab/feedback", {
    actor_role: $("feedbackRole").value,
    subject_type: $("feedbackSubjectType").value,
    subject_id: $("feedbackSubjectId").value,
    rating: Number($("feedbackRating").value),
    comment: $("feedbackComment").value,
    tags: ["analyst_review"],
    suggested_action: "review_queue",
  });
  $("feedbackStatus").textContent = `created: ${result.item?.feedback_id || ""} · ${storageText(result.storage)}`;
  await loadFeedback();
});

$("reloadFeedback").addEventListener("click", () => loadFeedback());

$("reloadGuidedQuestionFeedback").addEventListener("click", () => loadGuidedQuestionFeedback());

$("filterGuidedQuestion").addEventListener("click", () => loadGuidedQuestionFeedback($("guidedQuestionKey").value.trim()));

$("reloadAnswerQuality").addEventListener("click", () => loadAnswerQuality());

$("filterAnswerQualityFail").addEventListener("click", () => loadAnswerQuality("fail"));

$("filterAnswerQualityWatch").addEventListener("click", () => loadAnswerQuality("watch"));

$("reviewGuidedQuestion").addEventListener("click", async () => {
  const key = $("guidedQuestionKey").value.trim();
  if (!key) {
    $("guidedQuestionStatusLine").textContent = "请先填写 Question Key。";
    return;
  }
  const result = await postJson(`/api/lab/guided-question-feedback/${encodeURIComponent(key)}/review`, {
    status: $("guidedQuestionStatus").value,
    note: $("guidedQuestionNote").value,
    actor_role: "admin",
  });
  $("guidedQuestionStatusLine").textContent = `review: ${result.item?.question_key || key} · ${result.item?.status || ""} · no auto library change`;
  await loadGuidedQuestionFeedback(key);
});

$("reloadRuleImpacts").addEventListener("click", () => loadRuleImpacts());

$("filterIncomeImpacts").addEventListener("click", () => loadRuleImpacts("income_stability"));

$("createRevision").addEventListener("click", async () => {
  const sourceIds = $("revisionSourceImpactIds").value.split(",").map((item) => item.trim()).filter(Boolean);
  const result = await postJson("/api/lab/revisions", {
    source_rule_impact_ids: sourceIds,
    target_rule_id: $("revisionTargetRuleId").value,
    target_signal: $("revisionTargetSignal").value,
    current_version: Number($("revisionCurrentVersion").value || 1),
    proposed_version: Number($("revisionProposedVersion").value || 2),
    proposal: $("revisionProposal").value,
    rationale: "P7 proposal from analyst/admin review. Proposal only; no runtime rule mutation.",
    proposed_by_role: $("revisionReviewerRole").value,
  });
  $("revisionStatus").textContent = `created: ${result.item?.revision_id || ""} · ${storageText(result.storage)} · no runtime mutation`;
  await loadRevisions();
});

$("reloadRevisions").addEventListener("click", () => loadRevisions());

$("reloadActiveRevisions").addEventListener("click", () => loadActiveRevisions());

$("generateGqDraft").addEventListener("click", async () => {
  setBusy("generateGqDraft", true);
  try {
    const result = await postJson("/api/admin/guided-question/draft", {
      question_key: $("gqDraftQuestionKey").value,
      feedback_summary: $("gqDraftFeedbackSummary").value,
      reviewer_note: $("gqDraftReviewerNote").value,
    });
    fillGuidedQuestionProposalDraft(result.draft || {});
    $("gqDraftStatus").textContent = `draft generated · llm used: ${Boolean(result.llm_status?.used)} · manual review required`;
  } finally {
    setBusy("generateGqDraft", false);
  }
});

$("createGqProposal").addEventListener("click", async () => {
  const result = await postJson("/api/lab/guided-question-proposals", readGuidedQuestionProposal());
  $("gqProposalStatus").textContent = `created: ${result.item?.proposal_id || result.code || ""} · proposal only · no runtime mutation`;
  await loadGuidedQuestionProposals();
});

$("reloadGqProposals").addEventListener("click", () => loadGuidedQuestionProposals());

$("reloadGqVersions").addEventListener("click", () => loadGuidedQuestionVersions());

$("recordGqVersion").addEventListener("click", async () => {
  const result = await postJson("/api/lab/guided-question-library/versions", {
    included_proposals: $("gqVersionProposalIds").value,
    activated_by: "admin",
    activated_by_role: "admin",
    note: $("gqVersionNote").value,
  });
  $("gqProposalStatus").textContent = `version: ${result.item?.version_id || result.code || ""} · active record only · no runtime mutation`;
  await Promise.all([loadGuidedQuestionProposals(), loadGuidedQuestionVersions()]);
});

$("createBaziRuleProposal").addEventListener("click", async () => {
  const result = await postJson("/api/lab/bazi-rule-proposals", readBaziRuleProposal());
  $("baziRuleStatus").textContent = `created: ${result.item?.proposal_id || result.code || ""} · rule proposal only · no runtime inference mutation`;
  await loadBaziRuleProposals();
});

$("reloadBaziRuleProposals").addEventListener("click", () => loadBaziRuleProposals());

$("reloadBaziRuleVersions").addEventListener("click", () => loadBaziRuleVersions());

$("recordBaziRuleVersion").addEventListener("click", async () => {
  const result = await postJson("/api/lab/bazi-rule-knowledge/versions", {
    included_proposals: $("brVersionProposalIds").value,
    activated_by: "admin",
    activated_by_role: "admin",
    note: $("brVersionNote").value,
  });
  $("baziRuleStatus").textContent = `version: ${result.item?.version_id || result.code || ""} · active record only · no runtime inference mutation`;
  await Promise.all([loadBaziRuleProposals(), loadBaziRuleVersions()]);
});

$("ingestBaziRuleDb").addEventListener("click", async () => {
  const result = await postJson("/api/admin/bazi-rule-db/ingest-current", { force: false, enable_engine: true });
  $("ruleDbStatus").textContent = `ingested: +${result.imported_count || 0} / updated ${result.updated_count || 0} · blocked ${result.blocked_count || 0} · rules ${result.rule_count || 0}`;
  await loadBaziRuleDb();
});

$("reloadBaziRuleDb").addEventListener("click", () => loadBaziRuleDb());

$("filterBaziRuleDb").addEventListener("click", () => loadBaziRuleDb());

$("createPromotion").addEventListener("click", async () => {
  const result = await postJson("/api/lab/promotions", {
    kind: $("promotionKind").value,
    source_ids: $("promotionSourceIds").value,
    target_id: $("promotionTargetId").value,
    proposal: $("promotionProposal").value,
    rationale: "Analyst review queue entry from Admin.",
    created_by_role: "analyst",
  });
  $("promotionStatus").textContent = `created: ${result.item?.promotion_id || ""} · ${storageText(result.storage)}`;
  await loadPromotions();
});

$("reloadPromotions").addEventListener("click", () => loadPromotions());

$("seedValidation").addEventListener("click", async () => {
  const result = await postJson("/api/lab/validation/seed", { force: false });
  $("validationStatus").textContent = `${result.status}: ${result.count} case(s) · ${storageText(result.storage)}`;
  await loadValidationCases();
});

$("runValidation").addEventListener("click", async () => {
  const result = await postJson("/api/lab/validation/run", {});
  const run = result.run || {};
  $("validationStatus").textContent = `run ${run.run_id || ""}: ${run.passed || 0}/${run.case_count || 0} passed · ${storageText(result.storage)}`;
  renderValidationResults(run.results || []);
});

$("loadLabels").addEventListener("click", () => loadLabels());

async function loadSettings() {
  const result = await fetch("/api/admin/settings").then((response) => response.json());
  current = result.data;
  writeDb(current.db || {});
  writeLlm(current.llm || {});
  $("dbStatus").textContent = `loaded · ${current.settings_path}`;
  $("llmStatus").textContent = `loaded · ${current.settings_path}`;
  updateDerivedLabels();
}

async function loadKnowledge() {
  const status = await fetch("/api/admin/knowledge/status").then((response) => response.json());
  const units = await fetch("/api/admin/knowledge/units").then((response) => response.json());
  $("knowledgeStatus").textContent = `loaded: ${units.count || 0} unit(s) · ${storageText(status.storage)} · ${status.path || ""}`;
  renderKnowledge(units.items || []);
}

async function loadSourceArchive() {
  const params = new URLSearchParams();
  const risk = $("sourceRiskFilter").value;
  const type = $("sourceTypeFilter").value;
  const q = $("sourceQuery").value.trim();
  if (risk) params.set("risk_level", risk);
  if (type) params.set("source_type", type);
  if (q) params.set("q", q);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const [status, sources] = await Promise.all([
    fetch("/api/admin/bazi-source-archive/status").then((response) => response.json()),
    fetch(`/api/admin/bazi-source-archive/sources${suffix}`).then((response) => response.json()),
  ]);
  const counts = status.counts || {};
  $("sourceArchiveStatus").textContent = `sources: ${sources.count || 0}/${counts.sources || 0} · storage: ${storageText(status.storage)} · Source Archive only`;
  renderSourceArchive(sources.items || []);
  await loadSourceExcerpts();
  await loadKnowledgeDrafts();
}

async function loadSourceGovernanceOverview() {
  const result = await fetch("/api/admin/bazi-source-archive/governance-overview").then((response) => response.json());
  renderSourceGovernanceOverview(result);
  $("sourceArchiveStatus").textContent = `governance overview loaded · proposal_ready: ${result.counts?.proposal_ready || 0} · R4 blocked: ${result.counts?.r4_blocked || 0}`;
}

async function loadSourceExcerpts() {
  const params = new URLSearchParams();
  const sourceId = $("sourceExcerptSourceId").value.trim();
  if (sourceId) params.set("source_id", sourceId);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const result = await fetch(`/api/admin/bazi-source-archive/excerpts${suffix}`).then((response) => response.json());
  renderSourceExcerpts(result.items || []);
}

async function loadKnowledgeDrafts() {
  const result = await fetch("/api/admin/bazi-source-archive/knowledge-drafts").then((response) => response.json());
  renderKnowledgeDrafts(result.items || []);
}

async function loadLab() {
  const status = await fetch("/api/lab/status").then((response) => response.json());
  $("feedbackStatus").textContent = `feedback: ${status.counts?.feedback || 0} · guardrail: no auto learning`;
  $("ruleImpactStatus").textContent = `rule impacts: ${status.counts?.rule_impacts || 0} · attribution only`;
  $("revisionStatus").textContent = `revision proposals: ${status.counts?.revision_proposals || 0} · validation gated · no runtime mutation`;
  $("promotionStatus").textContent = `review queue: ${status.counts?.promotion_requests || 0} · no auto promotion`;
  $("validationStatus").textContent = `validation cases: ${status.counts?.validation_cases || 0}`;
  $("guidedQuestionStatusLine").textContent = `guided question feedback: ${status.counts?.guided_question_feedback || 0} · reviews: ${status.counts?.guided_question_reviews || 0}`;
  $("gqProposalStatus").textContent = `guided question proposals: ${status.counts?.guided_question_proposals || 0} · versions: ${status.counts?.guided_question_library_versions || 0}`;
  $("baziRuleStatus").textContent = `bazi rule proposals: ${status.counts?.bazi_rule_proposals || 0} · versions: ${status.counts?.bazi_rule_versions || 0}`;
  await Promise.all([loadFeedback(), loadGuidedQuestionFeedback(), loadAnswerQuality(), loadRuleImpacts(), loadRevisions(), loadActiveRevisions(), loadGuidedQuestionProposals(), loadGuidedQuestionVersions(), loadBaziRuleProposals(), loadBaziRuleVersions(), loadBaziRuleDb(), loadPromotions(), loadValidationCases(), loadLabels()]);
}

async function loadFeedback() {
  const result = await fetch("/api/lab/feedback").then((response) => response.json());
  renderFeedback(result.items || []);
}

async function loadGuidedQuestionFeedback(questionKey = "") {
  const suffix = questionKey ? `?question_key=${encodeURIComponent(questionKey)}` : "";
  const [summary, queue] = await Promise.all([
    fetch("/api/lab/guided-question-feedback/summary").then((response) => response.json()),
    fetch(`/api/lab/guided-question-feedback${suffix}`).then((response) => response.json()),
  ]);
  $("guidedQuestionStatusLine").textContent = `summary: ${summary.count || 0} question(s) · queue: ${queue.count || 0} feedback item(s) · no auto learning`;
  renderGuidedQuestionSummary(summary.items || []);
  renderGuidedQuestionFeedback(queue.items || []);
}

async function loadAnswerQuality(statusFilter = "") {
  const result = await fetch("/api/lab/guided-question-answer-quality").then((response) => response.json());
  const summary = result.summary || {};
  const byStatus = summary.by_status || {};
  const items = statusFilter ? (result.items || []).filter((item) => item.status === statusFilter) : (result.items || []);
  $("answerQualityStatus").textContent = `answer quality: pass ${byStatus.pass || 0} · watch ${byStatus.watch || 0} · fail ${byStatus.fail || 0} · ${statusFilter ? `filtered: ${statusFilter}` : "all"} · no auto learning`;
  renderAnswerQualitySummary(summary);
  renderAnswerQualityItems(items);
}

async function loadRuleImpacts(signal = "") {
  const suffix = signal ? `?signal=${encodeURIComponent(signal)}` : "";
  const result = await fetch(`/api/lab/rule-impacts${suffix}`).then((response) => response.json());
  $("ruleImpactStatus").textContent = `rule impacts: ${result.count || 0} · no auto rule update`;
  renderRuleImpacts(result.items || []);
}

async function loadPromotions() {
  const result = await fetch("/api/lab/promotions").then((response) => response.json());
  renderPromotions(result.items || []);
}

async function loadRevisions() {
  const result = await fetch("/api/lab/revisions").then((response) => response.json());
  $("revisionStatus").textContent = `revision proposals: ${result.count || 0} · proposal only · validation required`;
  renderRevisions(result.items || []);
}

async function loadActiveRevisions() {
  const result = await fetch("/api/lab/active-revisions").then((response) => response.json());
  renderActiveRevisions(result.items || []);
}

async function loadGuidedQuestionProposals() {
  const result = await fetch("/api/lab/guided-question-proposals").then((response) => response.json());
  $("gqProposalStatus").textContent = `guided question proposals: ${result.count || 0} · no auto library update`;
  renderGuidedQuestionProposals(result.items || []);
}

async function loadGuidedQuestionVersions() {
  const result = await fetch("/api/lab/guided-question-library/versions").then((response) => response.json());
  renderGuidedQuestionVersions(result.items || []);
}

async function loadBaziRuleProposals() {
  const result = await fetch("/api/lab/bazi-rule-proposals").then((response) => response.json());
  $("baziRuleStatus").textContent = `bazi rule proposals: ${result.count || 0} · ledger only · no runtime inference mutation`;
  renderBaziRuleProposals(result.items || []);
}

async function loadBaziRuleVersions() {
  const result = await fetch("/api/lab/bazi-rule-knowledge/versions").then((response) => response.json());
  renderBaziRuleVersions(result.items || []);
}

async function loadBaziRuleDb() {
  const params = new URLSearchParams();
  const domain = $("ruleDbDomainFilter").value;
  const risk = $("ruleDbRiskFilter").value;
  const q = $("ruleDbQuery").value.trim();
  if (domain) params.set("domain", domain);
  if (risk) params.set("risk_level", risk);
  if (q) params.set("q", q);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const [status, rules] = await Promise.all([
    fetch("/api/admin/bazi-rule-db/status").then((response) => response.json()),
    fetch(`/api/admin/bazi-rule-db/rules${suffix}`).then((response) => response.json()),
  ]);
  $("ruleDbStatus").textContent = `rules: ${rules.count || 0}/${status.counts?.rules || 0} · engine_enabled: ${status.counts?.engine_enabled || 0} · Rule DB`;
  renderBaziRuleDb(rules.items || []);
}

async function loadValidationCases() {
  const result = await fetch("/api/lab/validation/cases").then((response) => response.json());
  renderValidationCases(result.items || []);
}

async function loadLabels() {
  const locale = $("labelsLocale").value;
  const result = await fetch(`/api/lab/labels?locale=${encodeURIComponent(locale)}`).then((response) => response.json());
  renderLabels(result.terms || {});
}

async function saveSettings(payload) {
  const result = await postJson("/api/admin/settings", payload);
  current = result.data;
  writeDb(current.db || {});
  writeLlm(current.llm || {});
  updateDerivedLabels();
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

function readDb() {
  return {
    enabled: $("dbEnabled").checked,
    storage_backend: $("dbStorageBackend").value,
    backend: "postgres",
    driver: $("dbDriver").value,
    host: $("dbHost").value,
    port: Number($("dbPort").value || 5432),
    database: $("dbDatabase").value,
    username: $("dbUsername").value,
    password: $("dbPassword").value,
    sslmode: $("dbSslmode").value,
    url: $("dbUrl").value,
    auto_migrate_json_to_postgres: $("dbAutoMigrate").checked,
  };
}

function readLlm() {
  return {
    enabled: $("llmEnabled").checked,
    execute_llm: $("llmExecuteLlm").checked,
    provider: $("llmProvider").value,
    host: $("llmHost").value,
    port: Number($("llmPort").value || 11434),
    base_url: $("llmBaseUrl").value,
    username: $("llmUsername").value,
    password: $("llmPassword").value,
    api_key: $("llmApiKey").value,
    model: $("llmModel").value,
    http_timeout_sec: Number($("llmHttpTimeoutSec").value || 15),
    fuse_wait_timeout_sec: Number($("llmFuseWaitSec").value || 30),
    temperature: Number($("llmTemperature").value || 0.2),
    max_tokens: Number($("llmMaxTokens").value || 800),
  };
}

function readGuidedQuestionProposal() {
  return {
    proposed_action: $("gqProposalAction").value,
    source_question_key: $("gqSourceQuestionKey").value,
    source_feedback_ids: $("gqSourceFeedbackIds").value,
    proposed_question_key: $("gqProposedQuestionKey").value,
    proposed_label: {
      zh: $("gqLabelZh").value,
      en: $("gqLabelEn").value,
      ko: $("gqLabelKo").value,
    },
    proposed_metadata: {
      depth: $("gqDepth").value,
      required_context: $("gqRequiredContext").value.split(",").map((item) => item.trim()).filter(Boolean),
      related_questions: $("gqRelatedQuestions").value.split(",").map((item) => item.trim()).filter(Boolean),
      forbidden_prediction: true,
    },
    rationale: $("gqRationale").value,
  };
}

function readBaziRuleProposal() {
  return {
    actor_role: "admin",
    rule_id: $("brRuleId").value,
    domain: $("brDomain").value,
    version: Number($("brVersion").value || 1),
    source_feedback_ids: $("brSourceFeedbackIds").value,
    input_contract: { required: $("brInputRequired").value.split(",").map((item) => item.trim()).filter(Boolean) },
    condition: parseJsonField("brCondition", {}),
    output_contract: parseJsonField("brOutputContract", {}),
    reasoning_path: $("brReasoningPath").value,
    evidence: { source_ids: $("brSourceFeedbackIds").value.split(",").map((item) => item.trim()).filter(Boolean), notes: "Admin-entered proposal evidence placeholder." },
    confidence: 0,
    rationale: $("brRationale").value,
    guardrails: ["STRUCTURE_ONLY", "NO_PREDICTION", "NO_RUNTIME_INFERENCE_MUTATION"],
  };
}

function parseJsonField(id, fallback) {
  try {
    return JSON.parse($(id).value || "{}");
  } catch (error) {
    $(`${id === "brCondition" ? "baziRuleStatus" : "baziRuleStatus"}`).textContent = `${id} JSON parse failed: ${error.message}`;
    return fallback;
  }
}

function parseSourceJsonField(id, fallback) {
  try {
    return JSON.parse($(id).value || "{}");
  } catch (error) {
    $("sourceArchiveStatus").textContent = `${id} JSON parse failed: ${error.message}`;
    return fallback;
  }
}

function fillGuidedQuestionProposalDraft(draft) {
  $("gqProposalAction").value = draft.proposed_action || "edit";
  $("gqProposedQuestionKey").value = draft.proposed_question_key || $("gqDraftQuestionKey").value || "";
  if (!$("gqSourceQuestionKey").value) $("gqSourceQuestionKey").value = $("gqDraftQuestionKey").value || draft.proposed_question_key || "";
  const label = draft.proposed_label || {};
  $("gqLabelZh").value = label.zh || "";
  $("gqLabelEn").value = label.en || "";
  $("gqLabelKo").value = label.ko || "";
  const meta = draft.proposed_metadata || {};
  $("gqDepth").value = meta.depth || "beginner";
  $("gqRequiredContext").value = Array.isArray(meta.required_context) ? meta.required_context.join(",") : "chart,result";
  $("gqRelatedQuestions").value = Array.isArray(meta.related_questions) ? meta.related_questions.join(",") : "";
  $("gqRationale").value = draft.rationale || "Draft only. Human review required.";
}

function writeDb(db) {
  $("dbEnabled").checked = Boolean(db.enabled);
  $("dbStorageBackend").value = db.storage_backend || "file";
  $("dbDriver").value = db.driver || "postgresql";
  $("dbHost").value = db.host || "127.0.0.1";
  $("dbPort").value = db.port ?? 5432;
  $("dbDatabase").value = db.database || "qiazhi_v19";
  $("dbUsername").value = db.username || "postgres";
  $("dbPassword").value = db.password || "";
  $("dbSslmode").value = db.sslmode || "prefer";
  $("dbUrl").value = db.url || "";
  $("dbAutoMigrate").checked = Boolean(db.auto_migrate_json_to_postgres);
  $("dbResolvedUrl").textContent = db.resolved_url || deriveDbUrl();
}

function writeLlm(llm) {
  $("llmEnabled").checked = Boolean(llm.enabled);
  $("llmExecuteLlm").checked = llm.execute_llm !== false;
  $("llmProvider").value = llm.provider || "ollama";
  $("llmHost").value = llm.host || "127.0.0.1";
  $("llmPort").value = llm.port ?? 11434;
  $("llmBaseUrl").value = llm.base_url || "";
  $("llmUsername").value = llm.username || "";
  $("llmPassword").value = llm.password || "";
  $("llmApiKey").value = llm.api_key || "";
  $("llmModel").value = llm.model || "qwen2.5:7b";
  $("llmHttpTimeoutSec").value = llm.http_timeout_sec ?? 15;
  $("llmFuseWaitSec").value = llm.fuse_wait_timeout_sec ?? 30;
  $("llmTemperature").value = llm.temperature ?? 0.2;
  $("llmMaxTokens").value = llm.max_tokens ?? 800;
  $("llmResolvedBaseUrl").textContent = llm.resolved_base_url || deriveLlmBaseUrl();
  renderModels();
}

function updateDerivedLabels() {
  $("dbResolvedUrl").textContent = deriveDbUrl();
  $("llmResolvedBaseUrl").textContent = deriveLlmBaseUrl();
}

function deriveDbUrl() {
  const explicit = $("dbUrl").value.trim();
  if (explicit) return maskUrl(explicit);
  const driver = $("dbDriver").value.trim() || "postgresql";
  const host = $("dbHost").value.trim() || "127.0.0.1";
  const port = $("dbPort").value || "5432";
  const db = $("dbDatabase").value.trim() || "qiazhi_v19";
  const user = $("dbUsername").value.trim() || "postgres";
  const pass = $("dbPassword").value ? ":********" : "";
  const ssl = $("dbSslmode").value.trim() || "prefer";
  return `${driver}://${encodeURIComponent(user)}${pass}@${host}:${port}/${encodeURIComponent(db)}?sslmode=${encodeURIComponent(ssl)}`;
}

function deriveLlmBaseUrl() {
  const explicit = $("llmBaseUrl").value.trim();
  if (explicit) return explicit.replace(/\/$/, "");
  const host = $("llmHost").value.trim() || "127.0.0.1";
  const port = $("llmPort").value || "11434";
  const root = host.startsWith("http://") || host.startsWith("https://") ? host : `http://${host}`;
  const withPort = /:\d+(\/|$)/.test(root) ? root : `${root}:${port}`;
  return withPort.replace(/\/$/, "") + (withPort.endsWith("/v1") ? "" : "/v1");
}

function maskUrl(value) {
  return value.replace(/:\/\/([^:/@]+):([^@]+)@/, "://$1:********@");
}

function renderModels() {
  const select = $("llmModelSelect");
  const selected = $("llmModel").value;
  const primary = chatModels.length ? chatModels : models;
  select.innerHTML = primary.length
    ? primary.map((model) => `<option value="${escapeHtml(model)}" ${model === selected ? "selected" : ""}>${escapeHtml(model)}</option>`).join("")
    : '<option value="">先加载模型</option>';

  const box = $("llmModels");
  if (!models.length) {
    box.innerHTML = "";
    return;
  }
  box.innerHTML = models.map((model) => {
    const active = model === selected ? " active" : "";
    const muted = isChatModel(model) ? "" : " muted";
    const label = isChatModel(model) ? model : `${model} · embedding`;
    return `<button type="button" class="model-chip${active}${muted}" data-model="${escapeHtml(model)}">${escapeHtml(label)}</button>`;
  }).join("");
  box.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => setSelectedModel(button.dataset.model || ""));
  });
}

function setSelectedModel(model) {
  if (!model) return;
  $("llmModel").value = model;
  $("llmModelSelect").value = model;
  renderModels();
  $("llmStatus").textContent = `已选择模型：${model}；如需持久化请点保存 LLM。`;
}

function isChatModel(model) {
  const value = String(model || "").toLowerCase();
  return !/(embed|embedding|bge|nomic-embed|rerank)/.test(value);
}

function renderKnowledge(items) {
  const box = $("knowledgeList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No knowledge units loaded.</div>";
    return;
  }
  box.innerHTML = items.map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.knowledge_id || "")}</span><strong>${escapeHtml(item.domain || "")}</strong></div>
    <h3>${escapeHtml(item.title || "")}</h3>
    <p>${escapeHtml(item.statement || "")}</p>
    <div class="knowledge-guard">status: ${escapeHtml(item.status || "")} · evidence: ${escapeHtml(item.evidence_type || "")}</div>
  </article>`).join("");
}

function renderSourceArchive(items) {
  const box = $("sourceArchiveList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">没有匹配的八字资料来源。</div>";
    return;
  }
  box.innerHTML = items.map((item) => {
    const locator = item.url || item.local_path || "";
    const scope = Array.isArray(item.knowledge_scope) ? item.knowledge_scope.join(", ") : "";
    const allowed = Array.isArray(item.allowed_usage) ? item.allowed_usage.join(", ") : "";
    const forbidden = Array.isArray(item.forbidden_usage) ? item.forbidden_usage.join(", ") : "";
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.source_id || "")}</span><strong>${escapeHtml(item.risk_level || "")} · ${escapeHtml(item.source_type || "")}</strong></div>
      <h3>${escapeHtml(item.title || "")}</h3>
      <p>${escapeHtml(item.author_or_compiler || "")}${item.period ? " · " + escapeHtml(item.period) : ""}</p>
      <p>${escapeHtml(scope || "未标注知识范围")}</p>
      <div class="knowledge-guard">priority: ${escapeHtml(item.source_priority || "")} · reliability: ${escapeHtml(item.reliability || "")} · status: ${escapeHtml(item.ingestion_status || "")}</div>
      <div class="knowledge-guard">allowed: ${escapeHtml(allowed || "source_archive")}</div>
      <div class="knowledge-guard">forbidden: ${escapeHtml(forbidden || "direct_active_rule")}</div>
      <div class="knowledge-guard">${locator ? escapeHtml(locator) : "no locator"} · no runtime inference change</div>
    </article>`;
  }).join("");
}

function renderSourceGovernanceOverview(result) {
  const box = $("sourceGovernanceOverview");
  const counts = result.counts || {};
  const ready = result.proposal_ready_items || [];
  const blocked = result.r4_blocked_items || [];
  const revision = result.needs_revision_items || [];
  box.innerHTML = `<article class="knowledge-item">
    <div class="knowledge-top"><span>Knowledge Governance Overview</span><strong>no runtime inference change</strong></div>
    <h3>Drafts ${escapeHtml(counts.knowledge_drafts || 0)} · Ready ${escapeHtml(counts.proposal_ready || 0)} · R4 Blocked ${escapeHtml(counts.r4_blocked || 0)}</h3>
    <p>pending: ${escapeHtml(counts.pending || 0)} · needs_revision: ${escapeHtml(counts.needs_revision || 0)} · excerpts: ${escapeHtml(counts.excerpts || 0)}</p>
    <div class="knowledge-guard">review_status: ${escapeHtml(JSON.stringify(counts.by_review_status || {}))}</div>
    <div class="knowledge-guard">risk_level: ${escapeHtml(JSON.stringify(counts.by_risk_level || {}))}</div>
  </article>${renderDraftMiniList("Proposal Ready", ready)}${renderDraftMiniList("R4 Blocked", blocked)}${renderDraftMiniList("Needs Revision", revision)}`;
}

function renderDraftMiniList(title, items) {
  if (!items.length) return "";
  return `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(title)}</span><strong>${escapeHtml(items.length)}</strong></div>
    <p>${items.slice(0, 12).map((item) => escapeHtml(item.knowledge_id || item.draft_id || "")).join(" · ")}</p>
    <div class="knowledge-guard">overview only · proposal creation remains manual</div>
  </article>`;
}

function renderSourceExcerpts(items) {
  const box = $("sourceExcerptList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">暂无短摘录。先选择 Source ID，再创建 Excerpt。</div>";
    return;
  }
  box.innerHTML = items.slice(0, 16).map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.excerpt_id || "")}</span><strong>${escapeHtml(item.risk_level || "")} · ${escapeHtml(item.status || "")}</strong></div>
    <h3>${escapeHtml(item.source_id || "")}</h3>
    <p>${escapeHtml(item.normalized_summary || item.original_excerpt_short || "")}</p>
    <div class="knowledge-guard">locator: ${escapeHtml(item.locator || "-")} · keywords: ${escapeHtml((item.keywords || []).join(", ") || "-")}</div>
    <div class="knowledge-guard">short excerpt only · no bulk copy · no rule creation</div>
  </article>`).join("");
}

function renderKnowledgeDrafts(items) {
  const box = $("sourceDraftList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">暂无知识单元草稿。先从 Excerpt 创建 Draft。</div>";
    return;
  }
  box.innerHTML = items.slice(0, 16).map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.draft_id || "")}</span><strong>${escapeHtml(item.review_status || "pending")} · ${escapeHtml(item.risk_level || "")}</strong></div>
    <h3>${escapeHtml(item.knowledge_id || "")}</h3>
    <p>${escapeHtml(item.statement || "")}</p>
    <div class="knowledge-guard">category: ${escapeHtml(item.category || "-")} · excerpts: ${escapeHtml((item.source_excerpt_ids || []).join(", ") || "-")}</div>
    <div class="knowledge-guard">review: ${escapeHtml(item.review_note || "pending")} · domain: ${escapeHtml(item.domain || "")}</div>
    <div class="button-row">
      <button type="button" class="secondary" data-draft-proposal="${escapeHtml(item.knowledge_id || item.draft_id || "")}">Use for Proposal</button>
    </div>
    <div class="knowledge-guard">draft only · not active knowledge · requires Rule Proposal before runtime</div>
  </article>`).join("");
  box.querySelectorAll("[data-draft-proposal]").forEach((button) => {
    button.addEventListener("click", () => {
      $("sourceDraftProposalId").value = button.dataset.draftProposal || "";
      $("sourceDraftReviewId").value = button.dataset.draftProposal || "";
      $("sourceArchiveStatus").textContent = `selected draft: ${button.dataset.draftProposal || ""} · mark proposal_ready before creating proposal`;
    });
  });
}

function renderFeedback(items) {
  const box = $("feedbackList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No feedback yet.</div>";
    return;
  }
  box.innerHTML = items.slice(0, 8).map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.feedback_id || "")}</span><strong>${escapeHtml(item.actor_role || "")}</strong></div>
    <h3>${escapeHtml(item.subject_type || "")} · rating ${escapeHtml(item.rating ?? "")}</h3>
    <p>${escapeHtml(item.comment || "")}</p>
    <div class="knowledge-guard">status: ${escapeHtml(item.status || "")} · feedback is not a rule</div>
  </article>`).join("");
}

function renderGuidedQuestionSummary(items) {
  const box = $("guidedQuestionSummary");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No guided question feedback summary yet.</div>";
    return;
  }
  box.innerHTML = items.slice(0, 12).map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.question_key || "")}</span><strong>${escapeHtml(item.review_status || "pending")}</strong></div>
    <h3>${escapeHtml(String(item.helpful_count || 0))} helpful / ${escapeHtml(String(item.not_helpful_count || 0))} not helpful</h3>
    <p>total: ${escapeHtml(String(item.total || 0))} · helpful_rate: ${escapeHtml(String(item.helpful_rate ?? 0))} · latest: ${escapeHtml(item.latest_feedback_at || "-")}</p>
    <div class="knowledge-guard">summary only · no auto question-library update</div>
  </article>`).join("");
}

function renderGuidedQuestionFeedback(items) {
  const box = $("guidedQuestionFeedbackList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No guided question feedback items yet.</div>";
    return;
  }
  box.innerHTML = items.slice(0, 16).map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.feedback_id || "")}</span><strong>${escapeHtml(item.review_status || "pending")}</strong></div>
    <h3>${escapeHtml(item.subject_id || "")} · rating ${escapeHtml(item.rating ?? "")}</h3>
    <p>${escapeHtml(item.comment || "")}</p>
    <div class="knowledge-guard">actor: ${escapeHtml(item.actor_role || "")} · status: ${escapeHtml(item.status || "")} · guided feedback only</div>
  </article>`).join("");
}

function renderAnswerQualitySummary(summary = {}) {
  const box = $("answerQualitySummary");
  const byStatus = summary.by_status || {};
  const riskFlags = summary.risk_flags || [];
  if (!Object.keys(byStatus).length && !riskFlags.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No answer quality records yet. Run P7 audit or collect answer feedback first.</div>";
    return;
  }
  const statusLine = Object.entries(byStatus).map(([key, value]) => `${escapeHtml(key)}: ${escapeHtml(String(value))}`).join(" · ") || "no status";
  const risks = riskFlags.slice(0, 8).map((item) => `${escapeHtml(item.key || "")}: ${escapeHtml(String(item.count || 0))}`).join(" · ") || "no risk flags";
  box.innerHTML = `<article class="knowledge-item">
    <div class="knowledge-top"><span>P7 quality summary</span><strong>review only</strong></div>
    <h3>${statusLine}</h3>
    <p>${risks}</p>
    <div class="knowledge-guard">quality report only · no auto learning · no runtime mutation</div>
  </article>`;
}

function renderAnswerQualityItems(items) {
  const box = $("answerQualityList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No answer quality items for this filter.</div>";
    return;
  }
  box.innerHTML = items.slice(0, 24).map((item) => {
    const flags = (item.risk_flags || []).map(escapeHtml).join(", ") || "none";
    const status = item.status || "unknown";
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.source_id || "")}</span><strong>${escapeHtml(status)}</strong></div>
      <h3>${escapeHtml(item.question_key || "-")} · score ${escapeHtml(String(item.score ?? ""))}</h3>
      <p>${escapeHtml(item.text_preview || "")}</p>
      <div class="knowledge-guard">source: ${escapeHtml(item.source_type || "")} · action: ${escapeHtml(item.suggested_review_action || "")} · risks: ${flags}</div>
    </article>`;
  }).join("");
}

function renderRuleImpacts(items) {
  const box = $("ruleImpactList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No rule impact mappings yet.</div>";
    return;
  }
  box.innerHTML = items.slice(0, 12).map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.impact_id || "")}</span><strong>${escapeHtml(item.signal || "")}</strong></div>
    <h3>${escapeHtml(item.rule_id || "")}@v${escapeHtml(item.rule_version || "")}</h3>
    <p>${escapeHtml(item.condition || "")}</p>
    <div class="knowledge-guard">feedback: ${escapeHtml(item.feedback_id || "")} · confidence: ${escapeHtml(item.confidence ?? "")} · attribution only</div>
  </article>`).join("");
}

function renderPromotions(items) {
  const box = $("promotionList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No review requests yet.</div>";
    return;
  }
  box.innerHTML = items.slice(0, 8).map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.promotion_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
    <h3>${escapeHtml(item.kind || "")} → ${escapeHtml(item.target_id || "")}</h3>
    <p>${escapeHtml(item.proposal || "")}</p>
    <div class="knowledge-guard">request only · analyst approval required · no auto activation</div>
  </article>`).join("");
}

function renderValidationCases(items) {
  const box = $("validationList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No validation cases yet.</div>";
    return;
  }
  box.innerHTML = items.slice(0, 6).map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.case_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
    <h3>${escapeHtml(item.title || "")}</h3>
    <p>synthetic case · not domain truth</p>
  </article>`).join("");
}

function renderValidationResults(items) {
  const box = $("validationList");
  box.innerHTML = items.map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.case_id || "")}</span><strong>${item.passed ? "passed" : "failed"}</strong></div>
    <h3>${item.passed ? "PASS" : "FAIL"}</h3>
    <p>${escapeHtml(JSON.stringify(item.observed || {}))}</p>
  </article>`).join("");
}

function renderLabels(terms) {
  const box = $("labelsList");
  const items = Object.entries(terms);
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No labels loaded.</div>";
    return;
  }
  box.innerHTML = items.map(([key, value]) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(key)}</span><strong>${escapeHtml(value.category || "")}</strong></div>
    <h3>${escapeHtml(value.label || "")}</h3>
    <p>${escapeHtml(value.description || "")}</p>
  </article>`).join("");
}

function storageText(storage) {
  if (!storage) return "unknown";
  return `${storage.backend || "unknown"}${storage.fallback_reason ? " (" + storage.fallback_reason + ")" : ""}`;
}

function setBusy(id, busy) {
  $(id).disabled = busy;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

function renderRevisions(items) {
  const box = $("revisionList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No rule revision proposals.</div>";
    return;
  }
  box.innerHTML = items.map((item) => {
    const canValidate = item.status === "draft" || item.status === "validation_failed";
    const canApprove = item.status === "validation_passed";
    const canActivate = item.status === "approved";
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.revision_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
      <h3>${escapeHtml(item.target_rule_id || "")} · ${escapeHtml(item.target_signal || "")}</h3>
      <p>${escapeHtml(item.proposal || "")}</p>
      <div class="knowledge-guard">version: ${escapeHtml(String(item.current_version || ""))} -> ${escapeHtml(String(item.proposed_version || ""))} · source impacts: ${(item.source_rule_impact_ids || []).map(escapeHtml).join(", ") || "none"}</div>
      <div class="knowledge-guard">guardrail: proposal only · validation required · no runtime mutation</div>
      <div class="button-row three">
        <button type="button" data-revision-action="validate" data-revision-id="${escapeHtml(item.revision_id || "")}" ${canValidate ? "" : "disabled"}>Validate</button>
        <button type="button" class="secondary" data-revision-action="approve" data-revision-id="${escapeHtml(item.revision_id || "")}" ${canApprove ? "" : "disabled"}>Approve</button>
        <button type="button" class="secondary" data-revision-action="activate" data-revision-id="${escapeHtml(item.revision_id || "")}" ${canActivate ? "" : "disabled"}>Record Active</button>
      </div>
    </article>`;
  }).join("");
  box.querySelectorAll("[data-revision-action]").forEach((button) => {
    button.addEventListener("click", () => handleRevisionAction(button.dataset.revisionId || "", button.dataset.revisionAction || ""));
  });
}

function renderActiveRevisions(items) {
  const box = $("activeRevisionList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No active revision records. Active records do not mutate runtime rules.</div>";
    return;
  }
  box.innerHTML = items.map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.revision_id || "")}</span><strong>active revision record</strong></div>
    <h3>${escapeHtml(item.target_rule_id || "")}</h3>
    <p>${escapeHtml(item.activation_note || item.note || "No activation note.")}</p>
    <div class="knowledge-guard">activated_by: ${escapeHtml(item.activated_by_role || "")} · runtime_mutation: ${escapeHtml(String(item.runtime_mutation))}</div>
  </article>`).join("");
}

function renderGuidedQuestionProposals(items) {
  const box = $("gqProposalList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No guided question proposals yet.</div>";
    return;
  }
  box.innerHTML = items.map((item) => {
    const canValidate = item.status === "draft" || item.status === "validation_failed";
    const canApprove = item.status === "validation_ready";
    const checks = (((item.validation || {}).checks) || []).map((check) => `${check.name}:${check.passed ? "pass" : "fail"}`).join(" · ");
    const history = (item.history || []).slice(-4).map((row) => `${row.status}@${row.actor_role}: ${row.note || ""}`).join(" / ");
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.proposal_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
      <h3>${escapeHtml(item.proposed_action || "")} · ${escapeHtml(item.proposed_question_key || item.source_question_key || "")}</h3>
      <p>${escapeHtml(item.rationale || "")}</p>
      <div class="knowledge-guard">source: ${escapeHtml(item.source_question_key || "-")} · feedback: ${(item.source_feedback_ids || []).map(escapeHtml).join(", ") || "none"}</div>
      <div class="knowledge-guard">validation: ${escapeHtml(checks || "not run")} · no auto QUESTION_LIBRARY update</div>
      <div class="knowledge-guard">proposal only · validation required · approval required · runtime_mutation=false</div>
      <div class="knowledge-guard">history: ${escapeHtml(history || "created only")}</div>
      <div class="button-row three">
        <button type="button" data-gq-action="validate" data-gq-id="${escapeHtml(item.proposal_id || "")}" ${canValidate ? "" : "disabled"}>Validate</button>
        <button type="button" class="secondary" data-gq-action="approve" data-gq-id="${escapeHtml(item.proposal_id || "")}" ${canApprove ? "" : "disabled"}>Approve</button>
        <button type="button" class="secondary" data-gq-copy="${escapeHtml(item.proposal_id || "")}">Copy ID</button>
      </div>
    </article>`;
  }).join("");
  box.querySelectorAll("[data-gq-action]").forEach((button) => {
    button.addEventListener("click", () => handleGuidedQuestionProposalAction(button.dataset.gqId || "", button.dataset.gqAction || ""));
  });
  box.querySelectorAll("[data-gq-copy]").forEach((button) => {
    button.addEventListener("click", () => {
      $("gqVersionProposalIds").value = button.dataset.gqCopy || "";
      $("gqProposalStatus").textContent = `copied proposal id: ${button.dataset.gqCopy || ""}`;
    });
  });
}

function renderGuidedQuestionVersions(items) {
  const box = $("gqVersionList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No guided question library version records. Version records do not mutate runtime UI.</div>";
    return;
  }
  box.innerHTML = items.map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.version_id || "")}</span><strong>version record</strong></div>
    <h3>${escapeHtml(String((item.included_proposals || []).length))} proposal(s) · runtime_mutation: ${escapeHtml(String(item.runtime_mutation))}</h3>
    <p>${escapeHtml(item.note || "")}</p>
    <div class="knowledge-guard">included: ${(item.included_proposals || []).map(escapeHtml).join(", ") || "none"} · future engineering implementation required</div>
    <div class="knowledge-guard">changelog: ${escapeHtml((item.changelog || []).map((row) => `${row.action}:${row.question_key}`).join(" / ") || "none")}</div>
  </article>`).join("");
}

function renderBaziRuleProposals(items) {
  const box = $("baziRuleProposalList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No Bazi rule proposals yet.</div>";
    return;
  }
  box.innerHTML = items.map((item) => {
    const canValidate = item.status === "draft" || item.status === "validation_failed";
    const canApprove = item.status === "validation_ready";
    const checks = (((item.validation || {}).checks) || []).map((check) => `${check.name}:${check.passed ? "pass" : "fail"}`).join(" · ");
    const history = (item.history || []).slice(-4).map((row) => `${row.status}@${row.actor_role}: ${row.note || ""}`).join(" / ");
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.proposal_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
      <h3>${escapeHtml(item.rule_id || "")} · ${escapeHtml(item.domain || "")}@v${escapeHtml(item.version || "")}</h3>
      <p>${escapeHtml(item.rationale || "")}</p>
      <div class="knowledge-guard">validation: ${escapeHtml(checks || "not run")} · rule proposal only</div>
      <div class="knowledge-guard">runtime_inference_mutation=false · future engineering implementation required</div>
      <div class="knowledge-guard">history: ${escapeHtml(history || "created only")}</div>
      <div class="button-row three">
        <button type="button" data-br-action="validate" data-br-id="${escapeHtml(item.proposal_id || "")}" ${canValidate ? "" : "disabled"}>Validate</button>
        <button type="button" class="secondary" data-br-action="approve" data-br-id="${escapeHtml(item.proposal_id || "")}" ${canApprove ? "" : "disabled"}>Approve</button>
        <button type="button" class="secondary" data-br-copy="${escapeHtml(item.proposal_id || "")}">Copy ID</button>
      </div>
    </article>`;
  }).join("");
  box.querySelectorAll("[data-br-action]").forEach((button) => {
    button.addEventListener("click", () => handleBaziRuleProposalAction(button.dataset.brId || "", button.dataset.brAction || ""));
  });
  box.querySelectorAll("[data-br-copy]").forEach((button) => {
    button.addEventListener("click", () => {
      $("brVersionProposalIds").value = button.dataset.brCopy || "";
      $("baziRuleStatus").textContent = `copied rule proposal id: ${button.dataset.brCopy || ""}`;
    });
  });
}

function renderBaziRuleVersions(items) {
  const box = $("baziRuleVersionList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No Bazi rule version records. Version records do not mutate runtime inference.</div>";
    return;
  }
  box.innerHTML = items.map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.version_id || "")}</span><strong>rule version record</strong></div>
    <h3>${escapeHtml(String((item.included_proposals || []).length))} proposal(s) · runtime_mutation: ${escapeHtml(String(item.runtime_mutation))}</h3>
    <p>${escapeHtml(item.note || "")}</p>
    <div class="knowledge-guard">included: ${(item.included_proposals || []).map(escapeHtml).join(", ") || "none"} · future engineering implementation required</div>
    <div class="knowledge-guard">changelog: ${escapeHtml((item.changelog || []).map((row) => `${row.domain}:${row.rule_id}`).join(" / ") || "none")}</div>
  </article>`).join("");
}

function renderBaziRuleDb(items) {
  const box = $("ruleDbList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No Bazi Rule DB records yet.</div>";
    return;
  }
  box.innerHTML = items.slice(0, 40).map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.rule_id || "")}</span><strong>${escapeHtml(item.domain || "")} · ${escapeHtml(item.risk_level || "")}</strong></div>
    <h3>${escapeHtml(item.title || item.knowledge_id || "")}</h3>
    <p>${escapeHtml(item.statement || "")}</p>
    <div class="knowledge-guard">status: ${escapeHtml(item.status || "")} · engine_enabled: ${escapeHtml(String(Boolean(item.engine_enabled)))} · signal: ${escapeHtml((item.output_contract || {}).signal || "")}</div>
    <div class="knowledge-guard">source draft: ${escapeHtml(item.source_draft_id || "")} · category: ${escapeHtml(item.category || "")}</div>
  </article>`).join("");
}

async function handleBaziRuleProposalAction(proposalId, action) {
  if (!proposalId || !action) return;
  let result;
  if (action === "validate") {
    result = await postJson(`/api/lab/bazi-rule-proposals/${encodeURIComponent(proposalId)}/validate`, {});
  } else if (action === "approve") {
    result = await postJson(`/api/lab/bazi-rule-proposals/${encodeURIComponent(proposalId)}/approve`, {
      actor_role: "admin",
      note: "Approved as Bazi rule knowledge proposal. No runtime inference mutation.",
    });
  } else {
    return;
  }
  $("baziRuleStatus").textContent = `${action}: ${result.item?.proposal_id || proposalId} · ${result.item?.status || result.code || ""} · no runtime inference mutation`;
  await loadBaziRuleProposals();
}

async function handleGuidedQuestionProposalAction(proposalId, action) {
  if (!proposalId || !action) return;
  let result;
  if (action === "validate") {
    result = await postJson(`/api/lab/guided-question-proposals/${encodeURIComponent(proposalId)}/validate`, {});
  } else if (action === "approve") {
    result = await postJson(`/api/lab/guided-question-proposals/${encodeURIComponent(proposalId)}/approve`, {
      actor_role: "admin",
      note: "Approved as guided question governance proposal. No runtime mutation.",
    });
  } else {
    return;
  }
  $("gqProposalStatus").textContent = `${action}: ${result.item?.proposal_id || proposalId} · ${result.item?.status || result.code || ""} · no runtime mutation`;
  await loadGuidedQuestionProposals();
}

async function handleRevisionAction(revisionId, action) {
  if (!revisionId || !action) return;
  const role = $("revisionReviewerRole").value;
  let result;
  if (action === "validate") {
    result = await postJson(`/api/lab/revisions/${encodeURIComponent(revisionId)}/validate`, {});
  } else if (action === "approve") {
    result = await postJson(`/api/lab/revisions/${encodeURIComponent(revisionId)}/approve`, {
      actor_role: role,
      note: "Analyst/admin approval after validation. No runtime rule mutation.",
    });
  } else if (action === "activate") {
    result = await postJson(`/api/lab/revisions/${encodeURIComponent(revisionId)}/activate`, {
      actor_role: role,
      note: "Recorded as active revision governance record only; runtime inference unchanged.",
    });
  } else {
    return;
  }
  const item = result.item || {};
  $("revisionStatus").textContent = `${action}: ${result.status || item.status || "ok"} · ${item.revision_id || revisionId} · no runtime mutation`;
  await Promise.all([loadRevisions(), loadActiveRevisions()]);
}
