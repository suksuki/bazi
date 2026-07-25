import { approvedStage, loadApprovedScene } from "../s0-shared/scene-runtime.js";

const dom = {
  app: document.querySelector("#xiangfaApp"),
  modeButtons: [...document.querySelectorAll("[data-mode-value]")],
  stageButtons: [...document.querySelectorAll("[data-stage-value]")],
  hotspots: [...document.querySelectorAll("[data-semantic-ref]")],
  stageEyebrow: document.querySelector("#stageEyebrow"),
  stageHeadline: document.querySelector("#stageHeadline"),
  selectionKind: document.querySelector("#selectionKind"),
  selectionTitle: document.querySelector("#selectionTitle"),
  selectionExplanation: document.querySelector("#selectionExplanation"),
  semanticRef: document.querySelector("#semanticRef"),
  abuLine: document.querySelector("#abuLine"),
};

let packageData;
let currentStage = "original";
let currentMode = "xiangfa";
let currentRef = "path-committed-output-pressure";

boot();

async function boot() {
  try {
    packageData = await loadApprovedScene();
    bindControls();
    const params = new URLSearchParams(location.search);
    const requestedStage = params.get("stage");
    const requestedMode = params.get("mode");
    if (["original", "luck", "year"].includes(requestedStage)) currentStage = requestedStage;
    if (["xiangfa", "skeleton", "overlay"].includes(requestedMode)) currentMode = requestedMode;
    render();
    selectRef(currentRef);
  } catch (error) {
    dom.stageHeadline.textContent = "批准场景没有载入";
    dom.selectionTitle.textContent = String(error);
    for (const button of [...dom.modeButtons, ...dom.stageButtons, ...dom.hotspots]) button.disabled = true;
  }
}

function bindControls() {
  for (const button of dom.modeButtons) {
    button.addEventListener("click", () => {
      currentMode = button.dataset.modeValue;
      render();
    });
  }
  for (const button of dom.stageButtons) {
    button.addEventListener("click", () => {
      currentStage = button.dataset.stageValue;
      currentRef = stageDefaultRef(currentStage);
      render();
      selectRef(currentRef);
    });
  }
  for (const hotspot of dom.hotspots) {
    hotspot.addEventListener("click", () => selectRef(hotspot.dataset.semanticRef));
  }
}

function render() {
  dom.app.dataset.mode = currentMode;
  dom.app.dataset.stage = currentStage;
  for (const button of dom.modeButtons) button.setAttribute("aria-pressed", String(button.dataset.modeValue === currentMode));
  for (const button of dom.stageButtons) button.setAttribute("aria-current", String(button.dataset.stageValue === currentStage));
  const stage = approvedStage(packageData.source, currentStage);
  dom.stageEyebrow.textContent = stage.label;
  dom.stageHeadline.textContent = stage.shortLabel.replace(`${stage.label}：`, "");
}

function selectRef(ref) {
  currentRef = ref;
  for (const hotspot of dom.hotspots) hotspot.classList.toggle("is-selected", hotspot.dataset.semanticRef === ref);
  const detail = detailFor(ref);
  dom.selectionKind.textContent = detail.kind;
  dom.selectionTitle.textContent = detail.title;
  dom.selectionExplanation.textContent = detail.explanation;
  dom.semanticRef.textContent = ref;
  dom.abuLine.textContent = detail.abu;
}

function detailFor(ref) {
  const source = packageData.source;
  const natal = approvedStage(source, "original");
  const luck = approvedStage(source, "luck");
  const year = approvedStage(source, "year");
  const details = {
    "path-committed-output-pressure": {
      kind: "正式主路径 · analyst approved teaching projection",
      title: natal.explanation,
      explanation: currentStage === "original" ? "路径从左侧的乙木生发主体出发，经由中央丁火转化节点，最终作用于右侧金结构。" : approvedStage(source, currentStage).explanation,
      abu: currentStage === "luck" ? "这条路只是变弱，并没有中断。" : currentStage === "year" ? "这里的增强只相对庚子阶段，不表示超过原局。" : "沿着发光路径看，就能找到这一幕的结构主线。",
    },
    "node-stem-day-yi": {
      kind: "路径节点 · node-stem-day-yi",
      title: "乙木是这条正式主路径的生发源端。",
      explanation: currentStage === "luck" ? luck.explanation : "它从场景左侧进入路径，并向丁火节点传递。",
      abu: currentStage === "luck" ? "庚作用在这里，所以向丁火的流动变弱，但没有断。" : "这是我们理解整条路径时首先要找到的起点。",
    },
    "node-stem-year-ding": {
      kind: "路径节点 · node-stem-year-ding",
      title: "丁火是承接乙木、继续作用于金结构的转化中心。",
      explanation: currentStage === "year" ? year.explanation : "场景中央的灯火承接左侧生发，并把路径继续引向右侧结构。",
      abu: currentStage === "year" ? "丙在这一阶段支持丁火，所以路径相对庚子重新获得支持。" : "它不是装饰灯火，而是正式路径中的同一个丁火节点。",
    },
    "node-metal-structure": {
      kind: "候选结构边界 · node-metal-structure",
      title: "金结构是这条教学路径的作用边界。",
      explanation: source.approved_natal_path.terminal_uncertainty,
      abu: "这里保留了条件性，不把候选结构说成无条件完全合化。",
    },
    "relation-luck-geng-controls-yi": {
      kind: "庚子阶段关系 · weakened",
      title: "庚作用于乙木路径源端。",
      explanation: luck.explanation,
      abu: "我不会在这一步补画子水的独立作用，也不会把减弱演成阻断。",
    },
    "relation-year-bing-supports-ding": {
      kind: "丙午阶段关系 · reinforced",
      title: "丙支持丁火路径节点。",
      explanation: year.explanation,
      abu: "这一幕只演丙对丁的支持，不补画午支的独立作用。",
    },
  };
  return details[ref] || details["path-committed-output-pressure"];
}

function stageDefaultRef(stage) {
  if (stage === "luck") return "relation-luck-geng-controls-yi";
  if (stage === "year") return "relation-year-bing-supports-ding";
  return "path-committed-output-pressure";
}
