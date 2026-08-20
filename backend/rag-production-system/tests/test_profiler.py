import pytest
import json
from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from app.evaluation.profiler import LLMDocumentProfiler, ProfilerResult

# --- MOCKS ---

class MockChatModel:
    def __init__(self, response_json: dict):
        self.response_json = response_json

    async def ainvoke(self, messages):
        return AIMessage(content=json.dumps(self.response_json))

@pytest.fixture
def doc_legal():
    return Document(page_content="This Agreement constitutes a binding contract between the parties. Governing law shall be the State of Delaware.")

@pytest.fixture
def doc_technical():
    return Document(page_content="Abstract. We present a novel architecture for RAG systems using child-parent hierarchical retrieval. Experiments show a 15% increase in nDCG@10.")

@pytest.fixture
def doc_tabular():
    return Document(page_content="""
| Region | Q1 Sales | Q2 Sales |
|---|---|---|
| North | 1500 | 1800 |
| South | 1200 | 1100 |
""")

@pytest.fixture
def empty_doc():
    return Document(page_content="   \n  ")


# --- TESTS ---

@pytest.mark.asyncio
async def test_profiler_legal_high_confidence(doc_legal):
    llm = MockChatModel({"document_type": "legal", "type_confidence": 0.95})
    profiler = LLMDocumentProfiler(llm)
    result = await profiler.profile([doc_legal])
    assert result.document_type == "legal"
    assert result.type_confidence == 0.95

@pytest.mark.asyncio
async def test_profiler_technical_high_confidence(doc_technical):
    llm = MockChatModel({"document_type": "technical-research", "type_confidence": 0.85})
    profiler = LLMDocumentProfiler(llm)
    result = await profiler.profile([doc_technical])
    assert result.document_type == "technical-research"
    assert result.type_confidence == 0.85

@pytest.mark.asyncio
async def test_profiler_tabular_high_confidence(doc_tabular):
    llm = MockChatModel({"document_type": "tabular", "type_confidence": 0.75})
    profiler = LLMDocumentProfiler(llm)
    result = await profiler.profile([doc_tabular])
    assert result.document_type == "tabular"
    assert result.type_confidence == 0.75

# The 7 taxonomy categories covered
@pytest.mark.parametrize("category", ["policy", "manual", "narrative", "general"])
@pytest.mark.asyncio
async def test_profiler_taxonomy_categories(category, doc_legal):
    llm = MockChatModel({"document_type": category, "type_confidence": 0.90})
    profiler = LLMDocumentProfiler(llm)
    result = await profiler.profile([doc_legal])
    assert result.document_type == category

# Boundaries
@pytest.mark.parametrize("input_conf, expected_type, expected_conf", [
    (0.00, "general", 0.00),
    (0.59, "general", 0.59),
    (0.599, "general", 0.599),
    (0.60, "legal", 0.60),
    (0.61, "legal", 0.61),
    (1.00, "legal", 1.00),
    (1.05, "legal", 1.00),  # Clamped
    (-0.1, "general", 0.0), # Clamped and falls back
])
@pytest.mark.asyncio
async def test_confidence_boundary(input_conf, expected_type, expected_conf, doc_legal):
    llm = MockChatModel({"document_type": "legal", "type_confidence": input_conf})
    profiler = LLMDocumentProfiler(llm)
    result = await profiler.profile([doc_legal])
    assert result.document_type == expected_type
    assert abs(result.type_confidence - expected_conf) < 1e-6

# Invalid LLM response handling
@pytest.mark.asyncio
async def test_invalid_json_fallback(doc_legal):
    class BadMockChatModel:
        async def ainvoke(self, messages):
            return AIMessage(content="I think this is a legal document, maybe 80% confident.")

    profiler = LLMDocumentProfiler(BadMockChatModel())
    result = await profiler.profile([doc_legal])
    assert result.document_type == "general"
    assert result.type_confidence == 0.0

@pytest.mark.asyncio
async def test_invalid_taxonomy_fallback(doc_legal):
    llm = MockChatModel({"document_type": "novel", "type_confidence": 0.99})
    profiler = LLMDocumentProfiler(llm)
    result = await profiler.profile([doc_legal])
    assert result.document_type == "general"

# Empty input handling
@pytest.mark.asyncio
async def test_empty_documents():
    profiler = LLMDocumentProfiler(MockChatModel({"document_type": "legal", "type_confidence": 0.99}))
    result = await profiler.profile([])
    assert result.document_type == "general"
    assert result.type_confidence == 0.0

@pytest.mark.asyncio
async def test_whitespace_documents(empty_doc):
    profiler = LLMDocumentProfiler(MockChatModel({"document_type": "legal", "type_confidence": 0.99}))
    result = await profiler.profile([empty_doc])
    assert result.document_type == "general"
    assert result.type_confidence == 0.0
