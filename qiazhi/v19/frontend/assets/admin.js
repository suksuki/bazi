const $ = (id) => document.getElementById(id);

let current = null;
let models = [];
let chatModels = [];
let latestSyntheticDrafts = [];

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

$("seedP14ReviewBatches").addEventListener("click", async () => {
  const result = await postJson("/api/lab/knowledge-review-batches/seed-p14", {});
  $("kbReviewBatchStatus").textContent = `P14 batches: created ${result.created_count || 0} · skipped ${result.skipped_count || 0} · no draft status mutation`;
  await loadKnowledgeReviewBatches();
});

$("seedP21ReviewBatches").addEventListener("click", async () => {
  const result = await postJson("/api/lab/knowledge-review-batches/seed-p21", {});
  $("kbReviewBatchStatus").textContent = `P21 batches: created ${result.created_count || 0} · skipped ${result.skipped_count || 0} · new KB drafts only`;
  await loadKnowledgeReviewBatches();
});

$("createKbReviewBatch").addEventListener("click", async () => {
  const result = await postJson("/api/lab/knowledge-review-batches", {
    batch_name: $("kbReviewBatchName").value,
    knowledge_id_prefix: $("kbReviewBatchPrefix").value,
    risk_levels: $("kbReviewBatchRiskLevels").value,
    draft_ids: $("kbReviewBatchDraftIds").value,
    recommended_action: $("kbReviewBatchAction").value,
    actor_role: "admin",
  });
  $("kbReviewBatchStatus").textContent = `batch: ${result.item?.batch_id || result.code || ""} · ${result.item?.summary?.draft_count || result.message || ""}`;
  await loadKnowledgeReviewBatches();
});

$("reloadKbReviewBatches").addEventListener("click", () => loadKnowledgeReviewBatches());

$("createKbBatchProposalDrafts").addEventListener("click", async () => {
  const batchId = $("kbProposalBatchId").value.trim();
  if (!batchId) {
    $("kbBatchProposalStatus").textContent = "请先填写 Batch ID / Key。";
    return;
  }
  const result = await postJson(`/api/lab/knowledge-review-batches/${encodeURIComponent(batchId)}/proposal-drafts`, {
    actor_role: $("kbProposalActorRole").value,
    source_question_key: $("kbProposalSourceQuestion").value,
    note: $("kbProposalNote").value,
  });
  const item = result.item || {};
  $("kbBatchProposalStatus").textContent = `${item.status || result.code || "proposal_drafts"} · rules ${item.summary?.rule_proposal_count || 0} · questions ${item.summary?.question_proposal_count || 0} · blocked ${item.summary?.blocked_count || 0}`;
  await Promise.all([loadKnowledgeBatchProposalRuns(), loadBaziRuleProposals(), loadGuidedQuestionProposals()]);
});

$("reloadKbBatchProposalRuns").addEventListener("click", () => loadKnowledgeBatchProposalRuns());

$("createProposalValidationRun").addEventListener("click", async () => {
  const result = await postJson("/api/lab/proposal-validation-runs", {
    actor_role: $("proposalValidationActorRole").value,
    source_run_id: $("proposalValidationSourceRunId").value,
    batch_key: $("proposalValidationBatchKey").value,
    statuses: $("proposalValidationStatuses").value,
    proposal_ids: $("proposalValidationIds").value,
    note: "P17 schema validation only. No approval, version record, or runtime mutation.",
  });
  const item = result.item || {};
  $("proposalValidationStatus").textContent = `${item.status || result.code || "validation"} · passed ${item.summary?.passed || 0}/${item.summary?.total || 0} · failed ${item.summary?.failed || 0}`;
  await Promise.all([loadProposalValidationRuns(), loadBaziRuleProposals(), loadGuidedQuestionProposals()]);
});

$("reloadProposalValidationRuns").addEventListener("click", () => loadProposalValidationRuns());

$("createProposalReviewPacket").addEventListener("click", async () => {
  const result = await postJson("/api/lab/proposal-review-packets", {
    actor_role: $("proposalReviewActorRole").value,
    validation_run_id: $("proposalReviewValidationRunId").value,
    source_run_id: $("proposalReviewSourceRunId").value,
    batch_key: $("proposalReviewBatchKey").value,
    note: $("proposalReviewNote").value,
  });
  const item = result.item || {};
  $("proposalReviewStatus").textContent = `${item.status || result.code || "review_packet"} · items ${item.summary?.total || 0} · passed ${item.summary?.validation_passed || 0} · blocked ${item.summary?.validation_failed || 0}`;
  await loadProposalReviewPackets();
});

$("createP21ReviewPacket").addEventListener("click", async () => {
  $("p21ReviewPacketStatus").textContent = "running P22 P21 review packet pipeline...";
  const result = await postJson("/api/lab/p21/review-packet", {
    actor_role: "admin",
    source_question_key: "q_income_stability",
    note: "P22 P21 R1 review packet. Human approval required; no runtime mutation.",
  });
  renderP21ReviewPacket(result);
  await Promise.all([loadKnowledgeReviewBatches(), loadKnowledgeBatchProposalRuns(), loadProposalValidationRuns(), loadProposalReviewPackets(), loadBaziRuleProposals(), loadGuidedQuestionProposals()]);
});

$("reloadProposalReviewPackets").addEventListener("click", () => loadProposalReviewPackets());

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

