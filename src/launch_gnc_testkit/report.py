from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    severity: Severity = Severity.ERROR
    location: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    subject: str
    findings: list[Finding] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(item.severity == Severity.ERROR for item in self.findings)

    def add(
        self,
        code: str,
        message: str,
        severity: Severity = Severity.ERROR,
        location: str | None = None,
        **details: Any,
    ) -> None:
        self.findings.append(Finding(code, message, severity, location, details))

    def extend(self, other: "Report") -> None:
        self.findings.extend(other.findings)
        self.summary.update(other.summary)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "ok": self.ok,
            "summary": self.summary,
            "findings": [asdict(item) for item in self.findings],
        }

    def to_markdown(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        lines = [f"# {self.subject}", "", f"**Status:** {status}", ""]
        if self.summary:
            lines.extend(["## Summary", ""])
            for key, value in sorted(self.summary.items()):
                lines.append(f"- **{key}:** `{value}`")
            lines.append("")
        lines.extend(["## Findings", ""])
        if not self.findings:
            lines.append("No findings.")
        for item in self.findings:
            location = f" (`{item.location}`)" if item.location else ""
            lines.append(
                f"- **{item.severity.value.upper()} `{item.code}`**{location}: "
                f"{item.message}"
            )
            if item.details:
                for key, value in sorted(item.details.items()):
                    lines.append(f"  - {key}: `{value}`")
        return "\n".join(lines) + "\n"
