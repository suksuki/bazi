"use client";

import { AdminSettingsView } from "@/features/admin-settings/AdminSettingsView";
import { useAdminSettingsController } from "@/features/admin-settings/useAdminSettingsController";

export default function AdminSettingsPage() {
  const controller = useAdminSettingsController();
  return <AdminSettingsView controller={controller} />;
}
