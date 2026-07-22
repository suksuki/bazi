export type DreamLocale = "zh" | "en" | "ko";

const messages = {
  zh: {
    "dream.entry": "随阿布入梦",
    "dream.resume": "继续上次的梦",
    "dream.loading": "雾路正在显现",
    "dream.encounter.eyebrow": "阿布梦境 · 三树缘境",
    "dream.encounter.title": "三棵生命树，正安静地生长",
    "dream.encounter.lede": "一棵来自已授权的匿名真人档案，两棵来自明确标识的 Canonical NPC。选择一棵，只观察，不改写。",
    "dream.tree.choose": "走近这棵树",
    "dream.tree.eyebrow": "单树观察",
    "dream.tree.title": "一段生命，在雾里留下自己的形状",
    "dream.tree.lede": "树象只投影同一份正式命理状态，不会自行增加关系或结论。",
    "dream.mirror.open": "打开命盘镜",
    "dream.mirror.close": "回到树下",
    "dream.workspace.back": "回到生命世界",
    "dream.path.none_confirmed": "当前暂无已确认主路径",
    "dream.source.authorized_human": "已授权真人 · 匿名",
    "dream.source.canonical_npc": "Canonical NPC · 人工生命",
    "dream.unavailable.title": "这条梦路暂时没有开放",
    "dream.unavailable.detail": "只有三份真实、已授权且可撤回的匿名场景同时就绪时，阿布才会带你进入。",
    "dream.error.title": "雾路暂时看不清",
  },
  en: {
    "dream.entry": "Enter the dream with Abu",
    "dream.resume": "Continue the dream",
    "dream.loading": "The mist path is appearing",
    "dream.encounter.eyebrow": "Abu's Dream · Three Trees",
    "dream.encounter.title": "Three life trees are quietly growing",
    "dream.encounter.lede": "One tree is an authorized anonymous human scene; two are clearly identified Canonical NPCs. Observe, never rewrite.",
    "dream.tree.choose": "Approach this tree",
    "dream.tree.eyebrow": "Tree observation",
    "dream.tree.title": "A life leaves its own shape in the mist",
    "dream.tree.lede": "The tree only projects the same formal Mingli state. It adds no relationships or conclusions.",
    "dream.mirror.open": "Open the chart mirror",
    "dream.mirror.close": "Return to the tree",
    "dream.workspace.back": "Return to Life World",
    "dream.path.none_confirmed": "No confirmed primary path yet",
    "dream.source.authorized_human": "Authorized human · anonymous",
    "dream.source.canonical_npc": "Canonical NPC · artificial life",
    "dream.unavailable.title": "This dream path is not open yet",
    "dream.unavailable.detail": "Abu enters only when three real, authorized, revocable, anonymized scenes are ready together.",
    "dream.error.title": "The mist path is unclear for now",
  },
  ko: {
    "dream.entry": "아부와 꿈으로",
    "dream.resume": "지난 꿈 이어가기",
    "dream.loading": "안개 길이 열리고 있어요",
    "dream.encounter.eyebrow": "아부의 꿈 · 세 그루 인연",
    "dream.encounter.title": "세 생명나무가 조용히 자라고 있어요",
    "dream.encounter.lede": "한 그루는 허가된 익명 실제 사용자, 두 그루는 명확히 표시된 Canonical NPC입니다. 관찰하되 바꾸지 않습니다.",
    "dream.tree.choose": "이 나무에 다가가기",
    "dream.tree.eyebrow": "한 그루 관찰",
    "dream.tree.title": "한 생명이 안개 속에 고유한 형태를 남깁니다",
    "dream.tree.lede": "나무 형상은 동일한 공식 명리 상태만 비추며 관계나 결론을 덧붙이지 않습니다.",
    "dream.mirror.open": "명식 거울 열기",
    "dream.mirror.close": "나무 아래로",
    "dream.workspace.back": "생명 세계로 돌아가기",
    "dream.path.none_confirmed": "현재 확인된 주 경로가 없습니다",
    "dream.source.authorized_human": "허가된 실제 사용자 · 익명",
    "dream.source.canonical_npc": "Canonical NPC · 인공 생명",
    "dream.unavailable.title": "이 꿈길은 아직 열리지 않았어요",
    "dream.unavailable.detail": "실제 자료 세 건이 허가, 철회 가능, 익명화 조건을 모두 충족할 때만 아부가 안내합니다.",
    "dream.error.title": "안개 길이 잠시 흐려졌어요",
  },
} as const;

export type DreamMessageKey = keyof typeof messages.zh;

export function dreamLocale(): DreamLocale {
  const language = navigator.language.toLowerCase();
  if (language.startsWith("ko")) return "ko";
  if (language.startsWith("en")) return "en";
  return "zh";
}

export function dreamText(key: DreamMessageKey, locale = dreamLocale()): string {
  return messages[locale][key] || messages.zh[key];
}
