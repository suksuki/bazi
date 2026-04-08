"use client";

import { StreamBoardView } from "@/features/stream-board/StreamBoardView";
import { useStreamBoardController } from "@/features/stream-board/useStreamBoardController";

export function StreamBoard() {
  const viewModel = useStreamBoardController();
  return <StreamBoardView {...viewModel} />;
}
