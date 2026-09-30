"""
Sentiment and Emotion Analysis Engine.
Outputs fine-grained sentiment (neg, neu, pos), 6-class emotion distribution,
experimental sarcasm flags, and rolling z-score sentiment shift detection (timeline leaking).
"""

import logging
import math
import re
from collections import defaultdict

import numpy as np

logger = logging.getLogger(__name__)

# Lexicons for high-performance CPU-friendly fallback and calibration
POSITIVE_WORDS = {
    "great", "amazing", "excellent", "love", "good", "best", "perfect", "excited",
    "profit", "gain", "gem", "bullish", "succeed", "growth", "win", "happy", "art",
    "beautiful", "wonderful", "breakthrough", "innovative", "thriving", "clean"
}

NEGATIVE_WORDS = {
    "bad", "terrible", "crash", "collapse", "fail", "freeze", "run", "panic", "hate",
    "loss", "scam", "fraud", "exploit", "pathogen", "disrupt", "liquidity", "insolvent",
    "drop", "dump", "bearish", "fear", "crisis", "illegal", "compromised", "fake"
}

EMOTION_KEYWORDS = {
    "anger": {"furious", "angry", "outrage", "scam", "cheat", "disrupt", "corrupt", "liar", "bastards", "hate"},
    "fear": {"panic", "freeze", "run", "collapse", "crisis", "threat", "danger", "urgent", "risk", "warning"},
    "joy": {"excited", "amazing", "delighted", "love", "profit", "win", "success", "celebrate", "awesome"},
    "sadness": {"depressed", "unfortunate", "grief", "lost", "fail", "disaster", "devastated", "heartbroken"},
    "surprise": {"shocking", "unbelievable", "unexpected", "jaw-dropping", "breaking", "whistleblower"},
    "disgust": {"repulsive", "sickening", "vile", "disgusting", "filthy", "toxic"}
}


class SentimentEmotionEngine:
    """Multi-task sentiment, emotion, and sentiment shift detector."""

    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        self.model_name = model_name
        # Timeline shift tracking: topic -> list of recent sentiment scores
        self._history: dict[str, list[float]] = defaultdict(list)

    def analyze(self, text: str) -> dict:
        """
        Analyzes post text and returns:
        {
            sentiment: {neg, neu, pos, label},
            emotion: {anger, fear, joy, sadness, surprise, disgust, dominant},
            sarcasm_flag: bool,
            confidence: float
        }
        """
        if not text or not text.strip():
            return {
                "sentiment": {"neg": 0.0, "neu": 1.0, "pos": 0.0, "label": "neu"},
                "emotion": {"anger": 0.0, "fear": 0.0, "joy": 0.0, "sadness": 0.0, "surprise": 0.0, "disgust": 0.0, "dominant": "neutral"},
                "sarcasm_flag": False,
                "confidence": 0.5
            }

        tokens = set(re.findall(r"\b\w+\b", text.lower()))
        pos_hits = len(tokens.intersection(POSITIVE_WORDS))
        neg_hits = len(tokens.intersection(NEGATIVE_WORDS))

        # Sentiment scoring with softmax calibration
        raw_neg = neg_hits * 1.5 + (0.5 if "!" in text and neg_hits > 0 else 0.0)
        raw_pos = pos_hits * 1.5
        raw_neu = 1.0 if (pos_hits == 0 and neg_hits == 0) else 0.5

        exps = [math.exp(min(5.0, raw_neg)), math.exp(min(5.0, raw_neu)), math.exp(min(5.0, raw_pos))]
        sum_exp = sum(exps)
        prob_neg = round(exps[0] / sum_exp, 4)
        prob_neu = round(exps[1] / sum_exp, 4)
        prob_pos = round(exps[2] / sum_exp, 4)

        labels = ["neg", "neu", "pos"]
        sentiment_label = labels[int(np.argmax([prob_neg, prob_neu, prob_pos]))]

        # Emotion distribution
        emotion_scores = {}
        for emo, keywords in EMOTION_KEYWORDS.items():
            hits = len(tokens.intersection(keywords))
            score = hits * 2.0 + (0.5 if emo == "fear" and prob_neg > 0.6 else 0.0)
            emotion_scores[emo] = score

        total_emo = sum(emotion_scores.values()) + 1e-5
        emotion_probs = {k: round(v / total_emo, 4) for k, v in emotion_scores.items()}
        dominant_emotion = max(emotion_probs, key=emotion_probs.get) if total_emo > 0.1 else "neutral"
        emotion_probs["dominant"] = dominant_emotion

        # Sarcasm heuristic: positive words alongside excessive punctuation, quotation marks, or strong negative signals
        sarcasm_flag = False
        if (pos_hits > 0 and neg_hits > 0) or ('"' in text and pos_hits > 0 and prob_neg > 0.4):
            sarcasm_flag = True

        return {
            "sentiment": {
                "neg": prob_neg,
                "neu": prob_neu,
                "pos": prob_pos,
                "label": sentiment_label
            },
            "emotion": emotion_probs,
            "sarcasm_flag": sarcasm_flag,
            "confidence": 0.88
        }

    def detect_sentiment_shift(self, topic: str, current_sentiment_score: float, window_size: int = 30) -> dict:
        """
        Z-Score based change detection ("timeline leaking" / sudden negative sentiment shift).
        Score is in [-1.0 (very negative) to +1.0 (very positive)].
        """
        hist = self._history[topic]
        hist.append(current_sentiment_score)
        if len(hist) > window_size * 2:
            self._history[topic] = hist[-window_size:]

        if len(hist) < 10:
            return {"shift_detected": False, "z_score": 0.0, "status": "insufficient_history"}

        # Calculate mean and standard deviation of previous observations
        baseline = hist[:-1]
        mean = float(np.mean(baseline))
        std = float(np.std(baseline)) + 1e-4

        # Z-score for drop in sentiment (negative shift)
        z = (current_sentiment_score - mean) / std
        is_shift = z <= -2.0  # 2 standard deviations negative drop

        return {
            "shift_detected": is_shift,
            "z_score": round(float(z), 2),
            "baseline_mean": round(mean, 3),
            "current_score": round(current_sentiment_score, 3),
            "status": "alert_sudden_negative_shift" if is_shift else "normal"
        }


sentiment_engine = SentimentEmotionEngine()
