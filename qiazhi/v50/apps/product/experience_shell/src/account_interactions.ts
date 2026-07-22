import type { AuthMode } from "./api";


export interface AccountInteractionHandlers {
  setAuthMode(mode: AuthMode): void;
  submitAuth(form: HTMLFormElement): void;
  command(command: string): void;
  useProfile(profileId: string): void;
  editProfile(profileId: string): void;
  deleteProfile(profileId: string): void;
  submitProfile(form: HTMLFormElement): void;
}


export function bindAccountInteractions(
  root: HTMLElement,
  handlers: AccountInteractionHandlers,
): void {
  root.querySelectorAll<HTMLButtonElement>("[data-auth-mode]").forEach((button) => {
    button.addEventListener("click", () => handlers.setAuthMode((button.dataset.authMode || "login") as AuthMode));
  });
  root.querySelector<HTMLFormElement>("[data-auth-form]")?.addEventListener("submit", (event) => {
    event.preventDefault();
    handlers.submitAuth(event.currentTarget as HTMLFormElement);
  });
  root.querySelectorAll<HTMLButtonElement>("[data-account-command]").forEach((button) => {
    button.addEventListener("click", () => handlers.command(button.dataset.accountCommand || ""));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-profile-use]").forEach((button) => {
    button.addEventListener("click", () => handlers.useProfile(button.dataset.profileUse || ""));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-profile-edit]").forEach((button) => {
    button.addEventListener("click", () => handlers.editProfile(button.dataset.profileEdit || ""));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-profile-delete]").forEach((button) => {
    button.addEventListener("click", () => handlers.deleteProfile(button.dataset.profileDelete || ""));
  });
  root.querySelector<HTMLFormElement>("[data-profile-form]")?.addEventListener("submit", (event) => {
    event.preventDefault();
    handlers.submitProfile(event.currentTarget as HTMLFormElement);
  });
}
