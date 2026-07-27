import type { CanvasLayer, CanvasStage, CanvasVisibilityLayer } from "./contracts";
import type { LifeTreeQuestionCategory } from "./relation_work_api";
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
  selectCanvasVisibility(visibility: CanvasVisibilityLayer): void;
  selectCanvasObject(selected: string): void;
  selectProfile(profileId: string): void;
  selectLifeTreeQuestion(questionId: string, category: LifeTreeQuestionCategory): void;
  selectLifeTreeOption(optionId: string): void;
  submitLifeTreeAnswer(): void;
  selectRelationLabMode(mode: "facts" | "candidates" | "professional"): void;
  selectRelationPath(pathRef: string): void;
  selectRelationFact(factRef: string): void;
  restoreRelationNatal(): void;
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
        (button.dataset.canvasLayer || "overview") as CanvasLayer,
      );
    });
  });
  root.querySelectorAll<HTMLButtonElement>("[data-canvas-visibility]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!button.disabled) handlers.selectCanvasVisibility(
        (button.dataset.canvasVisibility || "formal") as CanvasVisibilityLayer,
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
  root.querySelectorAll<HTMLSelectElement>("[data-profile-select]").forEach((select) => {
    select.addEventListener("change", (event) => {
      handlers.selectProfile((event.currentTarget as HTMLSelectElement).value);
    });
  });
  root.querySelectorAll<HTMLButtonElement>("[data-life-tree-question]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectLifeTreeQuestion(
      button.dataset.lifeTreeQuestion || "",
      (button.dataset.lifeTreeCategory || "factual_observation") as LifeTreeQuestionCategory,
    ));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-life-tree-option]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectLifeTreeOption(
      button.dataset.lifeTreeOption || "",
    ));
  });
  root.querySelector<HTMLButtonElement>("[data-life-tree-submit]")?.addEventListener(
    "click",
    () => handlers.submitLifeTreeAnswer(),
  );
  root.querySelectorAll<HTMLButtonElement>("[data-relation-lab-mode]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectRelationLabMode(
      (button.dataset.relationLabMode || "facts") as "facts" | "candidates" | "professional",
    ));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-relation-path]").forEach((button) => {
    button.addEventListener("click", () => handlers.selectRelationPath(
      button.dataset.relationPath || "",
    ));
  });
  root.querySelectorAll<HTMLElement>("[data-relation-fact]").forEach((element) => {
    const select = () => handlers.selectRelationFact(
      element.dataset.relationFact || "",
    );
    element.addEventListener("click", select);
    element.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        select();
      }
    });
  });
  root.querySelector<HTMLButtonElement>("[data-relation-restore-natal]")?.addEventListener(
    "click",
    () => handlers.restoreRelationNatal(),
  );
}
