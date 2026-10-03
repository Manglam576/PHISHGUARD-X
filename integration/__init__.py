"""PHISHGUARD-X integration services."""

from .orchestrator import analyze_email, analyze_email_bytes

__all__ = ["analyze_email", "analyze_email_bytes"]
