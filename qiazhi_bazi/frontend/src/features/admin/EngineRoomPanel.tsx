"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { LabEngineConsole } from "@/features/admin-lab/LabEngineConsole";
import { useLabConfig } from "@/features/lab-config/LabConfigContext";

export function EngineRoomPanel() {
  const router = useRouter();
  const { labConfig, setLabConfig, pluginSwitches, setPluginSwitches } = useLabConfig();
  const [labOpen, setLabOpen] = useState(true);
  const [labGroupsOpen, setLabGroupsOpen] = useState({
    timing: true,
    riskTomb: true,
    climateTopology: true,
  });

  return (
    <LabEngineConsole
      variant="engineRoom"
      labOpen={labOpen}
      setLabOpen={setLabOpen}
      labGroupsOpen={labGroupsOpen}
      setLabGroupsOpen={setLabGroupsOpen}
      labConfig={labConfig}
      setLabConfig={setLabConfig}
      pluginSwitches={pluginSwitches}
      setPluginSwitches={setPluginSwitches}
      onApplyRecalculate={() => router.push("/")}
    />
  );
}
