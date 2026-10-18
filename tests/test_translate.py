import pytest

from subtitulador.translate import (
    DeepLTranslator,
    PassthroughTranslator,
    TranslationError,
    translate_texts,
)


def test_passthrough_returns_same():
    texts = ["Hello", "World"]
    assert PassthroughTranslator().translate(texts) == texts
    assert translate_texts(texts) == texts


def test_deepl_without_key_raises(monkeypatch):
    monkeypatch.delenv("DEEPL_API_KEY", raising=False)
    with pytest.raises(TranslationError) as excinfo:
        DeepLTranslator().translate(["Hello"])
    assert "DEEPL_API_KEY" in str(excinfo.value)
