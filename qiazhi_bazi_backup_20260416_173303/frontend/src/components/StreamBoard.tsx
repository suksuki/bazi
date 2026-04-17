"use client";

import { StreamBoardView, useStreamBoardController } from "@/features/stream-board";

export function StreamBoard() {
  const viewModel = useStreamBoardController();
  return <StreamBoardView {...viewModel} />;
}
