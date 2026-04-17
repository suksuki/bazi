import { describe, expect, it } from "vitest";
import {
  aggregateManualEnergyDeltas,
  appendSemanticVerdictDeduped,
  applyManualEnergyPatchesToDisplay,
  buildEnergyDeltasFromLogicProposal,
  mergeAnalyzeSeedMetadata,
  mergeIncomingMetadataPersistence,
} from "./individualAdjustment";
import type { BaziMetadata } from "@/types/bazi";
import { seedPayloadSignature } from "@/features/stream-board/controller/streamBoardPure";
import type { SeedPayload } from "@/features/stream-board/models";

describe("individualAdjustment", () => {
  it("mergeIncomingMetadataPersistence keeps patch when seed matches", () => {
    const incoming: BaziMetadata = {
      version: "1",
      pillars: null,
      conflict_matrix: { points: [] },
      flow_state: "x",
      notes: "",
    };
    const previous: BaziMetadata = {
      ...incoming,
      manual_energy_patch: {
        seed_hash: "sig-a",
        entries: [{ delta_by_deity: { 比肩: 1 }, confirmed_at: "t0" }],
      },
      persistence_layer: {
        semantic_verdicts: [{ id: "1", text: "x", seed_hash: "sig-a", confirmed_at: "t0" }],
      },
    };
    const merged = mergeIncomingMetadataPersistence(incoming, previous, "sig-a");
    expect(merged.manual_energy_patch?.entries).toHaveLength(1);
    expect(merged.persistence_layer?.semantic_verdicts).toHaveLength(1);
  });

  it("mergeAnalyzeSeedMetadata keeps verdict_anchor_layer when same seed and incoming empty", () => {
    const base: BaziMetadata = {
      version: "1",
      pillars: null,
      conflict_matrix: { points: [] },
      flow_state: "x",
      notes: "",
    };
    const previous: BaziMetadata = {
      ...base,
      verdict_anchor_layer: {
        narrative_version_id: "v1",
        assertions: [{ text: "流式判词锚点保留" }],
      },
    };
    const incoming: BaziMetadata = { ...base, flow_state: "ready" };
    const merged = mergeAnalyzeSeedMetadata(incoming, previous, "sig-s", { sameSeedResubmit: true });
    expect(merged.verdict_anchor_layer?.assertions?.[0]?.text).toBe("流式判词锚点保留");
  });

  it("mergeAnalyzeSeedMetadata keeps semantic_verdicts when same seed and incoming empty list", () => {
    const base: BaziMetadata = {
      version: "1",
      pillars: null,
      conflict_matrix: { points: [] },
      flow_state: "x",
      notes: "",
    };
    const previous: BaziMetadata = {
      ...base,
      persistence_layer: {
        persistence_protocol: "persistence_layer.v1",
        semantic_verdicts: [{ id: "a", text: "已归档", seed_hash: "s", confirmed_at: "t" }],
      },
    };
    const incoming: BaziMetadata = {
      ...base,
      persistence_layer: { persistence_protocol: "persistence_layer.v1", semantic_verdicts: [] },
    };
    const merged = mergeAnalyzeSeedMetadata(incoming, previous, "s", { sameSeedResubmit: true });
    expect(merged.persistence_layer?.semantic_verdicts).toHaveLength(1);
  });

  it("mergeIncomingMetadataPersistence drops patch when seed changes", () => {
    const incoming: BaziMetadata = {
      version: "1",
      pillars: null,
      conflict_matrix: { points: [] },
      flow_state: "x",
      notes: "",
    };
    const previous: BaziMetadata = {
      ...incoming,
      manual_energy_patch: { seed_hash: "old", entries: [{ delta_by_deity: { 比肩: 9 }, confirmed_at: "t" }] },
    };
    const merged = mergeIncomingMetadataPersistence(incoming, previous, "new-seed");
    expect(merged.manual_energy_patch).toBeUndefined();
  });

  it("applyManualEnergyPatchesToDisplay sums entries", () => {
    const scores = { 比肩: 10, 劫财: 5 } as Record<string, number>;
    const axes = { 比肩: { relative_percentage: 10 } };
    const patch = {
      seed_hash: "s1",
      entries: [
        { delta_by_deity: { 比肩: 2 } as Record<string, number>, confirmed_at: "a" },
        { delta_by_deity: { 比肩: 1, 劫财: -1 }, confirmed_at: "b" },
      ],
    };
    const out = applyManualEnergyPatchesToDisplay(scores, axes, patch, "s1");
    expect(out.scores["比肩"]).toBe(13);
    expect(out.scores["劫财"]).toBe(4);
  });

  it("buildEnergyDeltasFromLogicProposal returns shaped deltas", () => {
    const d = buildEnergyDeltasFromLogicProposal("CF_FLOATING_DECAY", 1.1);
    expect(typeof d["比肩"]).toBe("number");
    expect(d["比肩"]!).toBeLessThan(0);
  });

  it("appendSemanticVerdictDeduped dedupes across compatible seed signatures", () => {
    const seedA: SeedPayload = {
      date: "1990-01-01",
      time: "12:00",
      calendar: "solar",
      gender: "male",
    };
    const sig1 = seedPayloadSignature(seedA)!;
    const sig2 = JSON.stringify({
      gender: "male",
      calendar: "solar",
      date: "1990-01-01",
      time: "12:00",
    });
    expect(sig1).not.toBe(sig2);
    const base: BaziMetadata = {
      version: "1",
      pillars: null,
      conflict_matrix: { points: [] },
      flow_state: "x",
      notes: "",
    };
    const once = appendSemanticVerdictDeduped(base, sig1, "食伤过旺", "c1", "2026-01-01T00:00:00.000Z");
    const twice = appendSemanticVerdictDeduped(once, sig2, "食伤过旺", "c2", "2026-01-02T00:00:00.000Z");
    expect(once?.persistence_layer?.semantic_verdicts).toHaveLength(1);
    expect(twice?.persistence_layer?.semantic_verdicts).toHaveLength(1);
  });

  it("appendSemanticVerdictDeduped skips duplicate text for same seed", () => {
    const base: BaziMetadata = {
      version: "1",
      pillars: null,
      conflict_matrix: { points: [] },
      flow_state: "x",
      notes: "",
    };
    const once = appendSemanticVerdictDeduped(base, "s1", "食伤过旺，思虑过度", "c1", "2026-01-01T00:00:00.000Z");
    const twice = appendSemanticVerdictDeduped(once, "s1", "食伤过旺，思虑过度", "c2", "2026-01-02T00:00:00.000Z");
    expect(once?.persistence_layer?.semantic_verdicts).toHaveLength(1);
    expect(twice?.persistence_layer?.semantic_verdicts).toHaveLength(1);
  });

  it("aggregateManualEnergyDeltas merges keys", () => {
    const acc = aggregateManualEnergyDeltas([
      { delta_by_deity: { 食神: 0.5 }, confirmed_at: "1" },
      { delta_by_deity: { 食神: 0.25, 伤官: 0.1 }, confirmed_at: "2" },
    ]);
    expect(acc["食神"]).toBeCloseTo(0.75);
    expect(acc["伤官"]).toBeCloseTo(0.1);
  });
});
