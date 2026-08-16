import { describe, it } from "node:test";
import assert from "node:assert";

describe("Knowledge Library & Ingestion Logic", () => {
  const SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".docx"];
  const MAX_FILE_SIZE_MB = 50;

  const validateFile = (fileName, sizeInBytes) => {
    const name = fileName.toLowerCase();
    const isSupported = SUPPORTED_EXTENSIONS.some((ext) => name.endsWith(ext));
    if (!isSupported) {
      return { valid: false, error: "Unsupported file format" };
    }
    if (sizeInBytes > MAX_FILE_SIZE_MB * 1024 * 1024) {
      return { valid: false, error: "File exceeds size limit" };
    }
    return { valid: true };
  };

  it("accepts valid PDF, TXT, and DOCX files within size limits", () => {
    assert.strictEqual(validateFile("report.pdf", 5 * 1024 * 1024).valid, true);
    assert.strictEqual(validateFile("notes.txt", 100 * 1024).valid, true);
    assert.strictEqual(validateFile("contract.DOCX", 10 * 1024 * 1024).valid, true);
  });

  it("rejects unsupported file formats strictly", () => {
    assert.strictEqual(validateFile("spreadsheet.csv", 1000).valid, false);
    assert.strictEqual(validateFile("binary.exe", 1000).valid, false);
    assert.strictEqual(validateFile("image.png", 1000).valid, false);
    assert.strictEqual(validateFile("script.py", 1000).valid, false);
  });

  it("rejects oversized documents exceeding 50MB", () => {
    const oversizedBytes = 55 * 1024 * 1024;
    const res = validateFile("large_archive.pdf", oversizedBytes);
    assert.strictEqual(res.valid, false);
    assert.strictEqual(res.error, "File exceeds size limit");
  });

  it("accurately filters document collections by format and search keywords", () => {
    const sampleDocs = [
      {
        source_id: "digest_111",
        source_name: "machine_learning_survey.pdf",
        parents: 18,
        children: 72,
        status: "indexed",
      },
      {
        source_id: "digest_222",
        source_name: "notes_on_rag.txt",
        parents: 4,
        children: 16,
        status: "indexed",
      },
      {
        source_id: "digest_333",
        source_name: "architecture_specification.docx",
        parents: 25,
        children: 100,
        status: "indexed",
      },
    ];

    const filterDocs = (docs, format, query) => {
      return docs.filter((doc) => {
        if (format !== "all") {
          const ext = doc.source_name.split(".").pop()?.toLowerCase();
          if (ext !== format.toLowerCase()) return false;
        }
        if (query.trim()) {
          const q = query.toLowerCase();
          const matchesName = doc.source_name.toLowerCase().includes(q);
          const matchesId = doc.source_id.toLowerCase().includes(q);
          if (!matchesName && !matchesId) return false;
        }
        return true;
      });
    };

    // Filter by PDF format
    const pdfs = filterDocs(sampleDocs, "pdf", "");
    assert.strictEqual(pdfs.length, 1);
    assert.strictEqual(pdfs[0].source_name, "machine_learning_survey.pdf");

    // Filter by search query
    const searchRes = filterDocs(sampleDocs, "all", "rag");
    assert.strictEqual(searchRes.length, 1);
    assert.strictEqual(searchRes[0].source_name, "notes_on_rag.txt");

    // Filter by source digest
    const digestRes = filterDocs(sampleDocs, "all", "digest_333");
    assert.strictEqual(digestRes.length, 1);
    assert.strictEqual(digestRes[0].source_name, "architecture_specification.docx");
  });
});
