"""Build and format a human-readable report for a secret import operation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from vaultpull.secret_import import ImportConfig, ImportResult


@dataclass
class ImportReport:
    environment: str
    source_file: str
    imported: int
    skipped: int
    errors: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def build_import_report(
    cfg: ImportConfig,
    result: ImportResult,
    environment: str = "default",
) -> ImportReport:
    """Construct an ImportReport from config and result."""
    return ImportReport(
        environment=environment,
        source_file=cfg.source_file,
        imported=result.total,
        skipped=len(result.skipped),
        errors=list(result.errors),
    )


def format_import_report(report: ImportReport) -> str:
    """Return a plain-text summary of the import report."""
    lines: List[str] = [
        f"Import Report [{report.environment}]",
        f"  Source : {report.source_file}",
        f"  Imported : {report.imported}",
        f"  Skipped  : {report.skipped}",
    ]
    if report.errors:
        lines.append(f"  Errors   : {len(report.errors)}")
        for err in report.errors:
            lines.append(f"    - {err}")
    else:
        lines.append("  Errors   : 0")
    return "\n".join(lines)
