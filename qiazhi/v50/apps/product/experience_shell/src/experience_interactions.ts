import type { CanvasLayer, CanvasStage } from "./contracts";
import type { ProductArea, WorkspaceSurface } from "./state";


export interface ExperienceInteractionHandlers {
  selectArea(area: ProductArea): void;
  selectSurface(surface: WorkspaceSurface): void;
  selectAnchor(anchor: string, message: string): void;
  toggleSection(section: string): void;
  command(command: string): void;
  playSegment(index: number): void;
  selectCanvasStage(stage: CanvasStage): void;
  selectCanvasLayer(layer: CanvasLayer): void;
  selectCanvasObject(selected: string): void;
  selectCase(caseId: string): void;
}


export function bindExperienceInteractions(
  root: HTMLElement,
  handlers: ExperienceInteractionHandlers,
): void {
  root.querySelectorAll<HTMLButtonElement>("[data-product-area]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectArea(button.dataset.productArea as ProductArea));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-workspace-surface]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectSurface(button.dataset.workspaceSurface as WorkspaceSurface));
  });
  root.querySelectorAll<HTMLElement>("[data-select-anchor]").forEach((element) => {
    element.addEventListener("click", () => handlers.selectAnchor(
      element.dataset.selectAnchor || "baseline-summary",
      element.dataset.message || "这一处来自正式命局认知。",
    ));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-toggle-section]").forEach((button) => {
    button.addEventListener("click", () => handlers.toggleSection(button.dataset.toggleSection || "baseline"));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-command]").forEach((button) => {
    button.addEventListener("click", () => handlers.command(button.dataset.command || ""));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-play-segment]").forEach((button) => {
    button.addEventListener("click", () => handlers.playSegment(Number(button.dataset.playSegment || 0)));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-canvas-stage]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectCanvasStage(
      (button.dataset.canvasStage || "natal") as CanvasStage,
    ));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-canvas-layer]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!button.disabled) handlers.selectCanvasLayer(
        (button.dataset.canvasLayer || "generation_control") as CanvasLayer,
      );
    });
  });
  root.querySelectorAll<Element>("[data-canvas-object]").forEach((element) => {
    const select = () => {
      const selected = element.getAttribute("data-canvas-object") || "";
      if (selected) handlers.selectCanvasObject(selected);
    };
    element.addEventListener("click", select);
    element.addEventListener("keydown", (event) => {
      if (event instanceof KeyboardEvent && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        select();
      }
    });
  });
  root.querySelector<HTMLSelectElement>("[data-case-select]")?.addEventListener("change", (event) => {
    handlers.selectCase((event.currentTarget as HTMLSelectElement).value);
  });
}
