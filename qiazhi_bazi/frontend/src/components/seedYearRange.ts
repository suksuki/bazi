/** 与 SeedInput 生日年下拉一致：1950–2030（含） */
export const SEED_YEAR_MIN = 1950;
export const SEED_YEAR_MAX = 2030;

export const SEED_YEAR_STRINGS = Array.from(
  { length: SEED_YEAR_MAX - SEED_YEAR_MIN + 1 },
  (_, i) => String(SEED_YEAR_MIN + i),
);
