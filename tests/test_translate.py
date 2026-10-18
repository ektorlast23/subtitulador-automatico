import pytest

from subtitulador.translate import (
    DeepLTranslator,
    MarianTranslator,
    PassthroughTranslator,
    TranslationError,
    get_translator,
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


def test_marian_registered():
    translator = get_translator("marian")
    assert isinstance(translator, MarianTranslator)
    assert translator.name == "marian"


def test_marian_unsupported_pair_raises():
    with pytest.raises(TranslationError):
        MarianTranslator().translate(["Hola"], source="es", target="en")
