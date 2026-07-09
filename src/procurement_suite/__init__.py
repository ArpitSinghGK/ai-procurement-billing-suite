"""AI-driven procurement & billing automation suite.

End-to-end: capture an enquiry, understand it, source vendor quotes (plus live
online prices), identify L1, quote the customer with markup, raise POs, 3-way
match on receipt, and invoice — wired to the ERP.
"""
from .orchestrator import ProcurementOrchestrator

__all__ = ["ProcurementOrchestrator"]
__version__ = "0.1.0"
