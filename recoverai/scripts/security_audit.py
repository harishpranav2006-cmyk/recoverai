"""
RecoverAI — Security & Secret Audit Scanner
===========================================
Scans source files for leaked API keys, tokens, hardcoded credentials, and unsafe shell/code execution patterns.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent

PATTERNS = [
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI Secret Key"),
    (r"rzp_live_[a-zA-Z0-9]{14,}", "Razorpay Live Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"(?i)password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded Password Assignment"),
    (r"(?i)eval\s*\(", "Unsafe eval() usage"),
    (r"(?i)exec\s*\(", "Unsafe exec() usage"),
]

EXCLUDE_DIRS = {".git", ".pytest_cache", "__pycache__", "venv", ".venv", "artifacts"}

def run_security_audit() -> bool:
    print("\n" + "=" * 80)
    print("  RECOVERAI — CODEBASE SECURITY & SECRET SCAN")
    print("=" * 80 + "\n")

    findings = []
    scanned_files = 0

    for ext in ["*.py", "*.md", "*.yaml", "*.yml", "*.env.example", ".gitignore"]:
        for file_path in ROOT.rglob(ext):
            if any(part in file_path.parts for part in EXCLUDE_DIRS):
                continue

            scanned_files += 1
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            for pattern, desc in PATTERNS:
                matches = re.finditer(pattern, content)
                for m in matches:
                    line_no = content[:m.start()].count("\n") + 1
                    # Exclude the scanner itself from self-flagging
                    if "security_audit.py" in str(file_path):
                        continue
                    findings.append((str(file_path.relative_to(ROOT)), line_no, desc, m.group(0)[:10] + "..."))

    print(f"[SCAN] Audited {scanned_files} files across Python, Markdown, YAML, and Env configs.")

    if findings:
        print(f"❌ FOUND {len(findings)} POTENTIAL SECURITY ISSUES:")
        for file_name, line_no, desc, snippet in findings:
            print(f"  • {file_name}:{line_no} — {desc} ({snippet})")
        return False
    else:
        print("✅ ZERO SECRETS, HARDCODED KEYS, OR UNSAFE EXECUTION DETECTED (100% CLEAN)")
        print("=" * 80 + "\n")
        return True

if __name__ == "__main__":
    success = run_security_audit()
    if not success:
        sys.exit(1)
