import json
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from pydantic import ValidationError

from app.evaluation.datasets import load_golden_cases, GoldenCase, GoldenSource
from app.models.schemas import EvaluateRequest
from app.evaluation.runner import EvaluationRunner
from app.core.config import get_settings
from app.rag.service import RagService


def test_evaluate_request_schema():
    # Test 1: existing 5-case default
    req = EvaluateRequest()
    assert req.case_limit == 5

    # Test 2: case_limit=10
    req = EvaluateRequest(case_limit=10)
    assert req.case_limit == 10

    # Test 4: invalid case_limit
    with pytest.raises(ValidationError):
        EvaluateRequest(case_limit=0)
    
    with pytest.raises(ValidationError):
        EvaluateRequest(case_limit=-5)


def test_source_metadata_parsing():
    # Test 5 & 6: source metadata parsing & backward-compatible dataset without source metadata
    dummy_data = [
        {
            "question": "Q1",
            "answer": "A1"
        },
        {
            "question": "Q2",
            "answer": "A2",
            "source": {
                "source_name": "microled_paper.pdf",
                "source_id": "doc123"
            }
        }
    ]
    with tempfile.TemporaryDirectory(dir=".") as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "test_dataset.json"
        test_file.write_text(json.dumps(dummy_data))

        cases = load_golden_cases(test_file)
        assert len(cases) == 2
    
    # Backward compatible (no source)
    assert cases[0].question == "Q1"
    assert cases[0].source is None
    
    # Source metadata parsed
    assert cases[1].question == "Q2"
    assert cases[1].source is not None
    assert cases[1].source.source_name == "microled_paper.pdf"
    assert cases[1].source.source_id == "doc123"


@pytest.mark.asyncio
async def test_runner_case_limit():
    # Setup dummy dataset with 8 items
    dummy_data = [{"question": f"Q{i}", "answer": f"A{i}"} for i in range(8)]
    with tempfile.TemporaryDirectory(dir=".") as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "test_limit.json"
        test_file.write_text(json.dumps(dummy_data))

        settings = get_settings()
        settings.eval_report_dir = tmp_path / "reports"
        settings.eval_report_dir.mkdir()
        
        mock_rag = AsyncMock(spec=RagService)
        # mock answer_with_context to return simple output and empty retrieved
        mock_rag.answer_with_context.return_value = ("Generated Answer", [])

        runner = EvaluationRunner(settings, mock_rag)

        # Patch evaluate to return dummy results so we don't actually call the API
        with patch("app.evaluation.runner.evaluate") as mock_eval:
            mock_result = MagicMock()
            dummy_res = []
            for i in range(8):
                res = MagicMock()
                res.input = f"Q{i}"
                res.expected_output = f"A{i}"
                res.actual_output = "Generated Answer"
                res.success = True
                res.metrics_data = []
                dummy_res.append(res)
            mock_result.test_results = dummy_res
            mock_eval.return_value = mock_result
            
            # Test 2: case_limit=10 but bounded by dataset size (8)
            # Test 3: case_limit bounded by dataset size
            report_path = await runner.run("job123", test_file=str(test_file), case_limit=10)
            
            # Verify it ran 8 times
            assert mock_rag.answer_with_context.call_count == 8
            
            # The meta json should record 8 cases evaluated
            meta_file = Path(report_path).with_name(Path(report_path).stem + "_meta.json")
            meta_data = json.loads(meta_file.read_text())
            assert meta_data["cases_evaluated"] == 8


@pytest.mark.asyncio
async def test_source_match_mismatch():
    # Test 7 & 8: Source match and Source mismatch
    dummy_data = [
        {
            "question": "Match Q",
            "answer": "A",
            "source": {"source_name": "target.pdf"}
        },
        {
            "question": "Mismatch Q",
            "answer": "A",
            "source": {"source_name": "target.pdf"}
        }
    ]
    with tempfile.TemporaryDirectory(dir=".") as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "test_source.json"
        test_file.write_text(json.dumps(dummy_data))

        settings = get_settings()
        settings.eval_report_dir = tmp_path / "reports"
        settings.eval_report_dir.mkdir(exist_ok=True)
        
        mock_rag = AsyncMock(spec=RagService)
        
        class DummyDoc:
            def __init__(self, name):
                self.metadata = {"source_name": name}
                self.page_content = "content"
                
        class DummyItem:
            def __init__(self, name):
                self.document = DummyDoc(name)
                
        # First call returns matching source, second call returns mismatching source
        mock_rag.answer_with_context.side_effect = [
            ("Ans1", [DummyItem("target.pdf")]),
            ("Ans2", [DummyItem("wrong.pdf")])
        ]

        runner = EvaluationRunner(settings, mock_rag)

        with patch("app.evaluation.runner.evaluate") as mock_eval:
            mock_result = MagicMock()
            # Mock the successful DeepEval result for the first case
            res1 = MagicMock()
            res1.input = "Match Q"
            res1.expected_output = "A"
            res1.actual_output = "Ans1"
            res1.success = True
            res1.metrics_data = []
            mock_result.test_results = [res1]
            mock_eval.return_value = mock_result
            
            report_path = await runner.run("job_src", test_file=str(test_file), case_limit=5)
            
            # Read the CSV output
            import pandas as pd
            df = pd.read_csv(report_path)
            
            # Should have 2 rows
            assert len(df) == 2
            
            # First row passed DeepEval (no source_match_status)
            row1 = df[df['question'] == 'Match Q'].iloc[0]
            assert row1['success'] == True
            assert pd.isna(row1.get('source_match_status'))
            
            # Second row was bypassed (SOURCE_MISMATCH)
            row2 = df[df['question'] == 'Mismatch Q'].iloc[0]
            assert row2['success'] == False
            assert row2['source_match_status'] == 'SOURCE_MISMATCH'


@pytest.mark.asyncio
async def test_job_states():
    # Test 9 & 10: Failed and successful job state transitions
    from app.api.jobs import job_manager, Job
    from app.models.schemas import EvaluateRequest
    from app.api.routes_evaluate import _run_job
    
    job = await job_manager.create()
    
    # Successful
    runner_mock = AsyncMock(spec=EvaluationRunner)
    runner_mock.run.return_value = "data/reports/fake.csv"
    req = EvaluateRequest()
    
    await _run_job(job, req, runner_mock)
    
    final_job = await job_manager.get(job.job_id)
    assert final_job.status == "completed"
    assert final_job.progress == 100
    
    # Failed
    job2 = await job_manager.create()
    runner_fail = AsyncMock(spec=EvaluationRunner)
    runner_fail.run.side_effect = RuntimeError("Catastrophic API failure")
    
    await _run_job(job2, req, runner_fail)
    
    final_job2 = await job_manager.get(job2.job_id)
    assert final_job2.status == "failed"
    assert final_job2.error == "Catastrophic API failure"
    assert final_job2.progress == 100
