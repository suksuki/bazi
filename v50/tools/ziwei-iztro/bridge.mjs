import { astro } from "iztro";

let rawInput = "";
for await (const chunk of process.stdin) rawInput += chunk;
const input = JSON.parse(rawInput);
const language = input.language || "zh-CN";
const gender = input.gender === "female" ? "女" : "男";
const timeIndex = Number(input.time_index);
if (!Number.isInteger(timeIndex) || timeIndex < 0 || timeIndex > 12) {
  throw new Error("invalid_time_index");
}

const plate = input.calendar_type === "lunar"
  ? astro.byLunar(input.birth_date, timeIndex, gender, Boolean(input.is_leap_month), true, language)
  : astro.bySolar(input.birth_date, timeIndex, gender, true, language);
const horoscope = input.analysis_date ? plate.horoscope(input.analysis_date, timeIndex) : null;

const palaces = plate.palaces.map((palace) => ({
  name: palace.name,
  heavenly_stem: palace.heavenlyStem,
  earthly_branch: palace.earthlyBranch,
  is_body_palace: Boolean(palace.isBodyPalace),
  is_original_palace: Boolean(palace.isOriginalPalace),
  major_stars: (palace.majorStars || []).map(normalizeStar),
  minor_stars: (palace.minorStars || []).map(normalizeStar),
  adjective_stars: (palace.adjectiveStars || []).map(normalizeStar),
  changsheng_12: palace.changsheng12 || "",
  decadal: palace.decadal || null,
  ages: palace.ages || [],
}));

const output = {
  source: "iztro@2.5.8",
  solar_date: plate.solarDate,
  lunar_date: plate.lunarDate,
  chinese_date: plate.chineseDate,
  time: plate.time,
  time_range: plate.timeRange,
  zodiac: plate.zodiac,
  soul_palace_branch: plate.earthlyBranchOfSoulPalace,
  body_palace_branch: plate.earthlyBranchOfBodyPalace,
  soul_star: plate.soul,
  body_star: plate.body,
  five_elements_class: plate.fiveElementsClass,
  palaces,
  horoscope: horoscope ? normalizeHoroscope(horoscope) : null,
};

process.stdout.write(JSON.stringify(output));

function normalizeStar(star) {
  return {
    name: star.name,
    type: star.type || "",
    scope: star.scope || "",
    brightness: star.brightness || "",
    mutagen: star.mutagen || "",
  };
}

function normalizeHoroscope(value) {
  return {
    solar_date: value.solarDate,
    lunar_date: value.lunarDate,
    decadal: value.decadal || null,
    age: value.age || null,
    yearly: value.yearly || null,
    monthly: value.monthly || null,
    daily: value.daily || null,
    hourly: value.hourly || null,
  };
}
