import { SavedSettings } from "./types";

export function makePgUrl(args: {
  host: string;
  port: string;
  database: string;
  user: string;
  password: string;
  sslMode: string;
}) {
  const pwd = encodeURIComponent(args.password);
  const ssl = args.sslMode ? `?sslmode=${args.sslMode}` : "";
  return `postgresql://${args.user}:${pwd}@${args.host}:${args.port}/${args.database}${ssl}`;
}

export function buildSavedSettings(input: SavedSettings): SavedSettings {
  return { ...input };
}
