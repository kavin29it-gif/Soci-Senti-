"""
NLP and Text Normalization Pipeline.
Performs tokenization, lemmatization, language tagging, entity recognition,
and hashtag/mention/URL extraction.
"""

import re

# Common stopwords
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "from", "up", "down", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "this", "that",
    "it", "he", "she", "they", "we", "you", "i", "my", "your", "his", "her", "their"
}

# Simple language indicator wordsets for fast, zero-dependency language tagging
LANG_PATTERNS = {
    "es": {"el", "la", "los", "las", "un", "una", "de", "en", "que", "por", "para", "con"},
    "fr": {"le", "la", "les", "un", "une", "des", "du", "dans", "pour", "avec", "sur"},
    "de": {"der", "die", "das", "ein", "eine", "und", "in", "den", "von", "zu", "mit"},
}


class NLPPipeline:
    """Zero-dependency NLP processor providing tokenization, entity tagging, and linguistic extraction."""

    @staticmethod
    def detect_language(text: str, hint: str | None = None) -> str:
        """Determines ISO-639-1 language code using vocabulary intersection or platform hint."""
        if hint and hint in ["en", "es", "fr", "de"]:
            return hint

        words = set(re.findall(r"\b[a-zA-Z]{2,}\b", text.lower()))
        if not words:
            return "en"

        scores = {}
        for lang, indicator_words in LANG_PATTERNS.items():
            overlap = len(words.intersection(indicator_words))
            if overlap > 0:
                scores[lang] = overlap

        if scores:
            best_lang = max(scores, key=scores.get)
            if scores[best_lang] >= 2:
                return best_lang

        return "en"

    @staticmethod
    def extract_hashtags_and_mentions(text: str) -> tuple[list[str], list[str]]:
        """Extracts hashtags and @mentions from text."""
        hashtags = re.findall(r"#(\w+)", text)
        mentions = re.findall(r"@(\w+)", text)
        return hashtags, mentions

    @staticmethod
    def extract_entities(text: str) -> list[dict[str, str]]:
        """
        Lightweight entity recognizer for financial institutions, cryptos, and locations.
        """
        entities = []

        # Ticker / Crypto matching ($BTC, $ETH, $AURA, etc.)
        tickers = re.findall(r"\$([A-Z]{2,6})\b", text)
        for t in tickers:
            entities.append({"text": t, "label": "CRYPTO"})

        # Common financial entities
        financial_institutions = ["NordicCapital", "ApexReserve", "VanguardGlobal", "PacificTrust", "MeridianCredit"]
        for fi in financial_institutions:
            if fi.lower() in text.lower():
                entities.append({"text": fi, "label": "ORG"})

        # Cities / Locations
        cities = ["Zurich", "Frankfurt", "Chicago", "London", "Tokyo", "Singapore", "New York", "Toronto", "Sydney"]
        for city in cities:
            if city.lower() in text.lower():
                entities.append({"text": city, "label": "GPE"})

        return entities

    @classmethod
    def process(cls, text: str, lang_hint: str | None = None) -> dict:
        """
        Processes raw text and returns normalized NLP dictionary:
        {lang, tokens, entities, hashtags, mentions}
        """
        lang = cls.detect_language(text, lang_hint)
        raw_words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
        tokens = [w for w in raw_words if w not in STOPWORDS]
        hashtags, mentions = cls.extract_hashtags_and_mentions(text)
        entities = cls.extract_entities(text)

        return {
            "lang": lang,
            "tokens": tokens[:50], # top 50 normalized tokens
            "entities": entities,
            "hashtags": hashtags,
            "mentions": mentions
        }
