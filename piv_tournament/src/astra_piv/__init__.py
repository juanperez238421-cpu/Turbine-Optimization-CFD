from __future__ import annotations

# This module is intentionally small: it exposes the package version and the evidence gate.
from .config import AstraConfig, load_config
from .scientific_gate import EvidenceState, publication_gate

__all__ = ["AstraConfig", "load_config", "EvidenceState", "publication_gate"]
__version__ = "0.2.0"
