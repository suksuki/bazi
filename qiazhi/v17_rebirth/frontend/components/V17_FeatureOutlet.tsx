"use client";

import type { ReactNode } from "react";

export type V17FeatureRenderer = () => ReactNode;
export type V17FeatureRenderers<TId extends string> = Partial<Record<TId, V17FeatureRenderer>>;

type Props<TId extends string> = {
  activeId: TId;
  renderers: V17FeatureRenderers<TId>;
  fallback?: ReactNode;
};

export function V17_FeatureOutlet<TId extends string>({
  activeId,
  renderers,
  fallback = null,
}: Props<TId>) {
  return <>{renderers[activeId]?.() ?? fallback}</>;
}
