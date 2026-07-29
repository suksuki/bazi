import type {
  Bootstrap,
  DreamEntry,
  DreamGrove,
  DreamSnapshot,
  Session,
} from "./api";
import type { HomeSnapshot } from "./homeApi";

export interface RuntimeState {
  bootstrap: Bootstrap | null;
  session: Session | null;
  home: HomeSnapshot | null;
  grove: DreamGrove | null;
  snapshot: DreamSnapshot | null;
  loading: boolean;
  busy: boolean;
  error: string | null;
}

export const initialRuntimeState: RuntimeState = {
  bootstrap: null,
  session: null,
  home: null,
  grove: null,
  snapshot: null,
  loading: true,
  busy: false,
  error: null,
};

export function dreamEntryState(entry: DreamEntry) {
  return entry.kind === "GROVE"
    ? { grove: entry.grove, snapshot: null }
    : { grove: null, snapshot: entry.snapshot };
}

export function loggedOutState(current: RuntimeState): RuntimeState {
  return {
    ...current,
    session: null,
    home: null,
    grove: null,
    snapshot: null,
  };
}
