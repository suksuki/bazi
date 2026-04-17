"use client";

import { useState } from "react";
import { LabEngineConsole } from "@/features/admin-lab/LabEngineConsole";
import { useLabConfig } from "@/features/lab-config/LabConfigContext";
import { useActiveView } from "@/components/layout/ActiveViewContext";

export function EngineRoomPanel() {
  const { setActiveView } = useActiveView();
  const { labConfig, pluginSwitches, setPluginSwitches } = useLabConfig();
  const [labOpen, setLabOpen] = useState(true);

  return (
    <LabEngineConsole
      variant="engineRoom"
      labOpen={labOpen}
      setLabOpen={setLabOpen}
      labConfig={labConfig}
      pluginSwitches={pluginSwitches}
      setPluginSwitches={setPluginSwitches}
      onApplyRecalculate={() => setActiveView("lab")}
    />
  );
}
