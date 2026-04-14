import type { FinalVerdictChangeLog } from "../models";
import type { DeityComponent, DeityEnergyAxis } from "../models";

/** 与 useStreamBoardController 中 labState.snapshot 切片对齐 */
export type StreamBoardHydrationSnapshot = {
  physics_tensor?: {
    deity_scores?: Record<string, number>;
    deity_energy_axes?: Record<string, DeityEnergyAxis>;
    deity_components?: Record<string, DeityComponent>;
    deity_trace_details?: Record<string, Record<string, unknown>>;
  };
  final_verdict?: {
    body?: string;
    change_log?: FinalVerdictChangeLog;
    logical_evidence?: string[];
    work_vector?: Record<string, unknown>;
    topology_graph_v1?: Record<string, unknown>;
    structure_candidates_v0?: Record<string, unknown>;
    structure_final_decision_v0?: Record<string, unknown>;
    version_id?: string;
    brain_hub?: Record<string, unknown>;
    assertion_tree?: Record<string, unknown>;
    narrative_strategy?: string;
  };
  decision_selection_ids?: string[];
} | null;
