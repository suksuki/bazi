import { Application, Assets, Sprite } from "pixi.js";
import { useEffect, useRef } from "react";

import type { RuntimeAssetDelivery } from "./api";

export function DreamStage({ asset }: { asset: RuntimeAssetDelivery }) {
  const hostRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const application = new Application();
    let disposed = false;
    let background: Sprite | null = null;

    const layout = () => {
      if (!background) return;
      const width = application.renderer.width;
      const height = application.renderer.height;
      const textureWidth = background.texture.width;
      const textureHeight = background.texture.height;
      const scale = Math.max(width / textureWidth, height / textureHeight);
      background.scale.set(scale);
      background.position.set(
        Math.round((width - textureWidth * scale) / 2),
        Math.round((height - textureHeight * scale) / 2),
      );
    };

    void (async () => {
      await application.init({
        resizeTo: host,
        antialias: true,
        backgroundAlpha: 0,
        preference: "webgl",
      });
      if (disposed) {
        application.destroy(true);
        return;
      }

      host.appendChild(application.canvas);
      const texture = await Assets.load(asset.url);
      if (disposed) return;
      background = new Sprite(texture);
      application.stage.addChild(background);
      layout();
    })();

    const observer = new ResizeObserver(layout);
    observer.observe(host);

    return () => {
      disposed = true;
      observer.disconnect();
      application.destroy(true, { children: true });
    };
  }, [asset.url]);

  return (
    <div
      className="dream-canvas"
      data-asset-ref={asset.asset_ref}
      ref={hostRef}
      aria-hidden="true"
    />
  );
}
