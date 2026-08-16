import type { Metadata } from "next";
import { LibraryWorkspace } from "@/components/library/library-workspace";

export const metadata: Metadata = {
  title: "Knowledge Library",
  description:
    "Ingest and manage documents into the hierarchical vector index with persistent chunking.",
};

export default function LibraryPage() {
  return <LibraryWorkspace />;
}
