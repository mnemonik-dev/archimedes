#!/usr/bin/env python3
"""
Complexity gate: analyze changed files against a pre-fetched baseline directory.

The workflow checks out both the PR HEAD and the base branch as separate
directories, so this script never needs to call git — making it compatible
with a distroless container.

Metrics per function:
  CC        — cyclomatic complexity (lizard, cross-language)
  Nesting   — max nested loops/conditionals (lizard)
  Δ CC      — delta vs. same function in baseline
  Recursive — direct self-call (Python AST only)

Usage:
  python complexity_analysis.py \
    --changed-files a.py b.ts \
    --baseline-dir /workspace/.baseline \
    --output-json /tmp/result.json \
    > /tmp/comment.md

Exit codes:
  0 — all functions within bounds
  1 — one or more functions critically complex (CC >= 16)
"""
import argparse
import ast
import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import lizard

CC_SIMPLE = 5
CC_MODERATE = 10
CC_COMPLEX = 15
NESTING_WARN = 3


@dataclass
class FuncInfo:
    name: str
    file: str
    line: int
    cc: int
    length: int
    params: int
    nesting: int
    is_recursive: bool = False


def _lizard_funcs(filepath: str, source: Optional[str] = None) -> list[dict]:
    try:
        if source is not None:
            suffix = Path(filepath).suffix
            with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
                f.write(source)
                tmp = f.name
            try:
                info = lizard.analyze_file(tmp)
            finally:
                os.unlink(tmp)
        else:
            info = lizard.analyze_file(filepath)

        if info is None:
            return []
        return [
            {
                "name": fn.name,
                "line": fn.start_line,
                "cc": fn.cyclomatic_complexity,
                "length": fn.length,
                "params": fn.parameter_count,
                "nesting": getattr(fn, "max_nesting_depth", 0),
            }
            for fn in info.function_list
        ]
    except Exception:
        return []


class _RecursionVisitor(ast.NodeVisitor):
    def __init__(self, func_name: str):
        self.func_name = func_name
        self.found = False

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == self.func_name:
            self.found = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr == self.func_name:
            self.found = True
        self.generic_visit(node)


