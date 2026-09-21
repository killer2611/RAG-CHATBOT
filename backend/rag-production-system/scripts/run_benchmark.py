import argparse
import asyncio
import hashlib
import json
import logging
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.rag.loaders import load_file
from app.evaluation.generator_v3 import CandidateGenerator
from app.evaluation.verifier_v3 import Phase3CVerifier
from app.evaluation.enrichment import CorpusEnricher
from app.evaluation.aggregator import CaseAggregator
from app.evaluation.orchestrator import Phase3DOrchestrator
from app.evaluation.provenance import ProvenanceResolver
from app.evaluation.finalizer import StructuralValidator, ArtifactWriter
from app.evaluation.profiler import LLMDocumentProfiler
from app.evaluation.exceptions import (
    BenchmarkAdmissionError,
    BenchmarkPopulationError,
    BenchmarkPopulationAccountingError,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")

def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return "unknown"

async def main():
    parser = argparse.ArgumentParser(description="Run RAG benchmark pipeline")
    parser.add_argument("--doc", required=True, help="Path to source document")
    parser.add_argument("--n-candidates", type=int, required=True, help="Number of candidates to generate")
    parser.add_argument("--mode", choices=["smoke", "standard", "comprehensive"], default="standard", help="Run mode")
    parser.add_argument("--out", help="Output directory")
    args = parser.parse_args()

    if args.n_candidates <= 0:
        raise ValueError("--n-candidates must be a positive integer")

    run_id = uuid.uuid4().hex
    output_dir = Path(args.out) if args.out else Path("data/benchmark") / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[run_benchmark] run_id={run_id}")

    # DOCUMENT REGISTRATION
    source_path = Path(args.doc)
    raw_bytes = source_path.read_bytes()
    document_hash = hashlib.sha256(raw_bytes).hexdigest()
    ext = source_path.suffix.lower()

    registered = Path("data/documents") / f"{document_hash}{ext}"
    registered.parent.mkdir(parents=True, exist_ok=True)

    if not registered.exists():
        shutil.copy2(args.doc, registered)

    if hashlib.sha256(registered.read_bytes()).hexdigest() != document_hash:
        raise RuntimeError("Document integrity check failed")

    # SOURCE LOADING
    documents = load_file(registered)
    if not documents:
        raise RuntimeError("Document produced no content")

    # COMPONENT WIRING
    settings = get_settings()

    llm = ChatOpenAI(
        model=settings.eval_generation_model,
        api_key=settings.eval_deepseek_api_key,
        base_url=settings.eval_deepseek_base_url,
        temperature=0.0,
    )

    provenance_resolver = ProvenanceResolver(
        document_dir="data/documents"
    )

    profiler = LLMDocumentProfiler(llm=llm)

    generator = CandidateGenerator(
        llm=llm,
        provenance_resolver=provenance_resolver,
    )

    verifier = Phase3CVerifier(llm=llm)

    enricher = CorpusEnricher()

    aggregator = CaseAggregator(settings=settings)

    orchestrator = Phase3DOrchestrator(
        verifier=verifier,
        enricher=enricher,
        aggregator=aggregator,
    )

    validator = StructuralValidator()

    writer = ArtifactWriter(
        output_dir=str(output_dir),
        validator=validator,
    )

    # STEP 1 — PROFILE
    profiler_result = await profiler.profile(documents)
    print(f"[profiler] Document type: {profiler_result.document_type} (confidence: {profiler_result.confidence:.2f})")

    # STEP 2 — GENERATE
    candidates = await generator.generate_candidates(
        document_hash=document_hash,
        profiler_result=profiler_result,
        budget=args.n_candidates,
    )
    
    n_generated = len(candidates)
    print(f"[generator] Generated {n_generated} candidates")

    # STEP 3 — PER-CANDIDATE PIPELINE
    n_admitted = 0
    n_rejected = 0
    n_disputed = 0
    n_pipeline_errors = 0

    per_case_verdicts = []
    seen_case_ids = set()
    seen_span_hashes = set()

    for i, candidate in enumerate(candidates, 1):
        candidate_id = candidate.case_id

        # 3A — DUPLICATE case_id INTEGRITY CHECK
        if candidate_id in seen_case_ids:
            logging.error(f"Duplicate case_id detected: {candidate_id}")
            n_pipeline_errors += 1
            per_case_verdicts.append({
                "case_id": candidate_id,
                "verdict": "pipeline_error"
            })
            print(f"[pipeline] Candidate {i}/{n_generated}: verdict=pipeline_error")
            continue

        seen_case_ids.add(candidate_id)

        # 3B — EXISTING 3B -> 3D PIPELINE
        try:
            result = await orchestrator.run_pipeline(candidate.to_dict())
            case_dict = result.partial_case_dict
        except BenchmarkAdmissionError:
            # 3C — EXCEPTION CLASSIFICATION (Policy rejection)
            n_rejected += 1
            per_case_verdicts.append({
                "case_id": candidate_id,
                "verdict": "rejected"
            })
            print(f"[pipeline] Candidate {i}/{n_generated}: verdict=rejected")
            continue
        except Exception as e:
            # 3C — EXCEPTION CLASSIFICATION (Pipeline errors)
            n_pipeline_errors += 1
            logging.exception(f"Unexpected pipeline exception for candidate {candidate_id}: {e}")
            per_case_verdicts.append({
                "case_id": candidate_id,
                "verdict": "pipeline_error"
            })
            print(f"[pipeline] Candidate {i}/{n_generated}: verdict=pipeline_error")
            continue

        # 3D — VERDICT CLASSIFICATION
        verdict = case_dict.get("verification", {}).get("verdict")
        actual_case_id = case_dict.get("case_id", candidate_id)

        if verdict == "rejected":
            n_rejected += 1
            per_case_verdicts.append({
                "case_id": actual_case_id,
                "verdict": "rejected"
            })
            print(f"[pipeline] Candidate {i}/{n_generated}: verdict=rejected")
            continue

        if verdict == "disputed":
            n_disputed += 1
            per_case_verdicts.append({
                "case_id": actual_case_id,
                "verdict": "disputed"
            })
            print(f"[pipeline] Candidate {i}/{n_generated}: verdict=disputed")
            continue

        if verdict != "accepted":
            n_pipeline_errors += 1
            logging.error(f"Unexpected terminal verdict for candidate {actual_case_id}: {verdict}")
            per_case_verdicts.append({
                "case_id": actual_case_id,
                "verdict": "pipeline_error"
            })
            print(f"[pipeline] Candidate {i}/{n_generated}: verdict=pipeline_error")
            continue

        # STEP 4 — PROVISIONAL CORPUS ENRICHMENT
        retrieval_profile = case_dict.get("retrieval_profile", {})
        corpus_position = retrieval_profile.get("corpus_position")

        # 4A — corpus_position ADMISSION POLICY
        if corpus_position is None:
            n_rejected += 1
            per_case_verdicts.append({
                "case_id": actual_case_id,
                "verdict": "rejected"
            })
            print(f"[pipeline] Candidate {i}/{n_generated}: verdict=rejected")
            continue

        # 4B — distractor_profile
        # PROVISIONAL — OD #5 NOT RESOLVED
        candidate_spans = {
            e.get("span_hash")
            for e in case_dict.get("evidence", [])
            if e.get("span_hash")
        }

        if candidate_spans & seen_span_hashes:
            distractor = "near_duplicate"
        else:
            distractor = "none"

        # 4C — retrieval_risk
        # PROVISIONAL — OD #5 NOT RESOLVED
        evidence_scope = retrieval_profile.get("evidence_scope", "single_span")
        
        if distractor in ("near_duplicate", "semantic_distractor"):
            risk = "high"
        elif evidence_scope == "multi_span":
            risk = "medium"
        else:
            risk = "low"

        # 4D — WRITE REQUIRED RETRIEVAL PROFILE FIELDS
        case_dict.setdefault("retrieval_profile", {})
        case_dict["retrieval_profile"]["distractor_profile"] = distractor
        case_dict["retrieval_profile"]["retrieval_risk"] = risk

        # 4E — ARTIFACT WRITING
        try:
            artifact_path = writer.write_case(case_dict)
            n_admitted += 1
            seen_span_hashes.update(candidate_spans)
            per_case_verdicts.append({
                "case_id": actual_case_id,
                "verdict": "accepted",
                "artifact_path": str(artifact_path.relative_to(output_dir))
            })
            print(f"[pipeline] Candidate {i}/{n_generated}: verdict=accepted")
        except Exception as e:
            n_pipeline_errors += 1
            logging.exception(f"ArtifactWriter failure for candidate {actual_case_id}: {e}")
            per_case_verdicts.append({
                "case_id": actual_case_id,
                "verdict": "pipeline_error"
            })
            print(f"[pipeline] Candidate {i}/{n_generated}: verdict=pipeline_error")

    # STEP 5 — OD-11 ACCOUNTING GATE
    total = n_admitted + n_rejected + n_disputed + n_pipeline_errors
    if total != n_generated:
        raise BenchmarkPopulationAccountingError(
            f"PIPELINE ACCOUNTING FAILURE: "
            f"{n_admitted}+{n_rejected}+"
            f"{n_disputed}+{n_pipeline_errors}"
            f"={total} != n_generated={n_generated}"
        )

    # STEP 6 — MANIFEST
    minimum_required_map = {
        "smoke": 5,
        "standard": 10,
        "comprehensive": 20
    }
    minimum_required = minimum_required_map[args.mode]
    
    admission_rate = n_admitted / n_generated if n_generated > 0 else 0.0
    population_admitted = n_admitted >= minimum_required

    manifest = {
        "schema_version": "1",
        "run_id": run_id,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "mode": args.mode,
        "document_path": str(source_path.resolve()),
        "document_hash": document_hash,
        "git_commit": get_git_commit(),
        "model_versions": {
            "generator_model": settings.eval_generation_model,
            "verifier_primary_model": settings.eval_generation_model,
            "verifier_secondary_model": getattr(settings, 'eval_sambanova_model', "unknown")
        },
        "population": {
            "n_generated": n_generated,
            "n_admitted": n_admitted,
            "n_rejected": n_rejected,
            "n_disputed": n_disputed,
            "n_pipeline_errors": n_pipeline_errors,
            "admission_rate": round(admission_rate, 4),
            "min_floor": minimum_required,
            "population_admitted": population_admitted
        },
        "per_case_verdicts": per_case_verdicts
    }

    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n[result] admitted={n_admitted}")
    print(f"         rejected={n_rejected}")
    print(f"         disputed={n_disputed}")
    print(f"         errors={n_pipeline_errors}")
    print(f"\n[manifest] Written: {manifest_path}")

    # STEP 7 — POPULATION FLOOR
    if not population_admitted:
        print(f"[status] Population NOT admitted ({n_admitted}/{minimum_required} floor)")
        raise BenchmarkPopulationError(
            f"Run produced {n_admitted} admitted cases, "
            f"below {minimum_required} floor ({args.mode} mode).",
            n_generated=n_generated,
            n_admitted=n_admitted,
            n_rejected=n_rejected,
            n_disputed=n_disputed,
            n_pipeline_errors=n_pipeline_errors,
            min_floor=minimum_required,
            mode=args.mode,
        )
    
    print("[status] Population admitted")

if __name__ == "__main__":
    asyncio.run(main())
