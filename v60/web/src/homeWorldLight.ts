export type HomeWorldLight = "day" | "night";

const STORAGE_KEY = "abuknows-world-light-mode-v1";
const DAY_START_MINUTES = 6 * 60 + 30;
const NIGHT_START_MINUTES = 18 * 60 + 30;

export function resolveHomeWorldLight(date = new Date()): HomeWorldLight {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "day" || stored === "night") return stored;
  } catch {
    // World light is presentation state and may safely fall back to local time.
  }
  const minutes = date.getHours() * 60 + date.getMinutes();
  return minutes >= DAY_START_MINUTES && minutes < NIGHT_START_MINUTES
    ? "day"
    : "night";
}

export function rememberHomeWorldLight(light: HomeWorldLight) {
  try {
    window.localStorage.setItem(STORAGE_KEY, light);
  } catch {
    // Presentation memory never owns Case, Reading, or Dream state.
  }
}
