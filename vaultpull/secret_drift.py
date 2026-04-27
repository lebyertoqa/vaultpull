"""Detect drift between Vault secrets and the local .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DriftRecord:
    key: str
    vault_value: Optional[str]
    local_value: Optional[str]
    status: str  # 'added' | 'removed' | 'changed' | 'ok'


@dataclass
class DriftReport:
    environment: str
    records: List[DriftRecord] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def drifted(self) -> List[DriftRecord]:
        return [r for r in self.records if r.status != "ok"]

    @property
    def has_drift(self) -> bool:
        return bool(self.drifted)


def _parse_env_file(path: str) -> Dict[str, str]:
    """Parse a .env file into a key/value mapping, ignoring comments."""
    result: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return result


def compute_drift(
    vault_secrets: Dict[str, str],
    env_path: str,
    environment: str = "default",
) -> DriftReport:
    """Compare Vault secrets against a local .env file and return a DriftReport."""
    local = _parse_env_file(env_path)
    all_keys = set(vault_secrets) | set(local)
    records: List[DriftRecord] = []

    for key in sorted(all_keys):
        v_val = vault_secrets.get(key)
        l_val = local.get(key)

        if v_val is not None and l_val is None:
            status = "added"
        elif v_val is None and l_val is not None:
            status = "removed"
        elif v_val != l_val:
            status = "changed"
        else:
            status = "ok"

        records.append(DriftRecord(key=key, vault_value=v_val, local_value=l_val, status=status))

    return DriftReport(environment=environment, records=records)


def format_drift_report(report: DriftReport) -> str:
    """Return a human-readable summary of the drift report."""
    lines = [f"Drift report [{report.environment}]"]
    if not report.has_drift:
        lines.append("  No drift detected.")
        return "\n".join(lines)

    for rec in report.drifted:
        lines.append(f"  [{rec.status.upper():^8}] {rec.key}")
    lines.append(f"  {len(report.drifted)} drifted / {report.total} total keys")
    return "\n".join(lines)