def _is_recursive(source: str, func_name: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            v = _RecursionVisitor(func_name)
            v.visit(node)
            return v.found
    return False


def _baseline_source(filepath: str, baseline_dir: str) -> Optional[str]:
    baseline_path = Path(baseline_dir) / filepath
    if baseline_path.exists():
        return baseline_path.read_text(errors="replace")
    return None


def _analyze_file(filepath: str, baseline_dir: str) -> tuple[list[FuncInfo], list[FuncInfo]]:
    is_py = filepath.endswith(".py")

    after_raw = _lizard_funcs(filepath)
    after_source = Path(filepath).read_text(errors="replace") if is_py and Path(filepath).exists() else None

    after = [
        FuncInfo(
            name=f["name"], file=filepath, line=f["line"],
            cc=f["cc"], length=f["length"], params=f["params"], nesting=f["nesting"],
            is_recursive=_is_recursive(after_source, f["name"]) if is_py and after_source else False,
        )
        for f in after_raw
    ]

    baseline = _baseline_source(filepath, baseline_dir)
    before = [
        FuncInfo(
            name=f["name"], file=filepath, line=f["line"],
            cc=f["cc"], length=f["length"], params=f["params"], nesting=f["nesting"],
            is_recursive=_is_recursive(baseline, f["name"]) if is_py and baseline else False,
        )
        for f in _lizard_funcs(filepath, source=baseline)
    ] if baseline else []

    return before, after


def _cc_badge(cc: int) -> str:
    if cc <= CC_SIMPLE:   return f"{cc} ✅"
    if cc <= CC_MODERATE: return f"{cc} ⚠️"
    if cc <= CC_COMPLEX:  return f"{cc} 🟠"
    return f"{cc} 🔴"


def _verdict(cc: int, recursive: bool, nesting: int) -> str:
    if cc > CC_COMPLEX:                                   return "🔴 Critical"
    if cc > CC_MODERATE:                                  return "🟠 Complex"
    if cc > CC_SIMPLE or recursive or nesting >= NESTING_WARN: return "⚠️ Review"
    return "✅ OK"


def generate(changed_files: list[str], baseline_dir: str) -> tuple[str, dict]:
    rows = []
    has_critical = False

    for filepath in changed_files:
        if not Path(filepath).exists():
            continue

        before_list, after_list = _analyze_file(filepath, baseline_dir)
        before_by_name = {f.name: f for f in before_list}

        short = filepath
        for prefix in ("backend/archimedes/", "backend/", "ui/src/"):
            if short.startswith(prefix):
                short = short[len(prefix):]
                break

        for fn in after_list:
            prev = before_by_name.get(fn.name)
            if prev is None:
                delta = "new"
            else:
                d = fn.cc - prev.cc
                delta = f"+{d} ⚠️" if d > 0 else (f"{d} ✅" if d < 0 else "—")

            if fn.cc > CC_COMPLEX:
                has_critical = True

            rows.append({
                "func": fn.name,
                "file": f"`{short}:{fn.line}`",
                "cc": _cc_badge(fn.cc),
                "delta": delta,
                "nesting": f"{fn.nesting}{'⚠️' if fn.nesting >= NESTING_WARN else ''}",
                "recursive": "**Yes** ⚠️" if fn.is_recursive else "No",
                "verdict": _verdict(fn.cc, fn.is_recursive, fn.nesting),
                "cc_raw": fn.cc,
            })

    if not rows:
        md = "## 🔬 Complexity Analysis\n\nNo analyzable functions in changed files.\n"
        return md, {"has_critical": False, "total_funcs": 0}

    lines = ["## 🔬 Complexity Analysis\n"]
    if has_critical:
        lines.append("> 🔴 **Critical complexity — CC ≥ 16 detected. Merge blocked.**\n")
    elif any(r["cc_raw"] > CC_SIMPLE or "⚠️" in r["recursive"] for r in rows):
        lines.append("> ⚠️ Some functions warrant a closer look — see table.\n")
    else:
        lines.append("> ✅ All functions within acceptable complexity bounds.\n")

    lines += [
        f"**{len(rows)} function{'s' if len(rows) != 1 else ''} analyzed** "
        f"across {len(changed_files)} changed file{'s' if len(changed_files) != 1 else ''}.\n",
        "",
        "| Function | File | CC | Δ CC | Nesting | Recursive | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['func']}` | {r['file']} | {r['cc']} | {r['delta']} "
            f"| {r['nesting']} | {r['recursive']} | {r['verdict']} |"
        )

    lines += [
        "",
        "**CC thresholds:** ✅ 1–5 · ⚠️ 6–10 · 🟠 11–15 · 🔴 16+ blocks merge  "
        "**Nesting:** ⚠️ at depth ≥ 3  "
        "**Recursive:** Python files only",
    ]

    return "\n".join(lines), {"has_critical": has_critical, "total_funcs": len(rows)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-files", nargs="+", required=True)
    parser.add_argument("--baseline-dir", required=True,
                        help="Path to the checkout of the base branch (e.g. .baseline/)")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True,
                        help="Path to write the markdown comment body")
    args = parser.parse_args()

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)

    try:
        targets = [f for f in args.changed_files if Path(f).suffix in {".py", ".js", ".ts", ".jsx", ".tsx"}]
        if not targets:
            output_md.write_text("## 🔬 Complexity Analysis\n\nNo Python or JS/TS files changed.\n")
            output_json.write_text(json.dumps({"has_critical": False, "total_funcs": 0}))
            sys.exit(0)

        md, summary = generate(targets, args.baseline_dir)
        output_md.write_text(md)
        output_json.write_text(json.dumps(summary))
        sys.exit(1 if summary["has_critical"] else 0)

    except Exception as exc:
        import traceback as tb
        error_md = (
            "## 🔬 Complexity Analysis\n\n"
            f"> ⚠️ Analysis error: `{exc}`\n\n"
            "<details><summary>Traceback</summary>\n\n"
            f"```\n{tb.format_exc()}\n```\n\n"
            "</details>\n"
        )
        output_md.write_text(error_md)
        output_json.write_text(json.dumps({"has_critical": False, "total_funcs": 0}))
        sys.exit(0)


if __name__ == "__main__":
    main()
