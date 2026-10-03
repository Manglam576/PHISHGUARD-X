"""
PHISHGUARD-X NLP Module — DistilBERT Inference Wrapper.

Loads the fine-tuned DistilBertForSequenceClassification model from the
local DISTILBERT/ directory and exposes a single public function:

    analyze_text(text: str) -> dict

Label convention (assumed from standard training practice):
    label 0 = legitimate
    label 1 = phishing
"""

import os

# -----------------------------------------------------------------------
# CRITICAL: must be set BEFORE torch is imported.
# OMP_NUM_THREADS=1  → prevents PyTorch's OpenMP thread pool from
#   competing with loky semaphores left by XGBoost/joblib on macOS.
# TOKENIZERS_PARALLELISM=false → suppresses the HuggingFace fast-tokenizer
#   fork warning when multiprocessing is already in use.
# -----------------------------------------------------------------------
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from pathlib import Path
import sys

# -------------------------------------------------------
# Ensure project root is on the path so this module can
# be imported from anywhere in the project.
# -------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MODEL_DIR = PROJECT_ROOT / "DISTILBERT"
MODEL_VERSION = "distilbert-phishguard-v1"

# -------------------------------------------------------
# Lazy model loading — load once on first call.
# This avoids a ~267 MB torch load at import time.
# -------------------------------------------------------
_tokenizer = None
_model = None
_device = None


def _load():
    """Load tokenizer and model from DISTILBERT/ (once)."""
    global _tokenizer, _model, _device

    if _model is not None:
        return  # Already loaded

    # Re-assert thread limits here in case another module reset them
    # before this function was first called.
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    try:
        import torch
        from transformers import (
            DistilBertForSequenceClassification,
            BertTokenizer,
        )
    except ImportError as exc:
        raise ImportError(
            "transformers and torch are required for the NLP module. "
            "Run: pip install transformers torch"
        ) from exc

    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            f"DistilBERT model directory not found: {MODEL_DIR}"
        )

    # Use CPU by default; GPU picked up automatically if available.
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    _tokenizer = BertTokenizer.from_pretrained(str(MODEL_DIR))
    _model = DistilBertForSequenceClassification.from_pretrained(
        str(MODEL_DIR)
    )
    _model.to(_device)
    _model.eval()


def analyze_text(text: str) -> dict:
    """
    Run NLP phishing detection on the provided email text.

    Parameters
    ----------
    text : str
        The email body / NLP text produced by the email parser
        (typically: "Subject: ...\n\n<plain body>\n\n<html clean text>").

    Returns
    -------
    dict
        {
            "prediction":  "phishing" | "legitimate",
            "probability": float  (probability of phishing, 0-1),
            "risk_score":  int    (0-100),
            "model":       str
        }
    """
    if not text or not text.strip():
        return {
            "prediction": None,
            "probability": None,
            "risk_score": None,
            "model": MODEL_VERSION,
            "error": "No text provided",
        }

    try:
        import torch

        _load()

        # -------------------------------------------------------
        # Tokenise — truncate to 512 tokens (model max).
        # -------------------------------------------------------
        inputs = _tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        inputs = {k: v.to(_device) for k, v in inputs.items()}

        # -------------------------------------------------------
        # Forward pass (no gradient needed).
        # -------------------------------------------------------
        with torch.no_grad():
            outputs = _model(**inputs)
            logits = outputs.logits

        # Softmax → probabilities
        probabilities = torch.softmax(logits, dim=1)[0]

        # Label 1 = phishing (standard convention)
        phishing_probability = float(probabilities[1].item())

        prediction = (
            "phishing" if phishing_probability >= 0.5 else "legitimate"
        )

        risk_score = round(phishing_probability * 100)

        return {
            "prediction": prediction,
            "probability": round(phishing_probability, 4),
            "risk_score": risk_score,
            "model": MODEL_VERSION,
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "prediction": None,
            "probability": None,
            "risk_score": None,
            "model": MODEL_VERSION,
            "error": str(exc),
        }
