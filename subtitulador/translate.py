from __future__ import annotations


class TranslationError(RuntimeError):
    pass


class PassthroughTranslator:
    name = "passthrough"

    def translate(
        self, texts: list[str], source: str = "en", target: str = "es"
    ) -> list[str]:
        return list(texts)


class DeepLTranslator:
    name = "deepl"

    def __init__(self, endpoint: str = "https://api-free.deepl.com/v2/translate") -> None:
        self.endpoint = endpoint

    def translate(
        self, texts: list[str], source: str = "en", target: str = "es"
    ) -> list[str]:
        import os

        import httpx

        api_key = os.environ.get("DEEPL_API_KEY")
        if not api_key:
            raise TranslationError(
                "Falta la variable de entorno DEEPL_API_KEY para usar DeepL."
            )
        response = httpx.post(
            self.endpoint,
            headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
            data={
                "text": texts,
                "source_lang": source.upper(),
                "target_lang": target.upper(),
            },
            timeout=60.0,
        )
        response.raise_for_status()
        payload = response.json()
        return [item["text"] for item in payload["translations"]]


class NLLBTranslator:
    name = "nllb"

    _LANG_MAP = {"en": "eng_Latn", "es": "spa_Latn"}

    def __init__(self, model_name: str = "facebook/nllb-200-distilled-600M") -> None:
        self.model_name = model_name

    def translate(
        self, texts: list[str], source: str = "en", target: str = "es"
    ) -> list[str]:
        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:
            raise TranslationError(
                "transformers/torch no estan instalados. Instala las dependencias "
                "GPU con 'pip install -r requirements-gpu.txt'."
            ) from exc

        try:
            src_lang = self._LANG_MAP[source]
            tgt_lang = self._LANG_MAP[target]
        except KeyError as exc:
            raise TranslationError(
                f"Idioma no soportado por NLLB: {source!r}->{target!r}"
            ) from exc

        device = "cuda" if torch.cuda.is_available() else "cpu"
        tokenizer = AutoTokenizer.from_pretrained(self.model_name, src_lang=src_lang)
        model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        model.to(device)
        tokenizer.src_lang = src_lang
        tgt_id = tokenizer.convert_tokens_to_ids(tgt_lang)

        results: list[str] = []
        for text in texts:
            encoded = tokenizer(text, return_tensors="pt").to(device)
            generated = model.generate(
                **encoded,
                forced_bos_token_id=tgt_id,
                max_length=512,
            )
            results.append(
                tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
            )
        return results


def _passthrough() -> PassthroughTranslator:
    return PassthroughTranslator()


def _deepl() -> DeepLTranslator:
    return DeepLTranslator()


def _nllb() -> NLLBTranslator:
    return NLLBTranslator()


TRANSLATORS = {
    "passthrough": _passthrough,
    "deepl": _deepl,
    "nllb": _nllb,
}


def get_translator(name: str):
    try:
        factory = TRANSLATORS[name]
    except KeyError as exc:
        raise TranslationError(
            f"Traductor desconocido: {name!r}. Opciones: {sorted(TRANSLATORS)}"
        ) from exc
    return factory()


def translate_texts(
    texts: list[str],
    source: str = "en",
    target: str = "es",
    translator: str = "passthrough",
) -> list[str]:
    return get_translator(translator).translate(texts, source, target)
