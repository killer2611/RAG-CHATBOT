import type { Metadata } from "next";
import { HomeWorkspace } from "@/components/home/home-workspace";

export const metadata: Metadata = {
  title: "Evidence-Grounded RAG Platform",
  description:
    "Production-grade conversational knowledge platform with hierarchical retrieval, strict grounding, and DeepEval benchmarks.",
};

export default function HomePage() {
  return <HomeWorkspace />;
}
