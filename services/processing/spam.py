"""
Rule-Based and Heuristic Spam Classifier.
Produces a normalized spam_score in [0.0, 1.0] and categorizes drop reasons.
"""

import re

SPAM_KEYWORDS = [
    r"\bmake\s+\$\d+",
    r"\bwork\s+from\s+home\b",
    r"\bpassive\s+income\b",
    r"\beasy\s+cash\b",
    r"\breplica\b",
    r"\bdiscount\s+code\b",
    r"\bfree\s+worldwide\s+shipping\b",
    r"\blose\s+\d+\s+lbs\b",
    r"\bone\s+simple\s+bizarre\b",
    r"\bcrypto\s+signals\b",
    r"\b\d+%\s+win\s+rate\b",
    r"\bguaranteed\s+vip\b",
    r"\bfree\s+hd\s+streaming\b",
    r"\bno\s+credit\s+card\s+required\b",
    r"\bclick\s+here\b",
    r"\btelegram\s+channel\s+access\b",
    r"\bexclusive\s+deal\b",
]

SPAM_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SPAM_KEYWORDS]


class SpamFilter:
    """Heuristic spam detector evaluating text structure, repetitive patterns, and keyword signals."""

    def __init__(self, threshold: float = 0.70):
        self.threshold = threshold

    def score(self, text: str) -> tuple[float, str]:
        """
        Evaluates post text and returns (spam_score, reason).
        Score is in [0.0, 1.0].
        """
        if not text or not text.strip():
            return 0.0, "clean"

        reasons = []
        score = 0.0

        # 1. Check keyword matches
        keyword_hits = 0
        for pattern in SPAM_PATTERNS:
            if pattern.search(text):
                keyword_hits += 1

        if keyword_hits >= 2:
            score += 0.55
            reasons.append(f"multiple_spam_keywords({keyword_hits})")
        elif keyword_hits == 1:
            score += 0.35
            reasons.append("spam_keyword_match")

        # 2. Check excessive URLs / shorteners
        urls = re.findall(r"https?://\S+|www\.\S+|bit\.ly/\S+|tinyurl\.com/\S+", text)
        if len(urls) >= 2:
            score += 0.30
            reasons.append(f"excess_urls({len(urls)})")
        elif len(urls) == 1 and ("bit.ly" in text or "tinyurl" in text or ".xyz" in text):
            score += 0.20
            reasons.append("suspicious_shortener")

        # 3. Repeated character / exclamation spam
        if re.search(r"[!]{3,}|\?{3,}|\${3,}", text):
            score += 0.20
            reasons.append("repeated_punctuation")

        # 4. Excessive capitalization (shouting)
        letters = [c for c in text if c.isalpha()]
        if len(letters) > 15:
            upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
            if upper_ratio > 0.45:
                score += 0.25
                reasons.append(f"excessive_caps({upper_ratio:.2f})")

        # 5. Repeated word repetitions
        words = re.findall(r"\b\w+\b", text.lower())
        if len(words) > 8:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.40:
                score += 0.25
                reasons.append("repetitive_content")

        normalized_score = min(1.0, score)
        primary_reason = ", ".join(reasons) if reasons else "clean"
        return normalized_score, primary_reason

    def is_spam(self, text: str) -> tuple[bool, float, str]:
        """Returns (is_spam, score, reason)."""
        score, reason = self.score(text)
        return (score >= self.threshold), score, reason
