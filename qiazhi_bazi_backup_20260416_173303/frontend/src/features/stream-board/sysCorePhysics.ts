/** 物理引擎唯一对外出口：`plugin_outputs["sys.core.physics"]`（registry 将 runner 返回值包在 `payload` 内）。 */
export function sysCorePhysicsPayload(
  pluginOutputs: Record<string, unknown> | undefined,
): Record<string, unknown> | undefined {
  const row = pluginOutputs?.["sys.core.physics"];
  if (!row || typeof row !== "object") return undefined;
  const pl = (row as Record<string, unknown>).payload;
  return pl && typeof pl === "object" ? (pl as Record<string, unknown>) : undefined;
}
