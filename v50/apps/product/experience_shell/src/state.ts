import type {
  CaseWorkspaceState,
  CanvasLayer,
  CanvasStage,
  CanvasVisibilityLayer,
  MingliExperienceEnvelope,
  NarrationManifest,
  NarrationStatus,
} from "./contracts";

export type WorkspaceSurface = CaseWorkspaceState["current_surface"];
export type ProductArea = "world" | "workbench" | "lab";

export interface ServerState {
  envelope: MingliExperienceEnvelope | null;
  narrationManifest: NarrationManifest | null;
  narrationAssets: Record<string, NarrationStatus>;
}

export interface UiState {
  productArea: ProductArea;
  workspaceSurface: WorkspaceSurface;
  selectedAnchor: string;
  expandedSections: Record<string, boolean>;
  abuExpanded: boolean;
  narrationStatus: "idle" | "preparing" | "playing" | "paused" | "complete" | "error";
  narrationIndex: number;
  abuMessage: string;
  canvasStage: CanvasStage;
  canvasLayer: CanvasLayer;
  canvasVisibilityLayer: CanvasVisibilityLayer;
  selectedCanvasObject: string;
  canvasContextStatus: "idle" | "loading" | "ready" | "error";
}

export const initialUiState: UiState = {
  productArea: "world",
  workspaceSurface: "overview",
  selectedAnchor: "baseline-summary",
  expandedSections: {
    baseline: true,
    pillars: true,
    canvas: true,
    path: true,
    boundaries: true,
  },
  abuExpanded: false,
  narrationStatus: "idle",
  narrationIndex: -1,
  abuMessage: "我先陪你看整盘重心。想听的时候，点我就好。",
  canvasStage: "natal",
  canvasLayer: "overview",
  canvasVisibilityLayer: "formal",
  selectedCanvasObject: "",
  canvasContextStatus: "idle",
};

export type UiAction =
  | { type: "product-area"; area: ProductArea }
  | { type: "workspace-surface"; surface: WorkspaceSurface }
  | { type: "select"; anchor: string; message: string }
  | { type: "toggle-section"; section: string }
  | { type: "toggle-abu"; expanded?: boolean }
  | { type: "narration"; status: UiState["narrationStatus"]; index?: number; message?: string }
  | { type: "canvas-stage"; stage: CanvasStage; layer: CanvasLayer; selected: string }
  | { type: "canvas-layer"; layer: CanvasLayer }
  | { type: "canvas-visibility"; visibility: CanvasVisibilityLayer }
  | { type: "canvas-select"; selected: string; status: UiState["canvasContextStatus"] }
  | { type: "canvas-context-status"; status: UiState["canvasContextStatus"] };

export function reduceUi(state: UiState, action: UiAction): UiState {
  switch (action.type) {
    case "product-area":
      return { ...state, productArea: action.area };
    case "workspace-surface":
      return { ...state, workspaceSurface: action.surface };
    case "select":
      return { ...state, selectedAnchor: action.anchor, abuMessage: action.message };
    case "toggle-section":
      return {
        ...state,
        expandedSections: {
          ...state.expandedSections,
          [action.section]: !state.expandedSections[action.section],
        },
      };
    case "toggle-abu":
      return { ...state, abuExpanded: action.expanded ?? !state.abuExpanded };
    case "narration":
      return {
        ...state,
        narrationStatus: action.status,
        narrationIndex: action.index ?? state.narrationIndex,
        abuMessage: action.message ?? state.abuMessage,
      };
    case "canvas-stage":
      return {
        ...state,
        canvasStage: action.stage,
        canvasLayer: action.layer,
        selectedCanvasObject: action.selected,
        canvasContextStatus: "ready",
      };
    case "canvas-layer":
      return { ...state, canvasLayer: action.layer };
    case "canvas-visibility":
      return { ...state, canvasVisibilityLayer: action.visibility };
    case "canvas-select":
      return {
        ...state,
        selectedCanvasObject: action.selected,
        canvasContextStatus: action.status,
      };
    case "canvas-context-status":
      return { ...state, canvasContextStatus: action.status };
  }
}
