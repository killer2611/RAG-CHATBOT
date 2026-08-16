from pathlib import Path

from app.rag.loaders import load_file


def test_txt_loader(tmp_path: Path):
    file = tmp_path / "sample.txt"
    file.write_text("hello\nworld", encoding="utf-8")
    docs = load_file(file)
    assert len(docs) == 1
    assert "hello" in docs[0].page_content
