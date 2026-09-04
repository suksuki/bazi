export interface RuntimeAssetDelivery {
  asset_ref: string;
  asset_version: string;
  url: string;
  media_type: string;
  sha256: string;
}

export interface RuntimeMediaCue {
  cue_ref: string;
  version: string;
  trigger: string;
  playback: "LOOP" | "PLAY_ONCE";
  interruptible: boolean;
  deliveries: Record<string, RuntimeAssetDelivery>;
}

export interface PublicRuntimeMediaManifest {
  registry_version: string;
  catalog_version: string;
  assets: {
    brand_logo: RuntimeAssetDelivery;
    login_life_tree_background: RuntimeAssetDelivery;
    home_day_background: RuntimeAssetDelivery;
    home_night_background: RuntimeAssetDelivery;
    home_day_logo: RuntimeAssetDelivery;
    home_night_logo: RuntimeAssetDelivery;
    home_profile_leaf: RuntimeAssetDelivery;
    mingli_growth_day_video: RuntimeAssetDelivery;
    mingli_growth_day_start: RuntimeAssetDelivery;
    mingli_growth_day_poster: RuntimeAssetDelivery;
    mingli_growth_night_video: RuntimeAssetDelivery;
    mingli_growth_night_start: RuntimeAssetDelivery;
    mingli_growth_night_poster: RuntimeAssetDelivery;
    mingli_lab_day_background: RuntimeAssetDelivery;
    mingli_lab_night_background: RuntimeAssetDelivery;
  };
  cues: {
    abu_idle: RuntimeMediaCue;
    dodo_idle: RuntimeMediaCue;
  };
}

export type RuntimeMediaManifest = PublicRuntimeMediaManifest;

export interface PublicProductExposureManifest {
  policy_version: "v60.public-product-exposure.003";
  public_units: readonly ["MINGLI_READING", "ABU_SAYS"];
  lab: {
    status: "INTERNAL_ONLY";
    public_entry_allowed: false;
    public_route_allowed: false;
  };
}

export interface Bootstrap {
  manifest: {
    product_id: string;
    product_version: string;
    foundation_version: string;
    entry_experience: "MINGLI_HOME";
    public_product_exposure: PublicProductExposureManifest;
  };
  media: PublicRuntimeMediaManifest;
  experience: {
    state: "MINGLI_READY";
    entry: "MINGLI_HOME";
    unavailable_reason: string | null;
  };
}

export interface Session {
  account: {
    account_ref: string;
    email: string;
    display_name: string;
    account_role: string;
  };
  profiles: Array<{
    profile_ref: string;
    display_name: string;
  }>;
}
