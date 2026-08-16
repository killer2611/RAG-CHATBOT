import type { Metadata } from "next";
import { SettingsWorkspace } from "@/components/settings/settings-workspace";

export const metadata: Metadata = {
  title: "Settings & Preferences",
  description:
    "Workspace theme, accessibility, and visual density preferences.",
};

export default function SettingsPage() {
  return <SettingsWorkspace />;
}
