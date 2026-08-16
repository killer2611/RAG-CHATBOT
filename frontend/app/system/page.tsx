import type { Metadata } from "next";
import { SystemWorkspace } from "@/components/system/system-workspace";

export const metadata: Metadata = {
  title: "System Observability & Architecture",
  description:
    "Live health status, runtime configuration hyperparameters, and verified RAG pipeline topology.",
};

export default function SystemPage() {
  return <SystemWorkspace />;
}
