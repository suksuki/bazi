"use client";

import { useState } from "react";

import type { AuditItem } from "@/components/AuditSidebar";
import type { LlmDiagnosticData } from "../models";

/** 流式判词、侧栏审计、诊断数据 */
export function useStreamBoardAuditUiState() {
  const [streamingText, setStreamingText] = useState("");
  const [auditItems, setAuditItems] = useState<AuditItem[]>([]);
  const [resultLogs, setResultLogs] = useState<string[]>([]);
  const [showPhysicsAudit, setShowPhysicsAudit] = useState(false);
  const [llmDiagnosticData, setLlmDiagnosticData] = useState<LlmDiagnosticData | null>(null);

  return {
    streamingText,
    setStreamingText,
    auditItems,
    setAuditItems,
    resultLogs,
    setResultLogs,
    showPhysicsAudit,
    setShowPhysicsAudit,
    llmDiagnosticData,
    setLlmDiagnosticData,
  };
}