$("loadStructuralSignals")?.addEventListener("click", () => loadStructuralSignals());

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

$("createGovernanceRelease").addEventListener("click", async () => {
  const result = await postJson("/api/lab/governance-releases", {
    knowledge_draft_ids: $("releaseKnowledgeDraftIds").value,
    guided_question_version_ids: $("releaseGqVersionIds").value,
    bazi_rule_version_ids: $("releaseRuleVersionIds").value,
    active_revision_ids: $("releaseActiveRevisionIds").value,
    note: $("releaseNote").value,
    actor_role: "admin",
  });
  $("governanceReleaseStatus").textContent = `release: ${result.item?.release_id || result.code || ""} · ${result.item?.status || result.message || ""} · P11 gate required`;
  await loadGovernanceReleases();
});

$("reloadGovernanceReleases").addEventListener("click", () => loadGovernanceReleases());

$("ingestBaziRuleDb").addEventListener("click", async () => {
  const result = await postJson("/api/admin/bazi-rule-db/ingest-current", { force: false, enable_engine: true });
  $("ruleDbStatus").textContent = `ingested: +${result.imported_count || 0} / updated ${result.updated_count || 0} · blocked ${result.blocked_count || 0} · rules ${result.rule_count || 0}`;
  await loadBaziRuleDb();
});

$("executeP26KnowledgeToRules").addEventListener("click", async () => {
  const result = await postJson("/api/lab/p26/knowledge-to-rules", {
    actor_role: "admin",
    enable_engine: true,
    note: "P26 fast path: seed new knowledge pack, version approved proposals, ingest knowledge drafts into Rule DB.",
  });
  const summary = result.summary || {};
  $("ruleDbStatus").textContent = `P26 ${result.status || ""}: p26 drafts ${summary.p26_draft_count || 0} · versions ${summary.version_record_created ? "created" : "none"} · Rule DB ${summary.rule_db_rule_count || 0}`;
  await Promise.all([loadBaziRuleDb(), loadKnowledgeDrafts(), loadBaziRuleVersions(), loadGuidedQuestionVersions()]);
});

