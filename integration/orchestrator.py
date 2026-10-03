"""Central PHISHGUARD-X email analysis orchestration."""

from pathlib import Path
import sys
import tempfile

from email_parser.parser import analyze_email as parse_email

from .fusion import fuse_results

PROJECT_ROOT = Path(__file__).resolve().parents[1]
URL_ML_ROOT = PROJECT_ROOT / "url_ml"
if str(URL_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(URL_ML_ROOT))

# Make sure the project root is on sys.path so `nlp` package is importable.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# -----------------------------------------------------------------------
# Eagerly import the URL analyzer NOW — before torch (DistilBERT) is ever
# loaded. This ensures XGBoost / joblib / numba are fully initialized
# before torch enters the process, avoiding the macOS fork+torch deadlock.
# -----------------------------------------------------------------------
_analyze_url = None
_url_import_error = None
try:
    from api.service import analyze_url as _analyze_url
except Exception as _exc:
    _url_import_error = f"URL analyzer unavailable: {_exc}"


def _run_nlp_analysis(nlp_text: str) -> dict:
    """Run DistilBERT NLP analysis; return structured result or error dict."""
    try:
        from nlp.distilbert import analyze_text
        return analyze_text(nlp_text)
    except Exception as error:
        return {
            "prediction": None,
            "probability": None,
            "risk_score": None,
            "model": "distilbert-phishguard-v1",
            "error": f"NLP analyzer unavailable: {error}",
        }


def _analyze_parsed_email(parsed_email):
    url_results = []
    url_errors = []

    # ── 1. URL / XGBoost analysis (runs before torch is imported) ──
    for url in parsed_email.get("urls", []):
        if _analyze_url is None:
            url_errors.append({"url": url, "error": _url_import_error})
            continue
        try:
            url_results.append(_analyze_url(url))
        except Exception as error:
            url_errors.append({"url": url, "error": str(error)})

    # ── 2. NLP / DistilBERT analysis (imports torch lazily, runs after XGBoost) ──
    nlp_text = parsed_email.get("nlp_text", "")
    nlp_result = _run_nlp_analysis(nlp_text)

    # ── 3. Fuse all results ──
    result = fuse_results(parsed_email, url_results, url_errors, nlp_result)
    result["email_id"] = parsed_email.get("email_id")
    result["parsed_email"] = parsed_email
    return result


def analyze_email(file_path):
    """Analyze an email file through all currently available components."""
    return _analyze_parsed_email(parse_email(str(Path(file_path))))


def analyze_email_bytes(raw_email):
    """Analyze raw RFC 822 email bytes without retaining an uploaded file."""
    with tempfile.NamedTemporaryFile(suffix=".eml") as temporary_file:
        temporary_file.write(raw_email)
        temporary_file.flush()
        return analyze_email(temporary_file.name)

