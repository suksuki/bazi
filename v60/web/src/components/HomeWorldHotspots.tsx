import type { PublicLifeTreeHomeSnapshot } from "../publicHomeApi";
import type { PublicRuntimeMediaManifest } from "../publicRuntimeTypes";

export function HomeWorldHotspots({
  busy,
  busyCaseRef,
  home,
  media,
  onOpenMingli,
  onOpenSettings,
}: {
  busy: boolean;
  busyCaseRef: string | null;
  home: PublicLifeTreeHomeSnapshot;
  media: PublicRuntimeMediaManifest;
  onOpenMingli: (option: PublicLifeTreeHomeSnapshot["case_options"][number], anchor: HTMLElement) => void;
  onOpenSettings: () => void;
}) {
  const cases = [
    ...home.case_options.filter((option) => option.active),
    ...home.case_options.filter((option) => !option.active),
  ];

  return (
    <nav className="v108-tree-nav" aria-label="生命树空间入口">
      {cases.slice(0, 3).map((option, index) => (
        <button
          aria-current={option.active ? "page" : undefined}
          aria-label={`${option.display_name}的命理测算`}
          className={`v108-tree-entry v108-profile-leaf v108-profile-leaf-${index}`}
          data-active={option.active}
          data-case-ref={option.case_ref}
          disabled={busy || busyCaseRef !== null}
          key={option.case_ref}
          onClick={(event) => onOpenMingli(option, event.currentTarget)}
          type="button"
        >
          <img data-asset-ref={media.assets.home_profile_leaf.asset_ref} src={media.assets.home_profile_leaf.url} alt="" />
          <span>
            <small>命理测算</small>
            <strong>{option.display_name}</strong>
          </span>
        </button>
      ))}
      {cases.length > 3 && (
        <button className="v108-profile-more" onClick={onOpenSettings} type="button">
          +{cases.length - 3}
        </button>
      )}

      <button
        aria-label="打开八字档案"
        className="v108-settings-fruit"
        onClick={onOpenSettings}
        type="button"
      >
        <i aria-hidden="true" />
        <span><small>生命叶</small><strong>八字档案</strong></span>
      </button>
    </nav>
  );
}
