import type { Metadata } from "next";
import { EvaluationWorkspace } from "@/components/evaluation/evaluation-workspace";

export const metadata: Metadata = {
  title: "Evaluation Lab & Benchmarks",
  description:
    "Launch and monitor DeepEval benchmarks to measure retrieval and generation quality with statistical rigor.",
};

export default function EvaluatePage() {
  return <EvaluationWorkspace />;
}
