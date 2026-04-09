"use client";

import React, { createContext, useContext, useMemo, useState } from "react";
import type { PhysicsLabConfig } from "@/features/stream-board/models";
import type { PluginSwitches, PluginWeights } from "@/features/stream-board/models";

const DEFAULT_LAB: PhysicsLabConfig = {
  WEIGHT_LUCK: 0.4,
  WEIGHT_YEAR: 0.2,
  BASE_BACKFIRE_RISK: 0.2,
  HIGH_IMBALANCE_RISK: 0.35,
  TOMB_LOCK_RATE: 0.9,
  CLIMATE_INTENSITY: 1.0,
  STEM_RESONANCE_BOOST: 1.5,
  TRANSFER_DISTANCE_DECAY: 0.1,
  WORK_MIN_THRESHOLD: 0.5,
  SHOW_WEAK_WORK_PATHS: 1,
};

const DEFAULT_SWITCHES: PluginSwitches = {
  blindSchool: true,
  wangshuai: true,
  wealthRisk: false,
};

const DEFAULT_WEIGHTS: PluginWeights = {
  blindSchool: 0.8,
  wangshuai: 0.6,
};

type LabConfigValue = {
  labConfig: PhysicsLabConfig;
  setLabConfig: React.Dispatch<React.SetStateAction<PhysicsLabConfig>>;
  pluginSwitches: PluginSwitches;
  setPluginSwitches: React.Dispatch<React.SetStateAction<PluginSwitches>>;
  pluginWeights: PluginWeights;
  setPluginWeights: React.Dispatch<React.SetStateAction<PluginWeights>>;
  togglePlugin: (key: keyof PluginSwitches) => void;
  applyPreset: (preset: "blind_practical" | "health_audit") => void;
};

const LabConfigContext = createContext<LabConfigValue | null>(null);

export function LabConfigProvider({ children }: { children: React.ReactNode }) {
  const [labConfig, setLabConfig] = useState<PhysicsLabConfig>(DEFAULT_LAB);
  const [pluginSwitches, setPluginSwitches] = useState<PluginSwitches>(DEFAULT_SWITCHES);
  const [pluginWeights, setPluginWeights] = useState<PluginWeights>(DEFAULT_WEIGHTS);

  function togglePlugin(key: keyof PluginSwitches) {
    setPluginSwitches((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function applyPreset(preset: "blind_practical" | "health_audit") {
    if (preset === "blind_practical") {
      setPluginSwitches({ blindSchool: true, wangshuai: true, wealthRisk: false });
      setPluginWeights({ blindSchool: 0.9, wangshuai: 0.1 });
      return;
    }
    setPluginSwitches({ blindSchool: true, wangshuai: true, wealthRisk: true });
    setPluginWeights({ blindSchool: 0.2, wangshuai: 0.8 });
  }

  const value = useMemo(
    () => ({
      labConfig,
      setLabConfig,
      pluginSwitches,
      setPluginSwitches,
      pluginWeights,
      setPluginWeights,
      togglePlugin,
      applyPreset,
    }),
    [labConfig, pluginSwitches, pluginWeights],
  );

  return <LabConfigContext.Provider value={value}>{children}</LabConfigContext.Provider>;
}

export function useLabConfig(): LabConfigValue {
  const ctx = useContext(LabConfigContext);
  if (!ctx) {
    throw new Error("useLabConfig must be used within LabConfigProvider");
  }
  return ctx;
}
