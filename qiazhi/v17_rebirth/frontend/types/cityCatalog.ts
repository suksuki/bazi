import rawCatalog from "@/data/cityCatalog.json";

export type CityCatalogItem = {
  name: string;
  display_name: string;
  code: string;
  region: string;
  country: string;
  longitude: number | null;
};

export type CityCatalogGroup = {
  id: string;
  label: string;
  kind: "domestic" | "international";
  items: CityCatalogItem[];
};

type CityCatalogPayload = {
  version: string;
  group_count: number;
  city_count: number;
  groups: CityCatalogGroup[];
};

const catalog = rawCatalog as CityCatalogPayload;
const groups = Array.isArray(catalog.groups) ? catalog.groups : [];

const aliasMap = new Map<string, { item: CityCatalogItem; group: CityCatalogGroup }>();

function registerAlias(raw: string, item: CityCatalogItem, group: CityCatalogGroup) {
  const key = String(raw || "").trim().toLowerCase();
  if (!key || aliasMap.has(key)) return;
  aliasMap.set(key, { item, group });
}

for (const group of groups) {
  for (const item of group.items) {
    registerAlias(item.name, item, group);
    registerAlias(item.display_name, item, group);
    if (item.name.endsWith("市")) {
      registerAlias(item.name.slice(0, -1), item, group);
    }
  }
}

const manualAliases: Record<string, string> = {
  Beijing: "北京市",
  Shanghai: "上海市",
  "Hong Kong": "香港",
  Macau: "澳门",
  Taipei: "台北市",
  Tokyo: "东京",
  Seoul: "首尔",
  Singapore: "新加坡",
};

for (const [alias, canonical] of Object.entries(manualAliases)) {
  const hit = aliasMap.get(canonical.toLowerCase());
  if (!hit) continue;
  registerAlias(alias, hit.item, hit.group);
}

export function getCityCatalogGroups(): CityCatalogGroup[] {
  return groups;
}

export function findCityOption(rawName: string | undefined | null): {
  item: CityCatalogItem;
  group: CityCatalogGroup;
} | null {
  const key = String(rawName || "").trim().toLowerCase();
  if (!key) return null;
  return aliasMap.get(key) || null;
}

export function findCityGroup(groupId: string | undefined | null): CityCatalogGroup | null {
  const key = String(groupId || "").trim();
  if (!key) return null;
  return groups.find((group) => group.id === key) || null;
}

export function getCityCatalogStats() {
  return {
    version: catalog.version,
    groupCount: Number(catalog.group_count || groups.length || 0),
    cityCount: Number(catalog.city_count || 0),
  };
}
