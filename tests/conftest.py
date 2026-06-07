"""pytest configuration — business test case report generation."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest


REPORT_DIR = Path("docs/test_reports")
BUSINESS_CATEGORIES = {
    "fundamental": "Fundamental Analysis",
    "valuation": "Valuation & DCF",
    "risk": "Risk Detection",
    "broker": "Broker & Order Execution",
    "portfolio": "Portfolio Construction",
    "validator": "Input Validation",
    "moat": "Moat & Business Quality",
    "news": "News & Sentiment",
    "orchestrator": "Research Orchestration",
    "audit": "Audit & Prompt Versioning",
    "data": "Data Collection",
    "api": "API Endpoints",
    "coverage": "Coverage Gap Tests",
}


def _category(nodeid: str) -> str:
    lower = nodeid.lower()
    for key, label in BUSINESS_CATEGORIES.items():
        if key in lower:
            return label
    return "General"


def pytest_configure(config):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


class BusinessTestReport:
    def __init__(self):
        self.results: list[dict[str, Any]] = []
        self.start_time = datetime.utcnow()

    def record(self, report):
        if report.when != "call":
            return
        self.results.append({
            "test_id": report.nodeid,
            "category": _category(report.nodeid),
            "status": "PASSED" if report.passed else ("FAILED" if report.failed else "SKIPPED"),
            "duration_ms": round(report.duration * 1000, 1),
            "error": str(report.longrepr).split("\n")[-1] if report.failed else None,
        })

    def write(self):
        ts = self.start_time.strftime("%Y-%m-%d_%H-%M")
        passed = [r for r in self.results if r["status"] == "PASSED"]
        failed = [r for r in self.results if r["status"] == "FAILED"]
        skipped = [r for r in self.results if r["status"] == "SKIPPED"]

        # Group by category
        by_category: dict[str, list] = {}
        for r in self.results:
            by_category.setdefault(r["category"], []).append(r)

        # Write Markdown report
        md_path = REPORT_DIR / f"business_test_report_{ts}.md"
        lines = [
            "# Business Test Case Report",
            f"**Generated:** {self.start_time.strftime('%Y-%m-%d %H:%M UTC')}  ",
            f"**Total:** {len(self.results)} | "
            f"**✅ Passed:** {len(passed)} | "
            f"**❌ Failed:** {len(failed)} | "
            f"**⏭ Skipped:** {len(skipped)}",
            "",
            "> This is educational research software. "
            "All tests validate research and safety logic — not financial advice.",
            "",
        ]

        for category, tests in sorted(by_category.items()):
            cat_pass = sum(1 for t in tests if t["status"] == "PASSED")
            cat_fail = sum(1 for t in tests if t["status"] == "FAILED")
            status_icon = "✅" if cat_fail == 0 else "❌"
            lines.append(f"## {status_icon} {category} ({cat_pass}/{len(tests)} passed)")
            lines.append("")
            lines.append("| # | Test Case | Status | Duration |")
            lines.append("|---|-----------|--------|----------|")
            for i, t in enumerate(tests, 1):
                icon = "✅" if t["status"] == "PASSED" else ("❌" if t["status"] == "FAILED" else "⏭")
                name = t["test_id"].split("::")[-1].replace("_", " ").strip()
                err = f" — `{t['error']}`" if t["error"] else ""
                lines.append(f"| {i} | {name}{err} | {icon} {t['status']} | {t['duration_ms']}ms |")
            lines.append("")

        if failed:
            lines.append("## ❌ Failed Tests — Detail")
            lines.append("")
            for t in failed:
                lines.append(f"### {t['test_id']}")
                lines.append(f"```\n{t['error']}\n```")
                lines.append("")

        md_path.write_text("\n".join(lines))

        # Write JSON report
        json_path = REPORT_DIR / f"business_test_report_{ts}.json"
        json_path.write_text(json.dumps({
            "generated_at": self.start_time.isoformat(),
            "summary": {"total": len(self.results), "passed": len(passed),
                        "failed": len(failed), "skipped": len(skipped)},
            "by_category": {k: [{"test": t["test_id"], "status": t["status"],
                                  "duration_ms": t["duration_ms"], "error": t["error"]}
                                 for t in v]
                            for k, v in by_category.items()},
            "all_results": self.results,
        }, indent=2))

        # Always write a latest symlink-style copy
        (REPORT_DIR / "latest.md").write_text(md_path.read_text())
        (REPORT_DIR / "latest.json").write_text(json_path.read_text())

        print(f"\n📊 Business Test Report → {md_path}")
        return md_path, json_path


_report = BusinessTestReport()


def pytest_runtest_logreport(report):
    _report.record(report)


def pytest_sessionfinish(session, exitstatus):
    if _report.results:
        _report.write()