$("executeP27SmartRuleGate").addEventListener("click", async () => {
  const result = await postJson("/api/lab/p27/smart-rule-gate", {
    actor_role: "admin",
    activate: true,
    prefixes: "p27.",
    max_risk_level: "R1",
    min_confidence: 0.72,
    limit: 12,
    note: "P27 smart gate: activate low-risk rule candidates only after P11 synthetic regression passes.",
  });
  const summary = result.summary || {};
  const pre = result.pre_regression?.status || "";
  const post = result.post_regression?.status || "";
  $("ruleDbStatus").textContent = `P27 ${result.status || ""}: drafts ${summary.p27_draft_count || 0} · candidates ${summary.candidate_count || 0} · activated ${summary.activated_count || 0} · rollback ${summary.rolled_back_count || 0} · P11 ${pre}/${post}`;
  await Promise.all([loadBaziRuleDb(), loadKnowledgeDrafts()]);
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

$("runSyntheticCollision").addEventListener("click", () => runSyntheticCollisionReview());

$("runQuestionDiversityAudit").addEventListener("click", () => loadQuestionDiversityAudit());

$("reloadSyntheticPromotions").addEventListener("click", () => loadSyntheticPromotions());

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
  await loadKnowledgeReviewBatches();
  await loadKnowledgeBatchProposalRuns();
  await loadProposalValidationRuns();
  await loadProposalReviewPackets();
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

async function loadKnowledgeReviewBatches() {
  const result = await fetch("/api/lab/knowledge-review-batches").then((response) => response.json());
  $("kbReviewBatchStatus").textContent = `knowledge review batches: ${result.count || 0} · no draft status mutation`;
  renderKnowledgeReviewBatches(result.items || []);
}

async function loadKnowledgeBatchProposalRuns() {
  const result = await fetch("/api/lab/knowledge-batch-proposal-runs").then((response) => response.json());
  $("kbBatchProposalStatus").textContent = `P16 runs: ${result.count || 0} · proposal drafts only`;
  renderKnowledgeBatchProposalRuns(result.items || []);
}

async function loadProposalValidationRuns() {
  const result = await fetch("/api/lab/proposal-validation-runs").then((response) => response.json());
  $("proposalValidationStatus").textContent = `P17 validation runs: ${result.count || 0} · validation only`;
  renderProposalValidationRuns(result.items || []);
}

async function loadProposalReviewPackets() {
  const result = await fetch("/api/lab/proposal-review-packets").then((response) => response.json());
  const decisionCount = (result.items || []).reduce((total, item) => total + Number((item.decision_summary || {}).total || 0), 0);
  const preflightCount = (result.items || []).reduce((total, item) => total + Number((item.approval_preflight_summary || {}).total || 0), 0);
  const approvalCount = (result.items || []).reduce((total, item) => total + Number((item.approval_execution_summary || {}).total || 0), 0);
  $("proposalReviewStatus").textContent = `P18 review packets: ${result.count || 0} · decisions ${decisionCount} · preflights ${preflightCount} · approvals ${approvalCount} · no runtime`;
  renderProposalReviewPackets(result.items || []);
}

async function recordProposalReviewPacketDecision(packetId, proposalId = "") {
  if (!packetId) {
    return;
  }
  const scopedProposalId = proposalId || $("proposalPacketDecisionProposalId").value;
  $("proposalPacketDecisionProposalId").value = scopedProposalId;
  const result = await postJson(`/api/lab/proposal-review-packets/${encodeURIComponent(packetId)}/decisions`, {
    actor_role: $("proposalReviewActorRole").value,
    decision: $("proposalPacketDecision").value,
    proposal_id: scopedProposalId,
    note: $("proposalPacketDecisionNote").value,
  });
  const item = result.item || {};
  const summary = item.decision_summary || {};
  $("proposalReviewStatus").textContent = `${item.packet_id || packetId} · P23 decisions ${summary.total || 0} · ${result.ok ? "ledger only" : result.code || "blocked"}`;
  await Promise.all([loadProposalReviewPackets(), loadBaziRuleProposals(), loadGuidedQuestionProposals()]);
}

async function runProposalReviewApprovalPreflight(packetId) {
  if (!packetId) {
    return;
  }
  const result = await postJson(`/api/lab/proposal-review-packets/${encodeURIComponent(packetId)}/approval-preflight`, {
    actor_role: $("proposalReviewActorRole").value,
    note: "P24 approval preflight report only. No approval, version record, or runtime mutation.",
  });
  const item = result.item || {};
  const summary = item.summary || {};
  $("proposalReviewStatus").textContent = `${item.status || result.code || "preflight"} · ready ${summary.ready_item_count || 0}/${summary.item_count || 0} · failed checks ${summary.failed_checks || 0}`;
  await loadProposalReviewPackets();
}

async function executeProposalReviewApproval(packetId) {
  if (!packetId) {
    return;
  }
  const result = await postJson(`/api/lab/proposal-review-packets/${encodeURIComponent(packetId)}/controlled-approval`, {
    actor_role: $("proposalReviewActorRole").value,
    note: "P25 controlled approval. Proposal status only; no version record or runtime mutation.",
  });
  const item = result.item || {};
  const summary = item.summary || {};
  $("proposalReviewStatus").textContent = `${item.status || result.code || "approval"} · approved ${summary.approved_count || 0}/${summary.item_count || 0} · failed ${summary.failed_count || 0} · ${result.reused ? "reused" : "executed"}`;
  await Promise.all([loadProposalReviewPackets(), loadBaziRuleProposals(), loadGuidedQuestionProposals(), loadBaziRuleVersions(), loadGuidedQuestionVersions()]);
}

async function loadLab() {
  const status = await fetch("/api/lab/status").then((response) => response.json());
  $("feedbackStatus").textContent = `feedback: ${status.counts?.feedback || 0} · guardrail: no auto learning`;
  $("ruleImpactStatus").textContent = `rule impacts: ${status.counts?.rule_impacts || 0} · attribution only`;
  $("revisionStatus").textContent = `revision proposals: ${status.counts?.revision_proposals || 0} · validation gated · no runtime mutation`;
  $("promotionStatus").textContent = `review queue: ${status.counts?.promotion_requests || 0} · no auto promotion`;
  $("validationStatus").textContent = `validation cases: ${status.counts?.validation_cases || 0}`;
  $("syntheticPromotionStatus").textContent = `synthetic promotion candidates: ${status.counts?.synthetic_promotion_candidates || 0} · P11 regression gate required`;
  $("guidedQuestionStatusLine").textContent = `guided question feedback: ${status.counts?.guided_question_feedback || 0} · reviews: ${status.counts?.guided_question_reviews || 0}`;
  $("gqProposalStatus").textContent = `guided question proposals: ${status.counts?.guided_question_proposals || 0} · versions: ${status.counts?.guided_question_library_versions || 0}`;
  $("baziRuleStatus").textContent = `bazi rule proposals: ${status.counts?.bazi_rule_proposals || 0} · versions: ${status.counts?.bazi_rule_versions || 0}`;
  $("governanceReleaseStatus").textContent = `governance releases: ${status.counts?.governance_releases || 0} · manifest only`;
  $("kbBatchProposalStatus").textContent = `P16 runs: ${status.counts?.knowledge_batch_proposal_runs || 0} · R1 proposal draft gate`;
  $("proposalValidationStatus").textContent = `P17 validation runs: ${status.counts?.proposal_validation_runs || 0} · validation only`;
  $("proposalReviewStatus").textContent = `P18 review packets: ${status.counts?.proposal_review_packets || 0} · decisions ${status.counts?.proposal_review_packet_decisions || 0} · preflights ${status.counts?.proposal_review_approval_preflights || 0} · approvals ${status.counts?.proposal_review_approval_executions || 0} · no runtime`;
  await Promise.all([loadFeedback(), loadGuidedQuestionFeedback(), loadAnswerQuality(), loadRuleImpacts(), loadRevisions(), loadActiveRevisions(), loadGuidedQuestionProposals(), loadGuidedQuestionVersions(), loadBaziRuleProposals(), loadBaziRuleVersions(), loadGovernanceReleases(), loadProposalValidationRuns(), loadProposalReviewPackets(), loadBaziRuleDb(), loadPromotions(), loadValidationCases(), loadLabels(), loadSyntheticCollisionReview(), loadQuestionDiversityAudit(), loadSyntheticPromotions()]);
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

async function loadStructuralSignals() {
  const yearValue = Number($("structuralSignalYear")?.value || 2026);
  const selectedYear = Number.isFinite(yearValue) ? yearValue : 2026;
  const profileId = ($("structuralSignalProfileId")?.value || "").trim();
  const payload = {
    selected_year: selectedYear,
    ...(profileId
      ? { profile_id: profileId }
      : {
          birth_input: {
            year: 1990,
            month: 11,
            day: 13,
            hour: 12,
            gender: "male",
            calendar_type: "solar",
          },
        }),
  };
  $("structuralSignalStatus").textContent = "loading structural rule signals...";
  $("structuralSignalList").innerHTML = "";
  try {
    const result = await fetch("/api/lab/structural-rule-signals?role=admin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((response) => response.json());
    const data = result.data || result;
    const report = data.structural_rule_signals || data.report || data;
    renderStructuralSignals(report);
  } catch (error) {
    $("structuralSignalStatus").textContent = `structural signals failed: ${error?.message || error}`;
    $("structuralSignalList").innerHTML = "<div class=\"knowledge-empty\">Unable to load Structural Rule Signals.</div>";
  }
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

async function loadGovernanceReleases() {
  const result = await fetch("/api/lab/governance-releases").then((response) => response.json());
  $("governanceReleaseStatus").textContent = `governance releases: ${result.count || 0} · manifest only · no runtime mutation`;
  renderGovernanceReleases(result.items || []);
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

async function loadSyntheticCollisionReview() {
  const result = await fetch("/api/lab/synthetic-collision").then((response) => response.json());
  renderSyntheticCollisionReview(result);
}

async function runSyntheticCollisionReview() {
  $("syntheticCollisionStatus").textContent = "running P11 synthetic collision...";
  $("syntheticCollisionFailures").innerHTML = "";
  $("syntheticCollisionDrafts").innerHTML = "";
  const result = await postJson("/api/lab/synthetic-collision/run", {});
  renderSyntheticCollisionReview(result);
}

async function loadQuestionDiversityAudit() {
  $("questionDiversityStatus").textContent = "running P20 guided question diversity audit...";
  const result = await fetch("/api/lab/guided-question-diversity-audit").then((response) => response.json());
  renderQuestionDiversityAudit(result);
}

async function loadSyntheticPromotions() {
  const result = await fetch("/api/lab/synthetic-promotions").then((response) => response.json());
  $("syntheticPromotionStatus").textContent = `synthetic promotion candidates: ${result.count || 0} · no auto promotion`;
  renderSyntheticPromotions(result.items || []);
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

function renderKnowledgeReviewBatches(items) {
  const box = $("kbReviewBatchList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No knowledge review batches yet.</div>";
    return;
  }
  box.innerHTML = items.map((item) => {
    const summary = item.summary || {};
    const byRisk = summary.by_risk_level || {};
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.batch_key || item.batch_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
      <h3>${escapeHtml(item.batch_name || "")} · ${escapeHtml(String(summary.draft_count || 0))} draft(s)</h3>
      <p>${escapeHtml(item.note || item.recommended_action || "")}</p>
      <div class="knowledge-guard">risk: ${escapeHtml(JSON.stringify(byRisk))} · domains: ${escapeHtml((item.domains || []).join(", ") || "-")}</div>
      <div class="knowledge-guard">action: ${escapeHtml(item.recommended_action || "")} · no draft status mutation</div>
      <div class="knowledge-guard">knowledge: ${escapeHtml((item.knowledge_ids || []).slice(0, 10).join(", ") || "-")}</div>
    </article>`;
  }).join("");
}

function renderKnowledgeBatchProposalRuns(items) {
  const box = $("kbBatchProposalRunList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No P16 proposal runs yet.</div>";
    return;
  }
  box.innerHTML = items.map((item) => {
    const summary = item.summary || {};
    const ruleIds = (item.rule_proposals || []).map((row) => row.proposal_id || row.rule_id).filter(Boolean);
    const questionIds = (item.guided_question_proposals || []).map((row) => row.proposal_id || row.question_key).filter(Boolean);
    const blocked = (item.blocked_items || []).map((row) => row.knowledge_id || row.draft_id).filter(Boolean);
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.batch_key || item.batch_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
      <h3>${escapeHtml(item.run_id || "")} · rules ${escapeHtml(String(summary.rule_proposal_count || 0))} · questions ${escapeHtml(String(summary.question_proposal_count || 0))}</h3>
      <p>${escapeHtml(item.note || item.blocked_reason || "")}</p>
      <div class="knowledge-guard">rule proposals: ${escapeHtml(ruleIds.slice(0, 8).join(", ") || "-")}</div>
      <div class="knowledge-guard">question proposals: ${escapeHtml(questionIds.slice(0, 4).join(", ") || "-")}</div>
      <div class="knowledge-guard">blocked: ${escapeHtml(blocked.slice(0, 8).join(", ") || "-")} · no runtime mutation</div>
    </article>`;
  }).join("");
}

function renderProposalValidationRuns(items) {
  const box = $("proposalValidationRunList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No P17 validation runs yet.</div>";
    return;
  }
  box.innerHTML = items.map((item) => {
    const summary = item.summary || {};
    const failed = (item.items || []).filter((row) => row.passed !== true).map((row) => row.proposal_id || row.rule_id || row.question_key).filter(Boolean);
    const passed = (item.items || []).filter((row) => row.passed === true).map((row) => row.proposal_id || row.rule_id || row.question_key).filter(Boolean);
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.validation_run_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
      <h3>${escapeHtml(String(summary.passed || 0))}/${escapeHtml(String(summary.total || 0))} passed · failed ${escapeHtml(String(summary.failed || 0))}</h3>
      <p>${escapeHtml(item.note || "")}</p>
      <div class="knowledge-guard">source: ${escapeHtml(item.source_run_id || item.batch_key || "-")} · validation only</div>
      <div class="knowledge-guard">passed: ${escapeHtml(passed.slice(0, 8).join(", ") || "-")}</div>
      <div class="knowledge-guard">failed: ${escapeHtml(failed.slice(0, 8).join(", ") || "-")} · no approval</div>
    </article>`;
  }).join("");
}

function renderProposalReviewPackets(items) {
  const box = $("proposalReviewPacketList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No P18 review packets yet.</div>";
    return;
  }
  box.innerHTML = items.map((item) => {
    const summary = item.summary || {};
    const decisionSummary = item.decision_summary || {};
    const latestDecision = item.latest_decision_record || {};
    const preflightSummary = item.approval_preflight_summary || {};
    const latestPreflight = item.latest_approval_preflight_record || {};
    const approvalSummary = item.approval_execution_summary || {};
    const latestApproval = item.latest_approval_execution_record || {};
    const proposalIds = (item.items || []).map((row) => row.proposal_id || row.rule_id || row.question_key).filter(Boolean);
    const reviewItems = (item.items || []).map((row) => {
      const latestItemDecision = row.latest_review_decision || {};
      const displayId = row.proposal_id || row.rule_id || row.question_key || "";
      return `<div class="knowledge-guard">
        ${escapeHtml(row.kind || "proposal")} · ${escapeHtml(displayId)} · status ${escapeHtml(row.proposal_status || "")} · validation ${row.validation_passed ? "pass" : "fail"} · item decision ${escapeHtml(latestItemDecision.decision || "pending")}
        <button type="button" class="secondary" data-proposal-packet-item-decision="${escapeHtml(item.packet_id || "")}" data-proposal-id="${escapeHtml(row.proposal_id || "")}">记录条目 Decision</button>
      </div>`;
    }).join("");
    const canRecordDecision = item.status === "approval_review_ready" || item.status === "blocked_by_validation";
    const canExecuteApproval = (latestPreflight.status || preflightSummary.latest_status) === "approval_preflight_ready" && (latestApproval.status || approvalSummary.latest_status) !== "controlled_approval_executed";
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.packet_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
      <h3>${escapeHtml(String(summary.validation_passed || 0))}/${escapeHtml(String(summary.total || 0))} ready for human review</h3>
      <p>${escapeHtml(item.note || item.blocked_reason || "")}</p>
      <div class="knowledge-guard">validation: ${escapeHtml(item.validation_run_id || "-")} · decision: ${escapeHtml(item.recommended_decision || "")}</div>
      <div class="knowledge-guard">P23 decisions: ${escapeHtml(String(decisionSummary.total || 0))} · latest: ${escapeHtml(latestDecision.decision || decisionSummary.latest_decision || "pending")}</div>
      <div class="knowledge-guard">P24 preflight: ${escapeHtml(latestPreflight.status || preflightSummary.latest_status || "not_run")} · ready ${escapeHtml(String(preflightSummary.latest_ready_item_count || 0))}/${escapeHtml(String(preflightSummary.latest_item_count || 0))}</div>
      <div class="knowledge-guard">P25 approval: ${escapeHtml(latestApproval.status || approvalSummary.latest_status || "not_run")} · approved ${escapeHtml(String(approvalSummary.latest_approved_count || 0))}/${escapeHtml(String(approvalSummary.latest_item_count || 0))}</div>
      <div class="knowledge-guard">proposals: ${escapeHtml(proposalIds.slice(0, 10).join(", ") || "-")}</div>
      ${reviewItems}
      <div class="knowledge-guard">controlled approval only · no version record · no runtime mutation</div>
      <div class="button-row">
        <button type="button" data-proposal-packet-decision="${escapeHtml(item.packet_id || "")}" ${canRecordDecision ? "" : "disabled"}>记录 P23 Decision</button>
        <button type="button" class="secondary" data-proposal-packet-preflight="${escapeHtml(item.packet_id || "")}">运行 P24 Preflight</button>
        <button type="button" class="secondary" data-proposal-packet-approval="${escapeHtml(item.packet_id || "")}" ${canExecuteApproval ? "" : "disabled"}>执行 P25 Approval</button>
      </div>
    </article>`;
  }).join("");
  box.querySelectorAll("[data-proposal-packet-decision]").forEach((button) => {
    button.addEventListener("click", () => recordProposalReviewPacketDecision(button.dataset.proposalPacketDecision || ""));
  });
  box.querySelectorAll("[data-proposal-packet-item-decision]").forEach((button) => {
    button.addEventListener("click", () => recordProposalReviewPacketDecision(button.dataset.proposalPacketItemDecision || "", button.dataset.proposalId || ""));
  });
  box.querySelectorAll("[data-proposal-packet-preflight]").forEach((button) => {
    button.addEventListener("click", () => runProposalReviewApprovalPreflight(button.dataset.proposalPacketPreflight || ""));
  });
  box.querySelectorAll("[data-proposal-packet-approval]").forEach((button) => {
    button.addEventListener("click", () => executeProposalReviewApproval(button.dataset.proposalPacketApproval || ""));
  });
}

function renderP21ReviewPacket(payload) {
  const summary = payload.summary || {};
  const proposal = payload.proposal_run || {};
  const validation = payload.validation_run || {};
  const packet = payload.review_packet || {};
  const r2Gate = payload.r2_gate || {};
  $("p21ReviewPacketStatus").textContent = `P22 ${payload.status || "-"} · R1 proposals ${summary.r1_rule_proposal_count || 0}+${summary.r1_question_proposal_count || 0} · validation ${summary.validation_passed || 0}/${summary.validation_total || 0} · R2 blocked ${summary.r2_blocked_count || 0}`;
  $("p21ReviewPacketList").innerHTML = `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(payload.stage || "P22")}</span><strong>${escapeHtml(payload.status || "")}</strong></div>
    <h3>${escapeHtml(packet.packet_id || "review packet")}</h3>
    <p>R1 enters review packet only. R2 remains blocked before analyst/source review.</p>
    <div class="knowledge-guard">proposal run: ${escapeHtml(proposal.run_id || "-")} · validation: ${escapeHtml(validation.validation_run_id || "-")}</div>
    <div class="knowledge-guard">packet: ${escapeHtml(packet.status || "-")} · decision: ${escapeHtml(packet.recommended_decision || "human review required")}</div>
    <div class="knowledge-guard">R2 gate: ${escapeHtml(r2Gate.reason || "-")} · eligible: ${r2Gate.eligible ? "yes" : "no"}</div>
    <div class="knowledge-guard">${(payload.guardrails || []).map((item) => escapeHtml(item)).join(" · ")}</div>
  </article>`;
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

function renderSyntheticCollisionReview(payload) {
  const run = payload.run || payload;
  const summary = run.summary || {};
  const review = run.collision_review || {};
  const report = run.evolution_report || {};
  const cases = run.cases || [];
  const failures = cases.filter((item) => item.status === "fail");
  $("syntheticCollisionStatus").textContent = `P11 ${run.status || "-"} · ${summary.passed || 0}/${summary.total || 0} passed · failures ${summary.failed || 0} · analyst review required for drafts`;

  $("syntheticCollisionSummary").innerHTML = `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(payload.matrix || "P11_SYNTHETIC_EXPANSION")}</span><strong>${escapeHtml(run.validation_run || "")}</strong></div>
    <h3>${escapeHtml(String(summary.total || 0))} synthetic case(s)</h3>
    <p>stable ${escapeHtml(String((review.stable_structures || []).length))} · misfire ${escapeHtml(String((review.misfire_structures || []).length))} · missing ${escapeHtml(String((review.missing_structures || []).length))}</p>
    <div class="knowledge-guard">${(run.boundaries || []).map((item) => escapeHtml(item)).join(" · ")}</div>
  </article>`;

  if (!failures.length) {
    $("syntheticCollisionFailures").innerHTML = "<div class=\"knowledge-empty\">No failing synthetic cases. Failed cases will appear here for analyst review.</div>";
  } else {
    $("syntheticCollisionFailures").innerHTML = failures.map((item) => {
      const failureText = (item.failures || []).map((failure) => `${failure.failure_type || ""}:${failure.expected || failure.forbidden || failure.message || ""}`).join(" · ");
      const tags = (item.knowledge_tags || item.observed?.standardized_knowledge_tags || []).join(", ");
      return `<article class="knowledge-item">
        <div class="knowledge-top"><span>${escapeHtml(item.case_id || "")}</span><strong>${escapeHtml(item.structure_label || "")}</strong></div>
        <h3>${escapeHtml(item.collision_focus || "")}</h3>
        <p>${escapeHtml(failureText || "failure recorded")}</p>
        <div class="knowledge-guard">knowledge tags: ${escapeHtml(tags || "-")}</div>
        <div class="knowledge-guard">preview: ${escapeHtml(item.observed?.text_preview || "")}</div>
      </article>`;
    }).join("");
  }

  const audits = report.audit_records || [];
  const drafts = report.draft_suggestions || [];
  latestSyntheticDrafts = drafts;
  if (!audits.length && !drafts.length) {
    $("syntheticCollisionDrafts").innerHTML = "<div class=\"knowledge-empty\">No audit or draft proposal generated. Matrix is currently stable.</div>";
    return;
  }
  const auditCards = audits.map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.audit_id || "")}</span><strong>${escapeHtml(item.attribution_layer || "")}</strong></div>
    <h3>${escapeHtml(item.case_id || "")}</h3>
    <p>${escapeHtml((item.failure_types || []).join(" · "))}</p>
    <div class="knowledge-guard">review: ${escapeHtml(item.review_status || "")} · ${escapeHtml((item.guardrails || []).join(" · "))}</div>
  </article>`);
  const draftCards = drafts.map((item, index) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.proposal_id || "")}</span><strong>${escapeHtml(item.draft_type || item.target || "")}</strong></div>
    <h3>${escapeHtml(item.case_id || "")}</h3>
    <p>${escapeHtml(item.suggested_action || "")}</p>
    <div class="knowledge-guard">layer: ${escapeHtml(item.attribution_layer || "")} · scope: ${escapeHtml(item.proposal_scope || "")}</div>
    <div class="button-row">
      <button type="button" class="secondary" data-synthetic-draft-index="${escapeHtml(String(index))}">Create Promotion Candidate</button>
    </div>
  </article>`);
  $("syntheticCollisionDrafts").innerHTML = auditCards.concat(draftCards).join("");
  $("syntheticCollisionDrafts").querySelectorAll("[data-synthetic-draft-index]").forEach((button) => {
    button.addEventListener("click", () => createSyntheticPromotionFromDraft(Number(button.dataset.syntheticDraftIndex || 0)));
  });
}

function renderQuestionDiversityAudit(payload) {
  const summary = payload.summary || {};
  const checks = payload.checks || [];
  const failures = payload.failures || [];
  const items = payload.items || [];
  $("questionDiversityStatus").textContent = `P20 ${payload.status || "-"} · labels ${summary.top_label_sequence_count || 0} · keys ${summary.top_key_sequence_count || 0} · old static top ${summary.old_static_top_present ? "present" : "absent"} · no runtime mutation`;

  $("questionDiversitySummary").innerHTML = `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(payload.matrix || "P11_SYNTHETIC_EXPANSION")}</span><strong>${escapeHtml(payload.status || "")}</strong></div>
    <h3>${escapeHtml(String(payload.case_count || 0))} synthetic case(s)</h3>
    <p>income top10 ${escapeHtml(String(summary.income_stability_top10_count || 0))} · KB changed top5 ${escapeHtml(String(summary.kb_augmented_change_count || 0))} · failures ${escapeHtml(String(summary.failure_count || 0))}</p>
    <div class="knowledge-guard">${checks.map((item) => `${escapeHtml(item.name || "")}:${item.passed ? "pass" : "fail"}`).join(" · ")}</div>
    <div class="knowledge-guard">${(payload.guardrails || []).map((item) => escapeHtml(item)).join(" · ")}</div>
  </article>`;

  const box = $("questionDiversityList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No diversity audit rows.</div>";
    return;
  }
  const failureCards = failures.map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.case_id || "")}</span><strong>${escapeHtml(item.failure_type || "")}</strong></div>
    <h3>P20 failure</h3>
    <p>${escapeHtml(item.message || (item.top_keys || []).join(" / ") || "")}</p>
    <div class="knowledge-guard">audit only · no automatic question library change</div>
  </article>`);
  const auditCards = items.slice(0, 12).map((item) => `<article class="knowledge-item">
    <div class="knowledge-top"><span>${escapeHtml(item.case_id || "")}</span><strong>${escapeHtml(item.structure_label || "")}</strong></div>
    <h3>${escapeHtml(item.collision_focus || "")}</h3>
    <p>${escapeHtml((item.top_labels || []).join(" / "))}</p>
    <div class="knowledge-guard">keys: ${escapeHtml((item.top_keys || []).join(" / "))}</div>
    <div class="knowledge-guard">income top10: ${item.income_stability_in_top_10 ? "yes" : "no"} · old static: ${item.old_static_top_match ? "yes" : "no"}</div>
  </article>`);
  box.innerHTML = failureCards.concat(auditCards).join("");
}

function renderSyntheticPromotions(items) {
  const box = $("syntheticPromotionList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No synthetic promotion candidates.</div>";
    return;
  }
  box.innerHTML = items.map((item) => {
    const review = item.review_decision || {};
    const downstream = item.downstream_proposal || {};
    const canReview = item.status === "draft_review" || item.status === "analyst_review";
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.candidate_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
      <h3>${escapeHtml(item.case_id || "")} · ${escapeHtml(item.draft_type || item.target || "")}</h3>
      <p>${escapeHtml(item.suggested_action || "")}</p>
      <div class="knowledge-guard">decision: ${escapeHtml(review.decision || "pending")} · layer: ${escapeHtml(item.attribution_layer || "")}</div>
      <div class="knowledge-guard">downstream: ${escapeHtml(downstream.kind || "-")} ${escapeHtml(downstream.proposal_id || downstream.draft_id || downstream.knowledge_id || "")}</div>
      <div class="knowledge-guard">gate: P11 regression required before active/version record · runtime_mutation=false</div>
      <div class="button-row">
        <button type="button" data-synthetic-promotion-review="${escapeHtml(item.candidate_id || "")}" ${canReview ? "" : "disabled"}>Apply Decision</button>
      </div>
    </article>`;
  }).join("");
  box.querySelectorAll("[data-synthetic-promotion-review]").forEach((button) => {
    button.addEventListener("click", () => reviewSyntheticPromotion(button.dataset.syntheticPromotionReview || ""));
  });
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

function renderGovernanceReleases(items) {
  const box = $("governanceReleaseList");
  if (!items.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No governance release manifests yet.</div>";
    return;
  }
  box.innerHTML = items.map((item) => {
    const summary = item.summary || {};
    const byType = summary.by_artifact_type || {};
    const gate = item.p13_regression_gate || {};
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.release_id || "")}</span><strong>${escapeHtml(item.status || "")}</strong></div>
      <h3>${escapeHtml(String(summary.artifact_count || 0))} artifact(s) · ${escapeHtml(item.release_type || "")}</h3>
      <p>${escapeHtml(item.note || "")}</p>
      <div class="knowledge-guard">knowledge ${escapeHtml(String(byType.knowledge_drafts || 0))} · question versions ${escapeHtml(String(byType.guided_question_versions || 0))} · rule versions ${escapeHtml(String(byType.bazi_rule_versions || 0))} · active revisions ${escapeHtml(String(byType.active_revisions || 0))}</div>
      <div class="knowledge-guard">P11 gate: ${escapeHtml(String(Boolean(gate.passed)))} · ${escapeHtml(JSON.stringify(gate.summary || {}))}</div>
      <div class="knowledge-guard">runtime_mutation=${escapeHtml(String(Boolean(item.runtime_mutation)))} · ${(item.guardrails || []).map(escapeHtml).join(" · ")}</div>
    </article>`;
  }).join("");
}

function readableStructuralValue(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (Array.isArray(value)) return value.map(readableStructuralValue).join(" / ");
  if (typeof value === "object") {
    try {
      return JSON.stringify(value, null, 0);
    } catch {
      return String(value);
    }
  }
  return String(value);
}

function renderStructuralSignals(report = {}) {
  const box = $("structuralSignalList");
  const signals = Array.isArray(report.signals) ? report.signals : [];
  const facts = report.facts_summary || {};
  const count = report.count ?? signals.length;
  const version = report.version || report.signal_version || "p9";
  const mutated = signals.some((item) => item.mutates_result === true);
  $("structuralSignalStatus").innerHTML = [
    `<span class="pill">signals: ${escapeHtml(String(count))}</span>`,
    `<span class="pill">version: ${escapeHtml(String(version))}</span>`,
    `<span class="pill">${mutated ? "warning: mutation flag found" : "result mutation: false"}</span>`,
  ].join("");
  if (!signals.length) {
    box.innerHTML = "<div class=\"knowledge-empty\">No Structural Rule Signals for this chart/time context.</div>";
    return;
  }
  const factLine = Object.entries(facts)
    .filter(([, value]) => value !== null && value !== undefined && readableStructuralValue(value) !== "-")
    .map(([key, value]) => `${key}: ${readableStructuralValue(value)}`)
    .join(" · ");
  const factBlock = factLine
    ? `<article class="knowledge-item"><div class="knowledge-top"><span>fact summary</span><strong>read only</strong></div><p>${escapeHtml(factLine)}</p></article>`
    : "";
  box.innerHTML = `${factBlock}${signals.slice(0, 60).map((item) => {
    const observed = readableStructuralValue(item.observed || item.observed_facts || item.facts || {});
    const refs = readableStructuralValue(item.fact_refs || []);
    const scope = readableStructuralValue(item.answer_scope || []);
    const questions = readableStructuralValue(item.question_keys || []);
    return `<article class="knowledge-item">
      <div class="knowledge-top"><span>${escapeHtml(item.signal_id || item.rule_id || "")}</span><strong>${escapeHtml(item.category || item.domain || "structural_signal")}</strong></div>
      <h3>${escapeHtml(item.title || item.knowledge_id || item.rule_id || "")}</h3>
      <p>${escapeHtml(item.reason || item.statement || "")}</p>
      <div class="knowledge-guard">layer: ${escapeHtml(item.layer || "-")} · risk: ${escapeHtml(item.risk_level || "-")} · score: ${escapeHtml(String(item.score ?? "-"))}</div>
      <div class="knowledge-guard">observed: ${escapeHtml(observed)}</div>
      <div class="knowledge-guard">answer_scope: ${escapeHtml(scope)} · question_keys: ${escapeHtml(questions)}</div>
      <div class="knowledge-guard">source rule: ${escapeHtml(item.rule_id || "-")} · knowledge: ${escapeHtml(item.knowledge_id || "-")} · refs: ${escapeHtml(refs)}</div>
      <div class="knowledge-guard">mutates_result=${escapeHtml(String(Boolean(item.mutates_result)))} · source=${escapeHtml(item.source || "rule_db_adapter")}</div>
    </article>`;
  }).join("")}`;
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

async function createSyntheticPromotionFromDraft(index) {
  const draft = latestSyntheticDrafts[index];
  if (!draft) return;
  const result = await postJson("/api/lab/synthetic-promotions", { draft });
  $("syntheticPromotionStatus").textContent = `candidate: ${result.item?.candidate_id || result.code || ""} · review required · no auto learning`;
  await loadSyntheticPromotions();
}

async function reviewSyntheticPromotion(candidateId) {
  if (!candidateId) return;
  const result = await postJson(`/api/lab/synthetic-promotions/${encodeURIComponent(candidateId)}/review`, {
    decision: $("syntheticPromotionDecision").value,
    note: $("syntheticPromotionNote").value,
    actor_role: "admin",
  });
  const item = result.item || {};
  const downstream = result.downstream || item.downstream_proposal || {};
  $("syntheticPromotionStatus").textContent = `review: ${item.candidate_id || candidateId} · ${item.status || result.code || ""} · downstream ${downstream.kind || "-"} ${downstream.proposal_id || downstream.draft_id || ""}`;
  await Promise.all([loadSyntheticPromotions(), loadKnowledgeDrafts(), loadGuidedQuestionProposals(), loadBaziRuleProposals()]);
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
