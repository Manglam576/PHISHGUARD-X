"""Conservative evidence fusion for currently available analyzers."""


def _header_findings(parsed_email):
    findings = []
    authentication = parsed_email.get("authentication", {})

    for name in ("spf", "dkim", "dmarc"):
        value = authentication.get(name, "unknown")
        if value not in {"pass", "unknown"}:
            findings.append(f"{name.upper()} authentication result: {value}")

    sender_analysis = parsed_email.get("sender_domain_analysis", {})
    for mismatch_name, mismatch in sender_analysis.get("mismatches", {}).items():
        if mismatch:
            findings.append(mismatch_name.replace("_", " ").capitalize())

    return findings


def _attachment_findings(parsed_email):
    findings = []
    for attachment in parsed_email.get("attachments", []):
        if attachment.get("suspicious"):
            reason = attachment.get("reason") or "Suspicious attachment"
            findings.append(f"{attachment.get('filename', 'Attachment')}: {reason}")
    return findings


def fuse_results(parsed_email, url_results, url_errors, nlp_result=None):
    """Combine available evidence without inventing unavailable probabilities.

    Parameters
    ----------
    parsed_email : dict
        Output of email_parser.parser.analyze_email().
    url_results : list[dict]
        Per-URL XGBoost analysis results.
    url_errors : list[dict]
        URLs that could not be analyzed and their error messages.
    nlp_result : dict | None
        DistilBERT NLP analysis result, or None if not yet available.
    """

    # ------------------------------------------------------------------
    # URL signal
    # ------------------------------------------------------------------
    successful_probabilities = [item["probability"] for item in url_results]
    aggregate_url_probability = (
        max(successful_probabilities) if successful_probabilities else None
    )

    # ------------------------------------------------------------------
    # NLP signal
    # ------------------------------------------------------------------
    nlp_probability = None
    nlp_status = "unavailable"

    if nlp_result is not None:
        if nlp_result.get("error"):
            nlp_status = "error"
        elif nlp_result.get("probability") is not None:
            nlp_probability = nlp_result["probability"]
            nlp_status = "ok"

    # ------------------------------------------------------------------
    # Header / attachment evidence
    # ------------------------------------------------------------------
    header_findings = _header_findings(parsed_email)
    attachment_findings = _attachment_findings(parsed_email)

    # ------------------------------------------------------------------
    # Fuse numeric signals: average all available probabilities.
    # Missing signals are excluded (not treated as 0).
    # ------------------------------------------------------------------
    available_signals = [
        p for p in [aggregate_url_probability, nlp_probability]
        if p is not None
    ]

    # Heuristic boost: each header finding adds +0.05 (capped at 0.20).
    header_boost = min(len(header_findings) * 0.05, 0.20)

    # Heuristic boost: each suspicious attachment adds +0.10 (capped at 0.20).
    attachment_boost = min(len(attachment_findings) * 0.10, 0.20)

    if available_signals:
        base_probability = sum(available_signals) / len(available_signals)
        threat_probability = min(
            base_probability + header_boost + attachment_boost, 1.0
        )
        risk_score = round(threat_probability * 100)
        verdict = "phishing" if threat_probability >= 0.5 else "legitimate"
    else:
        # No numeric signal at all — use header/attachment evidence only
        # to decide inconclusiveness vs. low suspicion.
        if header_findings or attachment_findings:
            boost = header_boost + attachment_boost
            threat_probability = min(boost, 1.0)
            risk_score = round(threat_probability * 100)
            verdict = "suspicious" if threat_probability >= 0.1 else "inconclusive"
        else:
            threat_probability = None
            risk_score = None
            verdict = "inconclusive"

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------
    explanation = []
    for result in url_results:
        explanation.extend(result.get("explanation", []))

    if nlp_probability is not None:
        label = nlp_result.get("prediction", "unknown")
        explanation.append(
            f"NLP model classified email body as '{label}' "
            f"(probability: {nlp_probability:.2f})"
        )
    elif nlp_status == "error" and nlp_result:
        explanation.append(
            f"NLP analysis failed: {nlp_result.get('error', 'unknown error')}"
        )

    explanation.extend(header_findings)
    explanation.extend(attachment_findings)

    if url_errors:
        explanation.append(f"{len(url_errors)} URL(s) could not be analyzed")

    if not explanation and threat_probability is None:
        explanation.append("No numeric analyzer result is currently available")

    # ------------------------------------------------------------------
    # Final structured result
    # ------------------------------------------------------------------
    return {
        "email_verdict": verdict,
        "threat_probability": threat_probability,
        "risk_score": risk_score,
        "url_analysis": {
            "urls_found": len(parsed_email.get("urls", [])),
            "urls": url_results,
            "aggregate_probability": aggregate_url_probability,
            "errors": url_errors,
        },
        "nlp_analysis": {
            "status": nlp_status,
            "prediction": nlp_result.get("prediction") if nlp_result else None,
            "probability": nlp_probability,
            "risk_score": nlp_result.get("risk_score") if nlp_result else None,
            "model": nlp_result.get("model") if nlp_result else None,
        },
        "header_analysis": {
            "status": "evidence_only",
            "authentication": parsed_email.get("authentication", {}),
            "sender_domain_analysis": parsed_email.get("sender_domain_analysis", {}),
            "findings": header_findings,
            "risk_score": None,
        },
        "attachment_analysis": {
            "status": "evidence_only",
            "attachments": parsed_email.get("attachments", []),
            "findings": attachment_findings,
            "probability": None,
        },
        "explanation": explanation,
    }
