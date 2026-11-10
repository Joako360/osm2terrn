#!/usr/bin/env python3
"""Static inventory generator and validator for the OSM2Terrn technical book.

The tool only reads repository files and writes documentation artifacts under
``docs/book/``. It never imports or executes OSM2Terrn code, never reads
ignored/sensitive files (for example ``.env``) and uses only the standard
library. Results are static (AST based) and deterministic for a given tree.

Commands:
    generate   Regenerate the inventory artifacts in ``docs/book/inventory/``.
    validate   Validate artifacts against ``schema.json``, check cross-record
               integrity, run negative self-tests and compare a regeneration
               with the files on disk. ``--write-report`` renders
               ``docs/book/progress/inventory_report.md``.
"""

from __future__ import annotations

import argparse
import ast
import builtins
from datetime import datetime
import hashlib
import json
import logging
import re
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

GENERATOR_VERSION = "2.0.1"
REPO_ROOT = Path(__file__).resolve().parents[3]
INVENTORY_DIR = REPO_ROOT / "docs" / "book" / "inventory"
SCHEMA_PATH = INVENTORY_DIR / "schema.json"
TOOL_PATH = "docs/book/inventory/inventory_tool.py"
REPORT_MD_PATH = "docs/book/progress/inventory_report.md"
REPORT_JSON_PATH = "docs/book/inventory/generation_report.json"
STREAMS = {
    "files": "docs/book/inventory/files.jsonl",
    "symbols": "docs/book/inventory/symbols.jsonl",
    "relations": "docs/book/inventory/relations.jsonl",
    "xrefs": "docs/book/inventory/docs_cross_reference.jsonl",
    "flow": "docs/book/inventory/control_flow.jsonl",
    "claims": "docs/book/inventory/claims.jsonl",
    "unresolved": "docs/book/inventory/unresolved.jsonl",
    "entries": "docs/book/inventory/entry_points.jsonl",
    "deps": "docs/book/inventory/external_dependencies.jsonl",
}
GENERATED_PATHS = sorted([*STREAMS.values(), REPORT_JSON_PATH, REPORT_MD_PATH])
OWN_CODE_ROOTS = {"osm2terrn", "tests", "scripts"}
CLASS_KINDS = {"class", "enum"}
ENUM_BASES = {"Enum", "IntEnum", "StrEnum", "Flag", "IntFlag"}
DYNAMIC_NAMES = {"getattr", "setattr", "delattr", "__import__", "eval", "exec", "globals", "locals", "vars", "compile"}
DYNAMIC_ATTRS = {
    "importlib.import_module",
    "importlib.reload",
    "importlib.util.spec_from_file_location",
    "importlib.util.module_from_spec",
    "sys.path.append",
    "sys.path.insert",
}
TEST_STRING_RE = re.compile(r"^osm2terrn(\.[A-Za-z_]\w*)+$")
IMPORT_NAME_ALIASES = {"PIL": "pillow", "dotenv": "python-dotenv"}
LITERAL_NODES = (ast.Constant, ast.JoinedStr, ast.List, ast.Dict, ast.Set, ast.Tuple, ast.ListComp, ast.DictComp, ast.SetComp)
TRY_NODES = tuple(t for t in (ast.Try, getattr(ast, "TryStar", None), ast.ExceptHandler, ast.If, ast.IfExp) if t)

REASONS = {
    "callee_is_variable": "Callee is a variable or parameter; its value is not tracked.",
    "receiver_is_variable": "Receiver is a local/module-level variable or parameter; its type is not inferred.",
    "instance_attribute_receiver": "Receiver is an attribute of self/cls; the attribute type is not inferred.",
    "receiver_is_expression": "Receiver is a computed expression (call result, subscript, ...); its type is not inferred.",
    "callee_is_expression": "Callee is a computed expression.",
    "name_not_found": "Name is not bound in any statically visible scope (star import, injected global or undefined).",
    "attribute_not_found_on_class": "Method not found on the class or its statically resolvable own bases (may be inherited from an external base, assigned dynamically or be an instance attribute).",
    "imported_name_not_found": "Name imported from an own module is neither defined nor re-exported statically there.",
    "module_attribute_not_found": "Attribute is not defined statically in the own module.",
    "module_called": "A module object is called or no attribute remains after module resolution.",
    "receiver_is_function_object": "Attribute call on a function object.",
    "super_target_unresolved": "super() target not found in statically resolvable own base classes.",
    "nested_attribute": "Attribute path through a class is deeper than one level.",
    "own_import_not_found": "Import targets an own top-level package but no matching module exists.",
    "relative_import_beyond_top": "Relative import goes beyond the top-level package.",
    "namespace_package_import": "Import targets an own directory without __init__.py.",
    "external_base_class": "Base class is external (stdlib or third party).",
    "unresolved_base_class": "Base class expression could not be resolved statically.",
    "dynamic_construct": "Dynamic attribute access, import, execution or sys.path mutation; static analysis cannot follow it.",
    "parse_failure": "File could not be parsed as Python.",
}
CATEGORY = {
    "external_base_class": "inheritance",
    "unresolved_base_class": "inheritance",
    "own_import_not_found": "import",
    "relative_import_beyond_top": "import",
    "namespace_package_import": "import",
    "imported_name_not_found": "import",
    "dynamic_construct": "dynamic",
    "parse_failure": "analysis",
}
LIMITATIONS = [
    "Analysis is static (AST); no code, test or pipeline was executed, so no record shows that anything runs.",
    "Receiver types are not inferred: calls on variables, parameters, attributes of self and call results are reported as unresolved.",
    "self/cls method resolution assumes the enclosing class; subclass overrides and dynamic attributes are not considered.",
    "Class instantiation is linked to the class symbol, not to __init__.",
    "Decorator effects, metaclasses, star imports, plugin loading and environment-dependent branches are not modelled.",
    "Module-level variables and constants are not inventoried as symbols.",
    "Callable references that are not called (callbacks, getattr targets, string-based references outside tests) are not captured.",
    "Calls made inside lambdas and comprehensions are attributed to the enclosing symbol.",
    "Non-Python files (documentation, YAML, notebooks, batch files) are classified by path and extension only.",
    "Third-party distribution matching uses normalized names plus a small alias table, not installed metadata.",
    "docs_cross_reference.jsonl is intentionally empty: documentation cross-referencing is a later stage.",
    "control_flow.jsonl and claims.jsonl are contracts for later reviewed documentation; the generator does not populate them.",
    "No control-flow graph is generated; syntactic branches and exception handlers are not proof of reachability or execution.",
]

LOG = logging.getLogger("inventory_tool")
Binding = tuple


@dataclass(frozen=True)
class PathEntry:
    """A repository path considered by the inventory."""

    path: str
    git_state: str
    excluded: bool
    reason: str | None = None
    kind: str | None = None
    is_dir: bool = False
    note: str | None = None


@dataclass
class Scope:
    """A lexical scope used while resolving names."""

    kind: str
    table: dict[str, Binding]


@dataclass(frozen=True)
class State:
    """Walker state: visible scopes, owning symbol and enclosing class."""

    scopes: tuple[Scope, ...]
    owner: str
    method_class: str | None = None
    cond: bool = False


@dataclass
class Resolution:
    """Outcome of resolving a callee expression."""

    status: str
    target: str | None = None
    resolution: str = "static"
    top: str | None = None
    code: str | None = None


@dataclass
class ModuleInfo:
    """Parsed Python module."""

    path: str
    name: str
    is_init: bool
    is_test: bool
    file_id: str
    module_id: str
    tree: ast.Module | None = None
    line_count: int = 1
    table: dict[str, Binding] = field(default_factory=dict)
    top_defs: dict[str, str] = field(default_factory=dict)
    node_symbols: dict[int, str] = field(default_factory=dict)
    star_imports: list[str] = field(default_factory=list)
    guards: list[tuple[int, int]] = field(default_factory=list)
    error: str | None = None


@dataclass
class Outputs:
    """Static inventory outputs and preserved authored claim records."""

    files: list[dict]
    symbols: list[dict]
    relations: list[dict]
    unresolved: list[dict]
    entries: list[dict]
    deps: list[dict]
    report: dict
    claims: list[dict] = field(default_factory=list)


# ----------------------------------------------------------------- git helpers


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, check=True).stdout


def _split_z(raw: bytes) -> list[str]:
    return [part.decode("utf-8") for part in raw.split(b"\0") if part]


def git_revision() -> str:
    """Return the HEAD commit hash or ``unknown``."""
    try:
        return _git("rev-parse", "HEAD").decode("utf-8").strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _modified_paths() -> set[str]:
    entries = _split_z(_git("status", "--porcelain", "-z", "--untracked-files=no"))
    modified: set[str] = set()
    index = 0
    while index < len(entries):
        entry = entries[index]
        status, path = entry[:2], entry[3:]
        if status[0] in "RC":
            index += 1
        if status.strip():
            modified.add(path)
        index += 1
    return modified


def _exclusion(path: str) -> tuple[str, str]:
    name = path.rsplit("/", 1)[-1]
    parts = path.rstrip("/").split("/")
    if ".env" in parts:
        return "Local environment file; contents are never read because it may hold secrets.", "configuration"
    if "__pycache__" in parts or name.endswith(".pyc"):
        return "Interpreter bytecode cache.", "other"
    if any(part in {".venv", "venv", "env"} for part in parts):
        return "Virtual environment (third-party packages).", "other"
    if any(part.endswith(".egg-info") for part in parts):
        return "Local packaging metadata.", "other"
    if any(part in {".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in parts):
        return "Tool cache.", "other"
    is_osm2terrn_cache_source = (
        len(parts) >= 2
        and parts[:2] == ["osm2terrn", "cache"]
        and not any(part in {"cache", ".cache"} for part in parts[2:])
    )
    has_nested_cache = any(part in {"cache", ".cache"} for part in parts[1:])
    if not is_osm2terrn_cache_source and (parts[0] in {"cache", ".cache"} or has_nested_cache):
        return "Local runtime cache data.", "data"
    if "output" in parts:
        return "Generated terrain output.", "data"
    if "logs" in parts:
        return "Runtime logs.", "data"
    if any(part in {".docs", ".examples"} for part in parts):
        return "Ignored local content of unconfirmed provenance (see question:local-example-data).", "data"
    return "Ignored by .gitignore; category not classified.", "other"


def collect_paths() -> tuple[list[PathEntry], list[str]]:
    """Collect repository paths with Git state, exclusions and missing files."""
    tracked = set(_split_z(_git("ls-files", "-z")))
    untracked = set(_split_z(_git("ls-files", "-z", "--others", "--exclude-standard")))
    ignored = _split_z(_git("ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory"))
    modified = _modified_paths()
    entries: dict[str, PathEntry] = {}
    missing: list[str] = []
    for path in sorted(tracked | untracked | set(GENERATED_PATHS)):
        if path not in GENERATED_PATHS and not (REPO_ROOT / path).is_file():
            missing.append(path)
            continue
        state = "modified" if path in modified else "tracked" if path in tracked else "untracked"
        entries[path] = PathEntry(path, state, False)
    for raw in ignored:
        path = raw.rstrip("/")
        is_dir = raw.endswith("/")
        top = path.split("/", 1)[0]
        name = path.rsplit("/", 1)[-1]
        if is_dir and top in OWN_CODE_ROOTS and name != "__pycache__":
            reason, kind = _exclusion(path)
            if reason != "Ignored by .gitignore; category not classified.":
                entries[path] = PathEntry(path, "ignored", True, reason, kind, True)
                continue
            # Ignored directory inside own code roots: enumerate files, they are analyzed as source.
            for child in _split_z(_git("ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--", path)):
                child_parts = child.split("/")
                excluded_component = next((part for part in child_parts if part in {".env", "__pycache__", ".venv", "venv", "env", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache", ".docs", ".examples", "output", "logs"}), None)
                is_osm2terrn_cache_source = (
                    child.startswith("osm2terrn/cache/")
                    and not any(part in {"cache", ".cache"} for part in child_parts[2:])
                )
                if child.endswith(".pyc") or excluded_component is not None or ("cache" in child_parts[1:] and not is_osm2terrn_cache_source):
                    if excluded_component is not None:
                        index = child_parts.index(excluded_component)
                        excluded_path = "/".join(child_parts[: index + 1])
                    elif child.endswith(".pyc"):
                        index = child_parts.index("__pycache__") if "__pycache__" in child_parts else len(child_parts) - 1
                        excluded_path = "/".join(child_parts[: index + 1])
                    else:
                        index = next(i for i, part in enumerate(child_parts[1:], 1) if part in {"cache", ".cache"})
                        if child_parts[:2] == ["osm2terrn", "cache"] and index == 1:
                            index = next(i for i, part in enumerate(child_parts[2:], 2) if part in {"cache", ".cache"})
                        excluded_path = "/".join(child_parts[: index + 1])
                    reason, kind = _exclusion(excluded_path)
                    entries[excluded_path] = PathEntry(excluded_path, "ignored", True, reason, kind, True)
                    continue
                entries[child] = PathEntry(
                    child, "ignored", False,
                    note="Ignored by .gitignore but located in an owned code root and inventoried as source.",
                )
            continue
        if not is_dir and top in OWN_CODE_ROOTS and path.endswith(".py"):
            reason, kind = _exclusion(path)
            if reason == "Ignored by .gitignore; category not classified.":
                entries[path] = PathEntry(
                    path, "ignored", False,
                    note="Ignored by .gitignore but located in an owned code root and inventoried as Python source.",
                )
                continue
        reason, kind = _exclusion(path)
        entries[path] = PathEntry(path, "ignored", True, reason, kind, is_dir)
    return [entries[key] for key in sorted(entries)], missing


# ------------------------------------------------------------- classification


def classify(path: str) -> tuple[str, str, str]:
    """Return ``(kind, rule, evidence_type)`` for a repository path."""
    name = path.rsplit("/", 1)[-1]
    parts = path.split("/")
    suffix = Path(path).suffix.lower()
    if path.startswith(".github/workflows/"):
        return "ci_configuration", "path under .github/workflows", "configuration"
    if suffix == ".py":
        if parts[0] == "tests":
            return "python_test", "Python file under tests/", "test_source"
        if parts[0] == "osm2terrn":
            return "python_source", "Python file under osm2terrn/", "source"
        return "script", "Python file outside the package and tests", "source"
    if suffix == ".md":
        return "documentation", "Markdown file", "documentation"
    if suffix == ".ipynb":
        return "notebook", "Jupyter notebook", "source"
    if name in {"pyproject.toml", "uv.lock"}:
        return "build_metadata", "packaging/lock file name", "configuration"
    if suffix == ".jsonl":
        return "data", "JSON Lines data file", "source"
    if suffix in {".yaml", ".yml", ".json", ".toml", ".ini", ".cfg"} or name in {".gitignore", ".env.example"} or parts[0] == ".vscode":
        return "configuration", "configuration-like file name or extension", "configuration"
    if suffix in {".bat", ".cmd", ".ps1", ".sh"}:
        return "script", "shell/batch script extension", "source"
    if name.upper().startswith("LICEN"):
        return "documentation", "license file name", "documentation"
    return "other", "no classification rule matched", "source"


# --------------------------------------------------------------------- helpers


def _ev(path: str, start: int | None, end: int | None, etype: str, desc: str) -> dict:
    evidence_key = f"{path}|{start}|{end}|{etype}|{desc}"
    item: dict[str, Any] = {"evidence_id": "ev:" + _hash(evidence_key), "path": path}
    if start:
        item["start_line"] = start
    if end:
        item["end_line"] = end
    item["type"] = etype
    item["description"] = desc
    return item


def _short(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _rel_id(kind: str, source: str, target: str, resolution: str) -> str:
    return "rel:" + _hash(f"{kind}|{source}|{target}|{resolution}")


def _line_count_bytes(data: bytes) -> int:
    """Count physical lines, treating CRLF as one terminator and empty as zero."""
    if not data:
        return 0
    terminators = len(re.findall(rb"\r\n|\r|\n", data))
    ends_with_terminator = data.endswith((b"\r", b"\n"))
    return terminators + (0 if ends_with_terminator else 1)


def _is_git_commit_revision(revision: str) -> bool:
    """Return whether a full revision identifies a commit in this repository."""
    if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", revision) is None:
        return False
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _child_blocks(stmt: ast.AST) -> Iterator[list]:
    for name in ("body", "orelse", "finalbody"):
        value = getattr(stmt, name, None)
        if isinstance(value, list) and value and isinstance(value[0], ast.stmt):
            yield value
    for handler in getattr(stmt, "handlers", None) or []:
        yield handler.body
    for case in getattr(stmt, "cases", None) or []:
        yield case.body


def _scope_nodes(nodes: Iterable[ast.AST]) -> Iterator[ast.AST]:
    """Yield nodes of one scope without descending into nested definitions."""
    for node in nodes:
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield from _scope_nodes(ast.iter_child_nodes(node))


def _dotted_text(node: ast.AST) -> str:
    target = node.func if isinstance(node, ast.Call) else node
    return ast.unparse(target)


def _norm_dist(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _is_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    test = node.test
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    operands = [test.left, *test.comparators]
    names = [o.id for o in operands if isinstance(o, ast.Name)]
    consts = [o.value for o in operands if isinstance(o, ast.Constant)]
    return names == ["__name__"] and consts == ["__main__"]


# ------------------------------------------------------------------- inventory


class Inventory:
    """Builds file, symbol, relation and supplementary records."""

    def __init__(self) -> None:
        self.entries, self.missing = collect_paths()
        self.entry_by_path = {entry.path: entry for entry in self.entries}
        self.modules: dict[str, ModuleInfo] = {}
        self.modules_by_path: dict[str, ModuleInfo] = {}
        self.own_prefixes: set[str] = set()
        self.own_tops: set[str] = set()
        self.symbols: dict[str, dict] = {}
        self.qcount: dict[tuple[str, str], int] = {}
        self.class_methods: dict[str, dict[str, str]] = {}
        self.class_bases_expr: dict[str, list[ast.expr]] = {}
        self.class_module: dict[str, ModuleInfo] = {}
        self.class_bases: dict[str, list[str]] = {}
        self.relations: dict[str, dict] = {}
        self.unresolved: list[dict] = []
        self.ext_imports: dict[str, list[tuple[str, int, int | None, str, str]]] = defaultdict(list)
        self.ext_calls: Counter[str] = Counter()
        self.ext_call_paths: dict[str, set[str]] = defaultdict(set)
        self.internal_calls: list[tuple[str, str, str, int]] = []
        self.counts: Counter[str] = Counter()
        self.file_bytes: dict[str, bytes] = {}
        self.pyproject: dict = {}

    # ---------------------------------------------------------------- loading

    def run(self) -> None:
        """Run all passes."""
        for entry in self.entries:
            if entry.path.endswith(".py") and not entry.excluded:
                self._load_python(entry)
        for mod in self.modules.values():
            self.own_tops.add(mod.name.split(".")[0])
            parts = mod.name.split(".")
            for index in range(1, len(parts)):
                self.own_prefixes.add(".".join(parts[:index]))
        ordered = sorted(self.modules_by_path)
        for path in ordered:
            mod = self.modules_by_path[path]
            if mod.tree is not None:
                self._collect(mod, mod.tree.body, mod.module_id, "", None)
        for path in ordered:
            mod = self.modules_by_path[path]
            if mod.tree is not None:
                self._build_module_table(mod)
        for cid in sorted(self.class_bases_expr):
            self._resolve_bases(cid)
        for path in ordered:
            mod = self.modules_by_path[path]
            if mod.tree is not None:
                state = State((Scope("module", mod.table),), mod.module_id)
                for stmt in mod.tree.body:
                    self._visit(mod, stmt, state)
        self._add_contains()
        pyproject_path = REPO_ROOT / "pyproject.toml"
        if pyproject_path.is_file():
            self.pyproject = tomllib.loads(pyproject_path.read_bytes().decode("utf-8"))

    def _load_python(self, entry: PathEntry) -> None:
        path = entry.path
        parts = path[:-3].split("/")
        is_init = parts[-1] == "__init__"
        if is_init:
            parts = parts[:-1]
        name = ".".join(parts)
        kind, _, _ = classify(path)
        mod = ModuleInfo(path, name, is_init, kind == "python_test", f"file:{path}", f"py:{path}::<module>")
        self.modules_by_path[path] = mod
        data = (REPO_ROOT / path).read_bytes()
        self.file_bytes[path] = data
        mod.line_count = _line_count_bytes(data)
        try:
            mod.tree = ast.parse(data, filename=path)
        except (SyntaxError, ValueError, RecursionError, MemoryError) as exc:
            mod.error = f"{type(exc).__name__}: {exc}"
            self.unresolved.append(self._unresolved_record("analysis", "parse_failure", None, path, 1, None, path, mod.error, "source", f"File {path} could not be parsed: {mod.error}"))
            return
        self.modules[name] = mod
        self.symbols[mod.module_id] = {
            "symbol_id": mod.module_id, "file_id": mod.file_id, "path": path, "qualified_name": "<module>",
            "kind": "module", "owner_symbol_id": None,
            "start_line": 1 if mod.line_count else None,
            "end_line": mod.line_count if mod.line_count else None,
            "analysis_status": "inventory_generated",
            "evidence": [_ev(path, 1, mod.line_count, "test_source" if mod.is_test else "source", "Module extracted from AST")] if mod.line_count else [_ev(path, None, None, "test_source" if mod.is_test else "source", "Empty module file parsed")],
            "uncertainties": [], "limitations": [],
        }
        mod.guards = [(n.lineno, n.end_lineno or n.lineno) for n in mod.tree.body if _is_main_guard(n)]

    # ---------------------------------------------------------------- pass A

    def _etype(self, mod: ModuleInfo) -> str:
        return "test_source" if mod.is_test else "source"

    def _collect(self, mod: ModuleInfo, stmts: list, owner: str, qprefix: str, class_id: str | None) -> None:
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self._define(mod, stmt, owner, qprefix, class_id)
            else:
                for block in _child_blocks(stmt):
                    self._collect(mod, block, owner, qprefix, class_id)

    def _define(self, mod: ModuleInfo, node: ast.AST, owner: str, qprefix: str, class_id: str | None) -> None:
        is_class = isinstance(node, ast.ClassDef)
        base_q = f"{qprefix}.{node.name}" if qprefix else node.name
        key = (mod.path, base_q)
        self.qcount[key] = self.qcount.get(key, 0) + 1
        ordinal = self.qcount[key]
        qname = base_q if ordinal == 1 else f"{base_q}#{ordinal}"
        sid = f"py:{mod.path}::{qname}"
        decorators = [_dotted_text(d) for d in node.decorator_list]
        etype = self._etype(mod)
        if is_class:
            bases = [ast.unparse(b) for b in node.bases]
            kind = "enum" if any(b.split(".")[-1] in ENUM_BASES for b in bases) else "class"
            args = ", ".join(bases + [ast.unparse(k) for k in node.keywords])
            signature = f"{node.name}({args})" if args else node.name
        else:
            if class_id:
                is_prop = any(d == "property" or d.endswith((".setter", ".getter", ".deleter")) or d.endswith("cached_property") for d in decorators)
                kind = "property" if is_prop else "method"
            else:
                kind = "function"
            prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
            returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
            signature = f"{prefix}{node.name}({ast.unparse(node.args)}){returns}"
        evidence = [_ev(mod.path, node.lineno, node.end_lineno, etype, "Definition extracted from AST")]
        for deco in node.decorator_list:
            evidence.append(_ev(mod.path, deco.lineno, deco.end_lineno, etype, "decorator: " + _short(ast.unparse(deco), 200)))
        if is_class:
            for base in node.bases:
                evidence.append(_ev(mod.path, base.lineno, base.end_lineno, etype, "base class expression: " + _short(ast.unparse(base), 200)))
        if class_id and not is_class and node.name.startswith("__") and node.name.endswith("__"):
            evidence.append(_ev(mod.path, node.lineno, node.lineno, etype, "special (dunder) method"))
        uncertainties = [] if ordinal == 1 else [f"Duplicate qualified name in this file; ordinal suffix '#{ordinal}' added by the generator."]
        self.symbols[sid] = {
            "symbol_id": sid, "file_id": mod.file_id, "path": mod.path, "qualified_name": qname, "kind": kind,
            "owner_symbol_id": owner, "start_line": node.lineno, "end_line": node.end_lineno or node.lineno,
            "signature": signature, "analysis_status": "inventory_generated",
            "evidence": evidence, "uncertainties": uncertainties, "limitations": [],
        }
        mod.node_symbols[id(node)] = sid
        if qprefix == "":
            mod.top_defs[node.name] = sid
        if is_class:
            self.class_methods[sid] = {}
            self.class_bases_expr[sid] = list(node.bases)
            self.class_module[sid] = mod
            self._collect(mod, node.body, sid, qname, sid)
        else:
            if class_id:
                self.class_methods[class_id].setdefault(node.name, sid)
            self._collect(mod, node.body, sid, f"{qname}.<locals>", None)

    def _is_own(self, dotted: str) -> bool:
        return dotted in self.modules or dotted in self.own_prefixes

    def _import_base(self, mod: ModuleInfo, node: ast.ImportFrom) -> str | None:
        if node.level == 0:
            return node.module
        package = mod.name if mod.is_init else mod.name.rpartition(".")[0]
        parts = package.split(".") if package else []
        up = node.level - 1
        if up > len(parts):
            return None
        if up:
            parts = parts[:-up]
        base = ".".join(parts)
        if node.module:
            base = f"{base}.{node.module}" if base else node.module
        return base

    def _import_bindings(self, mod: ModuleInfo, node: ast.AST) -> list[tuple[str, Binding]]:
        bindings: list[tuple[str, Binding]] = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    bindings.append((alias.asname, ("mod", alias.name)))
                else:
                    top = alias.name.split(".")[0]
                    bindings.append((top, ("mod", top)))
        elif isinstance(node, ast.ImportFrom):
            base = self._import_base(mod, node)
            if base is None:
                return bindings
            for alias in node.names:
                if alias.name == "*":
                    if node not in [None]:
                        mod.star_imports.append(base)
                    continue
                name = alias.asname or alias.name
                sub = f"{base}.{alias.name}"
                bindings.append((name, ("mod", sub) if sub in self.modules else ("from", base, alias.name)))
        return bindings

    def _build_module_table(self, mod: ModuleInfo) -> None:
        nodes = list(_scope_nodes(mod.tree.body))
        for node in nodes:
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                mod.table[node.id] = ("var",)
        for node in nodes:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for name, binding in self._import_bindings(mod, node):
                    mod.table[name] = binding
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                sid = mod.node_symbols.get(id(node))
                if sid:
                    mod.table[node.name] = ("sym", sid)

    # ------------------------------------------------------------ resolution

    def _lookup_module_attr(self, module: str, attr: str, depth: int = 0) -> Binding | None:
        info = self.modules.get(module)
        if info is None:
            return None
        if attr in info.top_defs:
            return ("sym", info.top_defs[attr])
        bound = info.table.get(attr)
        if bound is not None:
            if bound[0] in {"sym", "mod"}:
                return bound
            if bound[0] == "from" and depth < 6:
                if self._is_own(bound[1]):
                    return self._lookup_module_attr(bound[1], bound[2], depth + 1)
                return ("ext", bound[1].split(".")[0])
            return ("var",)
        sub = f"{module}.{attr}"
        if sub in self.modules:
            return ("mod", sub)
        return None

    def _find_method(self, class_id: str, name: str, seen: set[str] | None = None) -> str | None:
        seen = seen or set()
        if class_id in seen:
            return None
        seen.add(class_id)
        found = self.class_methods.get(class_id, {}).get(name)
        if found:
            return found
        for base in self.class_bases.get(class_id, []):
            found = self._find_method(base, name, seen)
            if found:
                return found
        return None

    def _unres(self, code: str) -> Resolution:
        return Resolution("unresolved", code=code)

    def _internal(self, target: str, resolution: str = "static") -> Resolution:
        return Resolution("internal", target=target, resolution=resolution)

    def _lookup(self, name: str, state: State) -> Binding | None:
        for scope in reversed(state.scopes):
            bound = scope.table.get(name)
            if bound is not None:
                return bound
        return None

    def _callable_binding(self, bound: Binding, name: str) -> Resolution:
        kind = bound[0]
        if kind == "sym":
            return self._internal(bound[1])
        if kind == "from":
            base, attr = bound[1], bound[2]
            if not self._is_own(base):
                return Resolution("external", top=base.split(".")[0])
            found = self._lookup_module_attr(base, attr)
            if found is None:
                return self._unres("imported_name_not_found")
            if found[0] == "sym":
                return self._internal(found[1])
            if found[0] == "ext":
                return Resolution("external", top=found[1])
            return self._unres("module_called" if found[0] == "mod" else "callee_is_variable")
        if kind == "mod":
            return Resolution("external", top=bound[1].split(".")[0]) if not self._is_own(bound[1]) else self._unres("module_called")
        if kind == "self" and name == "cls":
            return self._internal(bound[1], "inferred")
        return self._unres("callee_is_variable")

    def _class_member(self, class_id: str, rest: list[str]) -> Resolution:
        if len(rest) != 1:
            return self._unres("nested_attribute")
        method = self._find_method(class_id, rest[0])
        return self._internal(method) if method else self._unres("attribute_not_found_on_class")

    def _walk_module_chain(self, dotted: str, chain: list[str]) -> Resolution:
        if not self._is_own(dotted):
            return Resolution("external", top=dotted.split(".")[0])
        current, index = dotted, 0
        while index < len(chain) and (f"{current}.{chain[index]}" in self.modules or f"{current}.{chain[index]}" in self.own_prefixes):
            current = f"{current}.{chain[index]}"
            index += 1
        remaining = chain[index:]
        if not remaining:
            return self._unres("module_called")
        found = self._lookup_module_attr(current, remaining[0]) if current in self.modules else None
        if found is None:
            return self._unres("module_attribute_not_found")
        if found[0] == "sym":
            if len(remaining) == 1:
                return self._internal(found[1])
            if self.symbols[found[1]]["kind"] in CLASS_KINDS:
                return self._class_member(found[1], remaining[1:])
            return self._unres("receiver_is_function_object")
        if found[0] == "mod":
            return self._walk_module_chain(found[1], remaining[1:])
        if found[0] == "ext":
            return Resolution("external", top=found[1])
        return self._unres("receiver_is_variable")

    def _resolve_chain(self, root: str, chain: list[str], state: State) -> Resolution:
        bound = self._lookup(root, state)
        if bound is None:
            return Resolution("builtin") if hasattr(builtins, root) else self._unres("name_not_found")
        kind = bound[0]
        if kind == "self":
            if len(chain) == 1:
                method = self._find_method(bound[1], chain[0])
                return self._internal(method, "inferred") if method else self._unres("attribute_not_found_on_class")
            return self._unres("instance_attribute_receiver")
        if kind in {"local", "var"}:
            return self._unres("receiver_is_variable")
        if kind == "sym":
            if self.symbols[bound[1]]["kind"] in CLASS_KINDS:
                return self._class_member(bound[1], chain)
            return self._unres("receiver_is_function_object")
        if kind == "mod":
            return self._walk_module_chain(bound[1], chain)
        if kind == "from":
            base, attr = bound[1], bound[2]
            if not self._is_own(base):
                return Resolution("external", top=base.split(".")[0])
            found = self._lookup_module_attr(base, attr)
            if found is None:
                return self._unres("imported_name_not_found")
            if found[0] == "mod":
                return self._walk_module_chain(found[1], chain)
            if found[0] == "sym":
                if self.symbols[found[1]]["kind"] in CLASS_KINDS:
                    return self._class_member(found[1], chain)
                return self._unres("receiver_is_function_object")
            if found[0] == "ext":
                return Resolution("external", top=found[1])
            return self._unres("receiver_is_variable")
        return self._unres("receiver_is_variable")

    def resolve_call(self, func: ast.expr, state: State) -> Resolution:
        """Resolve a callee expression statically."""
        if isinstance(func, ast.Name):
            bound = self._lookup(func.id, state)
            if bound is None:
                return Resolution("builtin") if hasattr(builtins, func.id) else self._unres("name_not_found")
            return self._callable_binding(bound, func.id)
        if isinstance(func, ast.Attribute):
            chain: list[str] = []
            node: ast.expr = func
            while isinstance(node, ast.Attribute):
                chain.append(node.attr)
                node = node.value
            chain.reverse()
            if isinstance(node, ast.Name):
                return self._resolve_chain(node.id, chain, state)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "super":
                if state.method_class and len(chain) == 1:
                    for base in self.class_bases.get(state.method_class, []):
                        method = self._find_method(base, chain[0])
                        if method:
                            return self._internal(method, "inferred")
                return self._unres("super_target_unresolved")
            if isinstance(node, LITERAL_NODES):
                return Resolution("builtin")
            return self._unres("receiver_is_expression")
        return self._unres("callee_is_expression")

    def _resolve_bases(self, class_id: str) -> None:
        mod = self.class_module[class_id]
        state = State((Scope("module", mod.table),), mod.module_id)
        resolved: list[str] = []
        for expr in self.class_bases_expr[class_id]:
            target_expr = expr.value if isinstance(expr, ast.Subscript) else expr
            result = self.resolve_call(target_expr, state)
            text = _short(ast.unparse(expr), 120)
            sym = self.symbols[class_id]
            if result.status == "internal" and self.symbols[result.target]["kind"] in CLASS_KINDS:
                resolved.append(result.target)
                self._add_relation("inherits", class_id, result.target, "static", _ev(mod.path, expr.lineno, expr.end_lineno, self._etype(mod), f"base class: {text}"))
            elif result.status in {"external", "builtin"}:
                if result.top:
                    self.ext_imports  # keep reference; external bases counted via imports
                self.unresolved.append(self._unresolved_record("inheritance", "external_base_class", class_id, mod.path, expr.lineno, expr.end_lineno, text, REASONS["external_base_class"], self._etype(mod), f"base class: {text}", expr.col_offset))
            else:
                self.unresolved.append(self._unresolved_record("inheritance", "unresolved_base_class", class_id, mod.path, expr.lineno, expr.end_lineno, text, REASONS["unresolved_base_class"], self._etype(mod), f"base class: {text}", expr.col_offset))
            del sym
        self.class_bases[class_id] = resolved

    # ---------------------------------------------------------------- records

    def _unresolved_record(self, category: str, code: str, source: str | None, path: str, start: int, end: int | None, expression: str, reason: str, etype: str, desc: str, col: int | None = 0) -> dict:
        uid = "unres:" + _hash(f"{category}|{code}|{source}|{path}|{start}|{col}|{expression}")
        return {
            "unresolved_id": uid, "category": category, "reason_code": code, "source_symbol_id": source,
            "path": path, "expression": expression, "reason": reason, "resolution": "unresolved",
            "analysis_status": "inventory_generated",
            "evidence": [_ev(path, start, end, etype, desc)],
            "uncertainties": [], "limitations": ["Static analysis cannot determine the target of this construct."],
        }

    def _add_relation(self, kind: str, source: str, target: str, resolution: str, evidence: dict, uncertainty: str | None = None) -> None:
        rid = _rel_id(kind, source, target, resolution)
        rel = self.relations.get(rid)
        if rel is None:
            limitation = {
                "calls": "Static syntactic relation; it does not show that the call executes.",
                "imports": "Import statement presence does not show runtime execution (imports may be conditional or unused).",
                "references_test": "A static reference from a test does not show that the test runs or passes.",
                "inherits": "Static base-class expression; metaclasses and dynamic bases are not considered.",
            }.get(kind)
            rel = {
                "relation_id": rid, "source_symbol_id": source, "target_symbol_id": target, "kind": kind,
                "resolution": resolution, "analysis_status": "inventory_generated",
                "evidence": [], "uncertainties": [], "limitations": [limitation] if limitation else [],
            }
            self.relations[rid] = rel
        rel["evidence"].append(evidence)
        if uncertainty and uncertainty not in rel["uncertainties"]:
            rel["uncertainties"].append(uncertainty)

    def _add_contains(self) -> None:
        for sid in sorted(self.symbols):
            sym = self.symbols[sid]
            if sym["owner_symbol_id"]:
                self._add_relation("contains", sym["owner_symbol_id"], sid, "static", _ev(sym["path"], sym["start_line"], sym["end_line"], sym["evidence"][0]["type"], "Definition nested in owner scope"))

    def _link(self, mod: ModuleInfo, kind: str, source: str, target: str, resolution: str, evidence: dict, uncertainty: str | None = None) -> None:
        target_mod = self.modules_by_path.get(self.symbols[target]["path"])
        if mod.is_test and target_mod is not None and not target_mod.is_test and kind in {"calls", "imports"}:
            kind = "references_test"
        self._add_relation(kind, source, target, resolution, evidence, uncertainty)

    # ---------------------------------------------------------------- pass B

    def _function_table(self, mod: ModuleInfo, node: ast.AST, class_id: str | None) -> dict[str, Binding]:
        args = node.args
        params = [a.arg for a in (*args.posonlyargs, *args.args)]
        extra = [a.arg for a in args.kwonlyargs] + ([args.vararg.arg] if args.vararg else []) + ([args.kwarg.arg] if args.kwarg else [])
        table: dict[str, Binding] = {name: ("local",) for name in params + extra}
        if class_id and params and not any(_dotted_text(d) == "staticmethod" for d in node.decorator_list):
            table[params[0]] = ("self", class_id)
        declared_global: set[str] = set()
        nodes = list(_scope_nodes(node.body))
        for item in nodes:
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store):
                table.setdefault(item.id, ("local",))
            elif isinstance(item, ast.ExceptHandler) and item.name:
                table.setdefault(item.name, ("local",))
            elif isinstance(item, (ast.Global, ast.Nonlocal)):
                declared_global.update(item.names)
        for item in nodes:
            if isinstance(item, (ast.Import, ast.ImportFrom)):
                for name, binding in self._import_bindings(mod, item):
                    table[name] = binding
            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                sid = mod.node_symbols.get(id(item))
                if sid:
                    table[item.name] = ("sym", sid)
        for name in declared_global:
            table.pop(name, None)
        return table

    def _class_table(self, mod: ModuleInfo, node: ast.ClassDef) -> dict[str, Binding]:
        table: dict[str, Binding] = {}
        nodes = list(_scope_nodes(node.body))
        for item in nodes:
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store):
                table[item.id] = ("var",)
        for item in nodes:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                sid = mod.node_symbols.get(id(item))
                if sid:
                    table[item.name] = ("sym", sid)
        return table

    def _visit(self, mod: ModuleInfo, node: ast.AST, state: State) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for deco in node.decorator_list:
                self._visit(mod, deco, state)
            for default in [*node.args.defaults, *[d for d in node.args.kw_defaults if d is not None]]:
                self._visit(mod, default, state)
            sid = mod.node_symbols.get(id(node))
            if sid is None:
                return
            in_class = state.scopes[-1].kind == "class"
            class_id = state.owner if in_class else None
            table = self._function_table(mod, node, class_id)
            scopes = tuple(s for s in state.scopes if s.kind != "class") + (Scope("function", table),)
            inner = State(scopes, sid, class_id if in_class else state.method_class, state.cond)
            for stmt in node.body:
                self._visit(mod, stmt, inner)
            return
        if isinstance(node, ast.ClassDef):
            for deco in node.decorator_list:
                self._visit(mod, deco, state)
            for base in node.bases:
                self._visit(mod, base, state)
            for kw in node.keywords:
                self._visit(mod, kw.value, state)
            sid = mod.node_symbols.get(id(node))
            if sid is None:
                return
            inner = State(state.scopes + (Scope("class", self._class_table(mod, node)),), sid, state.method_class, state.cond)
            for stmt in node.body:
                self._visit(mod, stmt, inner)
            return
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            self._record_import(mod, node, state)
            return
        if isinstance(node, ast.Lambda):
            names = {a.arg: ("local",) for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)}
            self._visit(mod, node.body, replace(state, scopes=state.scopes + (Scope("function", names),)))
            return
        if isinstance(node, ast.Call):
            self._record_call(mod, node, state)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and mod.is_test:
            self._record_string_reference(mod, node, state)
        child_state = replace(state, cond=True) if isinstance(node, TRY_NODES) else state
        for child in ast.iter_child_nodes(node):
            self._visit(mod, child, child_state)

    def _record_call(self, mod: ModuleInfo, node: ast.Call, state: State) -> None:
        text = _short(ast.unparse(node.func))
        etype = self._etype(mod)
        if text in DYNAMIC_ATTRS or (isinstance(node.func, ast.Name) and node.func.id in DYNAMIC_NAMES and self._lookup(node.func.id, state) is None):
            self.unresolved.append(self._unresolved_record("dynamic", "dynamic_construct", state.owner, mod.path, node.lineno, node.end_lineno, text, REASONS["dynamic_construct"], etype, f"dynamic construct: {text}", node.col_offset))
        result = self.resolve_call(node.func, state)
        if result.status == "builtin":
            self.counts["call_sites_builtin_skipped"] += 1
        elif result.status == "external":
            self.counts["call_sites_external"] += 1
            self.ext_calls[result.top] += 1
            self.ext_call_paths[result.top].add(mod.path)
        elif result.status == "internal":
            self.counts[f"call_sites_internal_{result.resolution}"] += 1
            desc = f"call to {text}"
            note = "Receiver assumed to be an instance of the enclosing class; a subclass override may be the runtime target." if result.resolution == "inferred" else None
            self._link(mod, "calls", state.owner, result.target, result.resolution, _ev(mod.path, node.lineno, node.end_lineno, etype, desc), note)
            self.internal_calls.append((state.owner, result.target, mod.path, node.lineno))
        else:
            self.counts["call_sites_unresolved"] += 1
            self.unresolved.append(self._unresolved_record("call", result.code, state.owner, mod.path, node.lineno, node.end_lineno, text, REASONS[result.code], etype, f"{result.code}: {text}", node.col_offset))

    def _record_string_reference(self, mod: ModuleInfo, node: ast.Constant, state: State) -> None:
        value = node.value
        if not TEST_STRING_RE.match(value):
            return
        parts = value.split(".")
        for cut in range(len(parts), 0, -1):
            dotted = ".".join(parts[:cut])
            if dotted in self.modules:
                rest = parts[cut:]
                target = self.modules[dotted].module_id
                note = None
                if rest and rest[0] in self.modules[dotted].top_defs:
                    target = self.modules[dotted].top_defs[rest[0]]
                elif rest:
                    note = f"Attribute '{rest[0]}' is not defined statically in {dotted}; relation points to the module."
                self._link(mod, "references_test", state.owner, target, "inferred", _ev(mod.path, node.lineno, node.end_lineno, "test_source", f"string reference: '{value}'"), note or "Reference inferred from a dotted-path string literal (for example a monkeypatch target).")
                return

    def _record_import(self, mod: ModuleInfo, node: ast.AST, state: State) -> None:
        text = _short(ast.unparse(node))
        etype = self._etype(mod)
        suffix = (" [inside function]" if self.symbols[state.owner]["kind"] != "module" else "") + (" [conditional]" if state.cond else "")
        evidence = _ev(mod.path, node.lineno, node.end_lineno, etype, f"import: {text}{suffix}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                dotted = alias.name
                top = dotted.split(".")[0]
                if dotted in self.modules:
                    self._link(mod, "imports", state.owner, self.modules[dotted].module_id, "static", evidence)
                elif top in self.own_tops:
                    code = "namespace_package_import" if dotted in self.own_prefixes else "own_import_not_found"
                    self.unresolved.append(self._unresolved_record("import", code, state.owner, mod.path, node.lineno, node.end_lineno, text, REASONS[code], etype, f"{code}: {text}", node.col_offset))
                else:
                    self.ext_imports[top].append((mod.path, node.lineno, node.end_lineno, text + suffix, etype))
            return
        base = self._import_base(mod, node)
        if base is None:
            self.unresolved.append(self._unresolved_record("import", "relative_import_beyond_top", state.owner, mod.path, node.lineno, node.end_lineno, text, REASONS["relative_import_beyond_top"], etype, text, node.col_offset))
            return
        if base.split(".")[0] not in self.own_tops:
            self.ext_imports[base.split(".")[0]].append((mod.path, node.lineno, node.end_lineno, text + suffix, etype))
            return
        if not self._is_own(base):
            self.unresolved.append(self._unresolved_record("import", "own_import_not_found", state.owner, mod.path, node.lineno, node.end_lineno, text, REASONS["own_import_not_found"], etype, text, node.col_offset))
            return
        for alias in node.names:
            sub = f"{base}.{alias.name}"
            if alias.name == "*":
                if base in self.modules:
                    self._link(mod, "imports", state.owner, self.modules[base].module_id, "static", evidence, "Star import: imported names are not enumerated.")
                continue
            if sub in self.modules:
                self._link(mod, "imports", state.owner, self.modules[sub].module_id, "static", evidence)
                continue
            found = self._lookup_module_attr(base, alias.name) if base in self.modules else None
            if found is not None and found[0] in {"sym", "mod"}:
                target = found[1] if found[0] == "sym" else self.modules[found[1]].module_id
                self._link(mod, "imports", state.owner, target, "static", evidence)
            elif found is not None and found[0] == "ext":
                self.ext_imports[found[1]].append((mod.path, node.lineno, node.end_lineno, text + suffix + " [re-exported external]", etype))
            else:
                if base in self.modules:
                    self._link(mod, "imports", state.owner, self.modules[base].module_id, "static", evidence, f"Imported name '{alias.name}' is not defined statically in {base}; relation points to the module.")
                self.unresolved.append(self._unresolved_record("import", "imported_name_not_found", state.owner, mod.path, node.lineno, node.end_lineno, f"{base}.{alias.name}", REASONS["imported_name_not_found"], etype, text, node.col_offset))

    # ------------------------------------------------------------------ output

    def _file_records(self) -> list[dict]:
        records = []
        for entry in self.entries:
            path = entry.path
            if entry.excluded:
                records.append({
                    "file_id": f"file:{path}", "path": path, "kind": entry.kind or "other", "git_state": "ignored",
                    "analysis_status": "inventory_generated", "inventory_disposition": "excluded",
                    "exclusion_reason": entry.reason,
                    "evidence": [_ev(path, None, None, "configuration", ("Directory entry collapsed by Git ignore rules; " if entry.is_dir else "Ignored file; ") + "path only, contents not read")],
                    "uncertainties": [], "limitations": ["Contents were not read or enumerated."],
                })
                continue
            kind, rule, etype = classify(path)
            record: dict[str, Any] = {
                "file_id": f"file:{path}", "path": path, "kind": kind, "git_state": entry.git_state,
                "analysis_status": "inventory_generated", "inventory_disposition": "included",
                "evidence": [_ev(path, None, None, etype, f"Classified as {kind}: {rule}")],
                "uncertainties": [], "limitations": [],
            }
            mod = self.modules_by_path.get(path)
            if path.endswith(".py"):
                if mod is not None and mod.error:
                    record["analysis_status"] = "blocked"
                    record["uncertainties"].append(f"Parse failed: {mod.error}")
                    record["limitations"].append("No symbols or relations were extracted.")
                else:
                    record["limitations"].append("Static AST analysis only.")
            elif kind == "notebook":
                record["limitations"].append("Notebook cells were not analyzed; classified by extension only.")
            elif path in GENERATED_PATHS:
                record["limitations"].append("Generated artifact; regenerate instead of editing.")
            else:
                record["limitations"].append("Content not parsed; classified by path and extension only.")
            if entry.note:
                record["uncertainties"].append(entry.note)
            records.append(record)
        return records

    def _entry_points(self) -> list[dict]:
        entries: list[dict] = []
        known = {e.path for e in self.entries if not e.excluded}
        scripts = (self.pyproject.get("project", {}).get("scripts", {}))
        pyproject_lines = (self.file_bytes.get("pyproject.toml") or (REPO_ROOT / "pyproject.toml").read_bytes()).decode("utf-8").split("\n") if (REPO_ROOT / "pyproject.toml").is_file() else []
        for name, target in sorted(scripts.items()):
            module_name, _, func = target.partition(":")
            sid = f"py:{self.modules[module_name].path}::{func}" if module_name in self.modules else None
            sid = sid if sid in self.symbols else None
            line = next((i + 1 for i, text in enumerate(pyproject_lines) if text.strip().startswith(f"{name} =")), None)
            entries.append(self._entry(f"entry:console_script:{name}", "console_script", "pyproject.toml", line, sid, target,
                                       f"Console command '{name}' (after installation)", [_ev("pyproject.toml", line, line, "configuration", f"[project.scripts] {name} = {target}")],
                                       [] if sid else [f"Target '{target}' could not be resolved to an inventoried symbol."], []))
        for path, mod in sorted(self.modules_by_path.items()):
            if mod.tree is None:
                continue
            etype = self._etype(mod)
            module_calls = sorted({t for s, t, p, _ in self.internal_calls if s == mod.module_id})
            if path.endswith("/__main__.py") or path == "__main__.py":
                package = mod.name.rpartition(".")[0]
                entries.append(self._entry(f"entry:module_main:{path}", "module_main", path, 1 if mod.line_count else None, None, None, f"python -m {package}", [_ev(path, 1, mod.line_count, etype, "__main__.py executed by python -m")] if mod.line_count else [_ev(path, None, None, etype, "Empty __main__.py executed by python -m")], [], module_calls))
            for start, end in mod.guards:
                called = sorted({t for s, t, p, line in self.internal_calls if p == path and start <= line <= end})
                entries.append(self._entry(f"entry:main_guard:{path}", "main_guard", path, start, None, None, f"python {path}", [_ev(path, start, end, etype, "if __name__ == '__main__' guard")], [], called))
            base = path.rsplit("/", 1)[-1]
            if mod.is_test and base.startswith("test_"):
                entries.append(self._entry(f"entry:pytest_module:{path}", "pytest_module", path, 1 if mod.line_count else None, None, None, "pytest test discovery by file name", [_ev(path, 1, mod.line_count, "test_source", "File name matches pytest default pattern test_*.py")] if mod.line_count else [_ev(path, None, None, "test_source", "Empty pytest-discoverable file")], ["No pytest configuration was found in pyproject.toml; default discovery is assumed."], []))
            if mod.is_test and base == "conftest.py":
                entries.append(self._entry(f"entry:pytest_conftest:{path}", "pytest_conftest", path, 1 if mod.line_count else None, None, None, "pytest conftest loaded automatically", [_ev(path, 1, mod.line_count, "test_source", "conftest.py")] if mod.line_count else [_ev(path, None, None, "test_source", "Empty conftest.py")], [], module_calls))
        for path in sorted(known):
            suffix = Path(path).suffix.lower()
            if suffix in {".bat", ".cmd"}:
                text = (REPO_ROOT / path).read_bytes().decode("utf-8", errors="replace").split("\n")
                for number, line in enumerate(text, 1):
                    match = re.search(r"([\w./\\-]+\.py)\b", line)
                    if match:
                        target = match.group(1).replace("\\", "/")
                        sid = self.modules_by_path[target].module_id if target in self.modules_by_path else None
                        entries.append(self._entry(f"entry:batch_launcher:{path}", "batch_launcher", path, number, sid, target, f"Windows launcher: {_short(line.strip())}", [_ev(path, number, number, "source", "Launcher line referencing a Python file")], [] if sid else [f"Target '{target}' not found among inventoried Python files."], []))
                        break
            elif suffix == ".ipynb":
                entries.append(self._entry(f"entry:notebook:{path}", "notebook", path, None, None, None, "Interactive notebook", [_ev(path, None, None, "source", "Jupyter notebook")], ["Notebook cells were not analyzed."], []))
        return sorted(entries, key=lambda e: e["entry_id"])

    def _entry(self, entry_id: str, kind: str, path: str, line: int | None, target: str | None, expression: str | None, invocation: str, evidence: list, uncertainties: list, called: list) -> dict:
        return {
            "entry_id": entry_id, "kind": kind, "path": path, "start_line": line, "target_symbol_id": target,
            "target_expression": expression, "invocation": invocation, "static_call_targets": called,
            "support_status": "unconfirmed", "analysis_status": "inventory_generated",
            "evidence": evidence,
            "uncertainties": ["Support status is unconfirmed (see question:supported-execution-surfaces).", *uncertainties],
            "limitations": ["Detected statically; it does not show that this entry point works or is supported."],
        }

    def _dependencies(self) -> list[dict]:
        project = self.pyproject.get("project", {})
        declared: dict[str, tuple[str, list[str]]] = {}
        groups = [("dependencies", project.get("dependencies", []))]
        groups += [(f"optional:{k}", v) for k, v in sorted(project.get("optional-dependencies", {}).items())]
        for group, items in groups:
            for item in items:
                match = re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*", item)
                if match:
                    key = _norm_dist(match.group(0))
                    declared.setdefault(key, (match.group(0), []))[1].append(group)
        records: list[dict] = []
        observed: set[str] = set()
        stdlib = sys.stdlib_module_names
        for top in sorted(self.ext_imports):
            sites = sorted(self.ext_imports[top])
            alias = IMPORT_NAME_ALIASES.get(top, top)
            key = _norm_dist(alias)
            observed.add(key)
            if top in stdlib or top == "__future__":
                classification, dist, groups_in = "stdlib", None, []
                uncertainties = []
            elif key in declared:
                classification, (dist, groups_in) = "third_party_declared", declared[key]
                uncertainties = ["Import name matched to a declared distribution by normalized name or alias table; not verified against installed metadata."]
            else:
                classification, dist, groups_in = "undeclared_or_unresolved", None, []
                uncertainties = ["Not in the standard library and not matched to pyproject.toml; may be a missing declaration, a legacy/stale import path or an unmapped alias."]
            records.append({
                "dep_id": f"dep:{top}", "top_level_module": top, "classification": classification,
                "declared_distribution": dist, "declared_in": groups_in,
                "importing_paths": sorted({s[0] for s in sites}), "import_site_count": len(sites),
                "importing_module_ids": sorted({self.modules_by_path[p].module_id for p in {s[0] for s in sites} if p in self.modules_by_path}),
                "external_call_site_count": self.ext_calls.get(top, 0),
                "analysis_status": "inventory_generated",
                "evidence": [_ev(p, s, e, t, "import: " + _short(txt, 200)) for p, s, e, txt, t in sites],
                "uncertainties": uncertainties,
                "limitations": ["Only static import statements are considered; dynamic imports are listed in unresolved.jsonl."],
            })
        for key in sorted(declared):
            if key not in observed:
                dist, groups_in = declared[key]
                records.append({
                    "dep_id": f"dep:declared:{key}", "top_level_module": None, "classification": "declared_not_observed",
                    "declared_distribution": dist, "declared_in": groups_in, "importing_paths": [],
                    "importing_module_ids": [],
                    "import_site_count": 0, "external_call_site_count": 0, "analysis_status": "inventory_generated",
                    "evidence": [_ev("pyproject.toml", None, None, "configuration", f"Declared in {', '.join(groups_in)}")],
                    "uncertainties": ["No static import of this distribution's top-level module was found; it may be used dynamically, by name, or only as a tool."],
                    "limitations": ["Mapping between distribution and import name is heuristic."],
                })
        return sorted(records, key=lambda r: r["dep_id"])

    def outputs(self) -> Outputs:
        """Assemble sorted outputs and the generation report."""
        files = self._file_records()
        symbols = sorted(self.symbols.values(), key=lambda s: (s["path"], s["start_line"], s["qualified_name"]))
        relations = sorted(self.relations.values(), key=lambda r: (r["kind"], r["source_symbol_id"], r["target_symbol_id"], r["resolution"]))
        unresolved = sorted(self.unresolved, key=lambda u: (u["path"], u["evidence"][0].get("start_line", 0), u["unresolved_id"]))
        entries = self._entry_points()
        deps = self._dependencies()
        # These fields represent independent work axes. AST generation never
        # asserts editorial approval or execution verification.
        for records in (files, symbols, relations, unresolved, entries, deps):
            for record in records:
                old_status = record.get("analysis_status")
                record["inventory_status"] = "excluded" if record.get("inventory_disposition") == "excluded" else "inventoried"
                record["analysis_status"] = "blocked" if old_status == "blocked" else "static_analyzed"
                record["documentation_status"] = "not_documented"
                record["execution_status"] = "not_verified"
        digest = hashlib.sha256()
        inputs = sorted(p for p in self.file_bytes) + [p for p in ("pyproject.toml", "start.bat") if (REPO_ROOT / p).is_file() and p not in self.file_bytes]
        for path in inputs:
            data = self.file_bytes.get(path) or (REPO_ROOT / path).read_bytes()
            digest.update(path.encode() + b"\0" + hashlib.sha256(data).digest())
        counts = {
            "files_by_kind": dict(sorted(Counter(f["kind"] for f in files).items())),
            "files_by_git_state": dict(sorted(Counter(f["git_state"] for f in files).items())),
            "files_by_disposition": dict(sorted(Counter(f["inventory_disposition"] for f in files).items())),
            "python_files_parsed": sum(1 for m in self.modules_by_path.values() if m.tree is not None),
            "python_files_failed": sum(1 for m in self.modules_by_path.values() if m.tree is None),
            "symbols_by_kind": dict(sorted(Counter(s["kind"] for s in symbols).items())),
            "relations_by_kind_and_resolution": dict(sorted(Counter(f"{r['kind']}/{r['resolution']}" for r in relations).items())),
            "unresolved_by_reason": dict(sorted(Counter(u["reason_code"] for u in unresolved).items())),
            "call_sites": dict(sorted(self.counts.items())),
            "entry_points_by_kind": dict(sorted(Counter(e["kind"] for e in entries).items())),
            "dependencies_by_classification": dict(sorted(Counter(d["classification"] for d in deps).items())),
        }
        report = {
            "generator": {"path": TOOL_PATH, "version": GENERATOR_VERSION},
            "schema_id": json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["$id"],
            "git_revision": git_revision(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "analysis_input_digest": digest.hexdigest(),
            "regeneration_command": "python docs/book/inventory/inventory_tool.py generate",
            "counts": counts,
            "skipped": {
                "tracked_paths_missing_on_disk": self.missing,
                "python_files_failed": sorted(p for p, m in self.modules_by_path.items() if m.tree is None),
                "excluded_paths": sorted(f["path"] for f in files if f["inventory_disposition"] == "excluded"),
            },
            "limitations": LIMITATIONS,
        }
        return Outputs(files, symbols, relations, unresolved, entries, deps, report)


# ----------------------------------------------------------------- serialization


def _dumps(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def serialize(out: Outputs) -> dict[str, bytes]:
    """Serialize inventory outputs and authored claims to repository paths."""
    mapping = {
        "files": out.files, "symbols": out.symbols, "relations": out.relations, "xrefs": [],
        "flow": [], "claims": out.claims,
        "unresolved": out.unresolved, "entries": out.entries, "deps": out.deps,
    }
    result: dict[str, bytes] = {}
    for key, records in mapping.items():
        text = "".join(_dumps(r) + "\n" for r in records)
        result[STREAMS[key]] = text.encode("utf-8")
    result[REPORT_JSON_PATH] = (json.dumps(out.report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return result


def generate_outputs() -> Outputs:
    """Run static analysis and retain authored claim records."""
    inventory = Inventory()
    inventory.run()
    outputs = inventory.outputs()
    claims_path = REPO_ROOT / STREAMS["claims"]
    if claims_path.is_file():
        claims, errors = load_jsonl(claims_path)
        if errors:
            raise ValueError(
                f"Cannot preserve authored claim records: {errors[0]}"
            )
        outputs.claims = claims
    return outputs


# -------------------------------------------------------------------- validation


def _type_ok(value: Any, expected: str) -> bool:
    return {
        "string": isinstance(value, str), "integer": isinstance(value, int) and not isinstance(value, bool),
        "object": isinstance(value, dict), "array": isinstance(value, list), "null": value is None,
        "boolean": isinstance(value, bool), "number": isinstance(value, (int, float)) and not isinstance(value, bool),
    }[expected]


def schema_errors(instance: Any, schema: dict, root: dict, path: str = "$") -> list[str]:
    """Validate ``instance`` against the JSON Schema subset used by schema.json."""
    if "$ref" in schema:
        node: Any = root
        for token in schema["$ref"][2:].split("/"):
            node = node[token]
        return schema_errors(instance, node, root, path)
    errors: list[str] = []
    expected = schema.get("type")
    if expected and not _type_ok(instance, expected):
        return [f"{path}: expected {expected}"]
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum")
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than minLength")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: {instance!r} does not match pattern")
    if isinstance(instance, int) and not isinstance(instance, bool) and "minimum" in schema and instance < schema["minimum"]:
        errors.append(f"{path}: below minimum")
    if isinstance(instance, dict):
        for name in schema.get("required", []):
            if name not in instance:
                errors.append(f"{path}: missing required '{name}'")
        props = schema.get("properties", {})
        for name, value in instance.items():
            if name in props:
                errors.extend(schema_errors(value, props[name], root, f"{path}.{name}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property '{name}'")
    if isinstance(instance, list) and "items" in schema:
        for index, item in enumerate(instance):
            errors.extend(schema_errors(item, schema["items"], root, f"{path}[{index}]"))
    if isinstance(instance, list) and len(instance) < schema.get("minItems", 0):
        errors.append(f"{path}: fewer than minItems")
    for sub in schema.get("allOf", []):
        errors.extend(schema_errors(instance, sub, root, path))
    if "oneOf" in schema:
        matches = sum(1 for sub in schema["oneOf"] if not schema_errors(instance, sub, root, path))
        if matches != 1:
            errors.append(f"{path}: matches {matches} oneOf variants (expected 1)")
    if "if" in schema:
        branch = "then" if not schema_errors(instance, schema["if"], root, path) else "else"
        if branch in schema:
            errors.extend(schema_errors(instance, schema[branch], root, path))
    if "not" in schema and not schema_errors(instance, schema["not"], root, path):
        errors.append(f"{path}: matches a forbidden 'not' schema")
    return errors


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    """Load a JSONL file; return records and parse errors."""
    records: list[dict] = []
    errors: list[str] = []
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [], [f"{path.name}: could not read UTF-8 JSONL ({exc})"]
    for number, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line, object_pairs_hook=_reject_duplicate_json_keys)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{path.name}:{number}: invalid JSON ({exc})")
            continue
        if isinstance(value, dict):
            records.append(value)
        else:
            errors.append(f"{path.name}:{number}: not a JSON object")
    return records, errors


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate object keys instead of silently discarding authored data."""
    record: dict[str, Any] = {}
    for key, value in pairs:
        if key in record:
            raise ValueError(f"duplicate object key {key!r}")
        record[key] = value
    return record


def global_checks(data: dict[str, list[dict]], schema: dict, line_count: Callable[[str], int | None]) -> list[str]:
    """Check cross-record integrity; returns a list of error strings."""
    errors: list[str] = []
    defs = {
        "files": "fileRecord",
        "symbols": "symbolRecord",
        "relations": "relationRecord",
        "xrefs": "documentationReferenceRecord",
        "flow": "controlFlowRecord",
        "claims": "claimRecord",
        "unresolved": "unresolvedRecord",
        "entries": "entryPointRecord",
        "deps": "externalDependencyRecord",
    }
    for stream, def_name in defs.items():
        for index, record in enumerate(data.get(stream, [])):
            for message in schema_errors(record, {"$ref": f"#/$defs/{def_name}"}, schema, f"{stream}[{index}]"):
                errors.append(f"schema: {message}")
    # Do not run relationship checks on malformed shapes: report schema errors
    # instead of raising KeyError/TypeError while trying to follow bad fields.
    if errors:
        return errors
    id_fields = {"files": "file_id", "symbols": "symbol_id", "relations": "relation_id", "xrefs": "reference_id", "flow": "control_id", "claims": "claim_id", "unresolved": "unresolved_id", "entries": "entry_id", "deps": "dep_id"}
    for stream, field_name in id_fields.items():
        seen: set[str] = set()
        for record in data.get(stream, []):
            value = record.get(field_name)
            if value in seen:
                errors.append(f"duplicate {field_name}: {value}")
            seen.add(value)
    files = {r["file_id"]: r for r in data.get("files", []) if "file_id" in r}
    paths = [r.get("path") for r in data.get("files", [])]
    if len(paths) != len(set(paths)):
        errors.append("duplicate file path in files stream")
    path_set = set(paths)
    for record in files.values():
        if record["file_id"] != f"file:{record['path']}":
            errors.append(f"file_id does not match path: {record['file_id']}")
        disposition = record.get("inventory_disposition")
        inventory_status = record.get("inventory_status")
        if disposition == "included" and inventory_status == "excluded":
            errors.append(f"file {record['path']}: inventory_status excluded contradicts included disposition")
        if disposition == "excluded" and inventory_status != "excluded":
            errors.append(f"file {record['path']}: excluded disposition requires inventory_status excluded")
    symbols = {r["symbol_id"]: r for r in data.get("symbols", []) if "symbol_id" in r}
    modules_per_file: Counter[str] = Counter()
    for sym in symbols.values():
        file_rec = files.get(sym.get("file_id"))
        if file_rec is None:
            errors.append(f"symbol {sym['symbol_id']}: unknown file_id {sym.get('file_id')}")
        elif file_rec["path"] != sym.get("path"):
            errors.append(f"symbol {sym['symbol_id']}: path differs from file record")
        if sym["symbol_id"] != f"py:{sym.get('path')}::{sym.get('qualified_name')}":
            errors.append(f"symbol_id does not derive from path and qualified name: {sym['symbol_id']}")
        owner = sym.get("owner_symbol_id")
        if owner is not None:
            owner_rec = symbols.get(owner)
            if owner_rec is None:
                errors.append(f"symbol {sym['symbol_id']}: unknown owner {owner}")
            elif owner_rec["path"] != sym["path"]:
                errors.append(f"symbol {sym['symbol_id']}: owner in another file")
        elif sym.get("kind") != "module":
            errors.append(f"symbol {sym['symbol_id']}: non-module symbol without owner")
        if sym.get("kind") == "module":
            modules_per_file[sym["path"]] += 1
        count = line_count(sym.get("path", ""))
        start, end = sym.get("start_line"), sym.get("end_line")
        if (start is None) != (end is None):
            errors.append(f"symbol {sym['symbol_id']}: line range must provide both endpoints")
        elif start is None:
            if sym.get("kind") != "module" or count != 0:
                errors.append(f"symbol {sym['symbol_id']}: missing line range")
        elif start < 1 or end < start or count is None or end > count:
            errors.append(f"symbol {sym['symbol_id']}: invalid line range {start}-{end}")
    for record in files.values():
        if record.get("kind") in {"python_source", "python_test", "script"} and str(record["path"]).endswith(".py") and record.get("inventory_disposition") != "excluded":
            expected = 1 if record.get("analysis_status") != "blocked" else 0
            if modules_per_file.get(record["path"], 0) != expected:
                errors.append(f"python file {record['path']}: expected {expected} module symbol(s)")
    for rel in data.get("relations", []):
        if rel.get("source_symbol_id") not in symbols:
            errors.append(f"relation {rel.get('relation_id')}: unknown source_symbol_id {rel.get('source_symbol_id')}")
        if rel.get("target_symbol_id") is not None and rel.get("target_symbol_id") not in symbols:
            errors.append(f"relation {rel.get('relation_id')}: unknown target_symbol_id {rel.get('target_symbol_id')}")
        target_ref = rel.get("target_symbol_id") or rel.get("target_dependency_id") or ""
        expected_id = _rel_id(rel.get("kind", ""), rel.get("source_symbol_id", ""), target_ref, rel.get("resolution", ""))
        if rel.get("relation_id") != expected_id:
            errors.append(f"relation_id is not deterministic for {rel.get('relation_id')}")
        if rel.get("resolution") == "unresolved":
            errors.append(f"relation {rel.get('relation_id')}: unresolved relations must not carry a target symbol")
        if rel.get("kind") == "contains":
            target = symbols.get(rel.get("target_symbol_id"))
            if target is not None and target.get("owner_symbol_id") != rel.get("source_symbol_id"):
                errors.append(f"relation {rel.get('relation_id')}: contains does not match owner")
    for record in data.get("unresolved", []):
        source = record.get("source_symbol_id")
        if source is not None and source not in symbols:
            errors.append(f"unresolved {record.get('unresolved_id')}: unknown source symbol")
        if record.get("path") not in path_set:
            errors.append(f"unresolved {record.get('unresolved_id')}: path not in file inventory")
        elif source in symbols and symbols[source].get("path") != record.get("path"):
            errors.append(f"unresolved {record.get('unresolved_id')}: source symbol is in another file")
    for record in data.get("entries", []):
        target = record.get("target_symbol_id")
        if target is not None and target not in symbols:
            errors.append(f"entry {record.get('entry_id')}: unknown target symbol")
        for called in record.get("static_call_targets", []):
            if called not in symbols:
                errors.append(f"entry {record.get('entry_id')}: unknown static call target")
        if record.get("path") not in path_set:
            errors.append(f"entry {record.get('entry_id')}: path not in file inventory")
        elif record.get("start_line") is not None:
            count = line_count(record["path"])
            if count is not None and record["start_line"] > count:
                errors.append(f"entry {record.get('entry_id')}: start_line beyond end of file")
    for record in data.get("deps", []):
        for importing in record.get("importing_paths", []):
            if importing not in path_set:
                errors.append(f"dependency {record.get('dep_id')}: importing path not in file inventory")
        classification = record.get("classification")
        for module_id in record.get("importing_module_ids", []):
            if module_id not in symbols or symbols[module_id].get("kind") != "module":
                errors.append(f"dependency {record.get('dep_id')}: importing module ID is not an inventoried module")
        if classification == "stdlib" and record.get("declared_distribution") is not None:
            errors.append(f"dependency {record.get('dep_id')}: stdlib record has a declared distribution")
        if classification == "third_party_declared" and not record.get("declared_distribution"):
            errors.append(f"dependency {record.get('dep_id')}: declared third-party distribution is missing")
        if classification == "declared_not_observed" and (record.get("top_level_module") is not None or record.get("importing_paths") or record.get("import_site_count") != 0):
            errors.append(f"dependency {record.get('dep_id')}: declared_not_observed record has observed imports")
    evidence_ids: dict[str, dict] = {}
    for stream, records in data.items():
        for record in records:
            for item in record.get("evidence", []):
                previous = evidence_ids.setdefault(item["evidence_id"], item)
                if previous != item:
                    errors.append(f"{stream}: conflicting evidence records share ID {item['evidence_id']}")
                if item.get("path") not in path_set:
                    errors.append(f"{stream}: evidence path not in file inventory: {item.get('path')}")
                    continue
                evidence_symbol_id = item.get("symbol_id")
                if evidence_symbol_id is not None:
                    evidence_symbol = symbols.get(evidence_symbol_id)
                    if evidence_symbol is None:
                        errors.append(f"{stream}: evidence references unknown symbol {evidence_symbol_id}")
                    elif evidence_symbol.get("path") != item.get("path"):
                        errors.append(f"{stream}: evidence symbol {evidence_symbol_id} is not in {item.get('path')}")
                    else:
                        symbol_start = evidence_symbol.get("start_line")
                        symbol_end = evidence_symbol.get("end_line")
                        evidence_start = item.get("start_line")
                        evidence_end = item.get("end_line")
                        if (
                            symbol_start is not None
                            and symbol_end is not None
                            and evidence_start is not None
                            and evidence_end is not None
                            and (evidence_start < symbol_start or evidence_end > symbol_end)
                        ):
                            errors.append(
                                f"{stream}: evidence line range is outside symbol {evidence_symbol_id}"
                            )
                count = line_count(item["path"])
                start, end = item.get("start_line"), item.get("end_line")
                if start is not None and end is not None and start > end:
                    errors.append(f"{stream}: evidence line range reversed in {item['path']}")
                if (start is not None or end is not None) and count is None:
                    errors.append(f"{stream}: evidence line range cannot be verified for {item['path']}")
                if count is not None and ((start is not None and start > count) or (end is not None and end > count)):
                    errors.append(f"{stream}: evidence line out of range in {item['path']}")
                if (start is None) != (end is None):
                    errors.append(f"{stream}: evidence line range must provide both endpoints in {item['path']}")
                if start is not None and (start < 1 or end is None):
                    errors.append(f"{stream}: evidence line range is incomplete or starts before line 1 in {item['path']}")
                for field in ("observed_at",):
                    value = item.get(field)
                    if value is not None:
                        try:
                            datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
                        except ValueError:
                            errors.append(f"{stream}: evidence {field} is not a valid UTC calendar timestamp")
                revision = item.get("repository_revision")
                if revision is not None and not _is_git_commit_revision(revision):
                    errors.append(f"{stream}: evidence repository_revision is not an available Git commit")
    for claim in data.get("claims", []):
        missing = set(claim["evidence_ids"]) - evidence_ids.keys()
        if missing:
            errors.append(f"claim {claim['claim_id']}: unknown evidence IDs {sorted(missing)}")
        if claim["chapter_path"] not in path_set:
            errors.append(f"claim {claim['claim_id']}: chapter path not in file inventory")
    for xref in data.get("xrefs", []):
        if xref["documentation_path"] not in path_set:
            errors.append(f"reference {xref['reference_id']}: documentation path not in file inventory")
        target_symbol = xref.get("target_symbol_id")
        if target_symbol is not None and target_symbol not in symbols:
            errors.append(f"reference {xref['reference_id']}: unknown target symbol")
        if xref["status"] == "resolved":
            if xref["target_path"] not in path_set:
                errors.append(f"reference {xref['reference_id']}: resolved target path not in file inventory")
            else:
                target_file = next((item for item in files.values() if item["path"] == xref["target_path"]), None)
                if target_file is None or target_file.get("inventory_disposition") != "included":
                    errors.append(f"reference {xref['reference_id']}: resolved target is excluded from inventory")
                elif line_count(xref["target_path"]) is None:
                    errors.append(f"reference {xref['reference_id']}: resolved target cannot be verified on disk")
            if target_symbol is not None and target_symbol in symbols and symbols[target_symbol].get("path") != xref["target_path"]:
                errors.append(f"reference {xref['reference_id']}: target symbol is not in target path")
    dependencies = {record["dep_id"] for record in data.get("deps", [])}
    for relation in data.get("relations", []):
        target_dependency_id = relation.get("target_dependency_id")
        if target_dependency_id and target_dependency_id not in dependencies:
            errors.append(f"relation {relation['relation_id']}: unknown target dependency {target_dependency_id}")
    for record in data.get("flow", []):
        if record["source_symbol_id"] not in symbols:
            errors.append(f"control flow {record['control_id']}: unknown source symbol")
        elif symbols[record["source_symbol_id"]]["path"] != record["path"]:
            errors.append(f"control flow {record['control_id']}: source symbol is in another file")
        count = line_count(record["path"])
        start, end = record["start_line"], record["end_line"]
        if start < 1 or end < start:
            errors.append(f"control flow {record['control_id']}: invalid line range {start}-{end}")
        if count is None:
            errors.append(f"control flow {record['control_id']}: source path cannot be verified on disk")
        elif end > count:
            errors.append(f"control flow {record['control_id']}: line range {start}-{end} exceeds {count} lines")
        file_rec = next((item for item in files.values() if item["path"] == record["path"]), None)
        if file_rec is None or file_rec.get("inventory_disposition") != "included":
            errors.append(f"control flow {record['control_id']}: source path is not included in inventory")
        handler = record.get("handler_symbol_id")
        if handler and handler not in symbols:
            errors.append(f"control flow {record['control_id']}: unknown handler symbol")
    for stream, records in data.items():
        for record in records:
            if record.get("analysis_status") == "blocked" and not (record.get("uncertainties") or record.get("limitations")):
                errors.append(f"{stream}: analysis_status blocked requires a recorded reason")
            if record.get("analysis_status") == "human_reviewed" or record.get("documentation_status") in {"reviewed", "approved"}:
                reviews = [item for item in record.get("evidence", []) if item.get("type") == "review" and item.get("result") == "passed"]
                if not reviews:
                    errors.append(f"{stream}: human-reviewed/reviewed/approved status requires passed review evidence")
            if record.get("inventory_status") == "excluded" and stream != "files" and not (record.get("uncertainties") or record.get("limitations")):
                errors.append(f"{stream}: excluded inventory status requires a recorded reason")
            if record.get("execution_status") in {"passed", "failed"}:
                expected_result = record["execution_status"]
                execution_evidence = [item for item in record.get("evidence", []) if item.get("type") in {"test_execution", "runtime_observation"}]
                if not any(item.get("result") == expected_result for item in execution_evidence):
                    errors.append(f"{stream}: execution_status {expected_result} requires matching execution evidence")
                if any(item.get("result") != expected_result for item in execution_evidence):
                    errors.append(f"{stream}: execution evidence result contradicts execution_status {expected_result}")
            elif record.get("execution_status") == "not_applicable" and any(
                item.get("type") in {"test_execution", "runtime_observation"} for item in record.get("evidence", [])
            ):
                errors.append(f"{stream}: not_applicable execution_status contradicts execution evidence")
            if stream == "relations" and record.get("resolution") == "runtime_observed":
                observations = [item for item in record.get("evidence", []) if item.get("type") == "runtime_observation" and item.get("result") == "passed"]
                if record.get("execution_status") != "passed" or not observations:
                    errors.append(f"relations: runtime_observed requires passed execution_status and passed runtime_observation evidence")
    return errors


def _negative_self_tests(schema: dict) -> list[tuple[str, bool]]:
    """Confirm that invalid records and broken data sets are rejected."""
    evidence: list = []
    file_rec = {"file_id": "file:a.py", "path": "a.py", "kind": "python_source", "git_state": "tracked", "analysis_status": "inventory_generated", "evidence": evidence, "uncertainties": [], "limitations": []}
    sym_rec = {"symbol_id": "py:a.py::<module>", "file_id": "file:a.py", "path": "a.py", "qualified_name": "<module>", "kind": "module", "owner_symbol_id": None, "start_line": 1, "end_line": 3, "analysis_status": "inventory_generated", "evidence": [], "uncertainties": [], "limitations": []}
    rel_rec = {"relation_id": _rel_id("calls", sym_rec["symbol_id"], sym_rec["symbol_id"], "static"), "source_symbol_id": sym_rec["symbol_id"], "target_symbol_id": sym_rec["symbol_id"], "kind": "calls", "resolution": "static", "analysis_status": "inventory_generated", "evidence": [], "uncertainties": [], "limitations": []}
    base = {"files": [file_rec], "symbols": [sym_rec], "relations": [rel_rec]}
    unresolved_rec = {
        "unresolved_id": "unres:test", "category": "call", "reason_code": "callee_is_variable",
        "source_symbol_id": sym_rec["symbol_id"], "path": "a.py", "expression": "callback()",
        "reason": "The callback target is not statically known.", "resolution": "unresolved",
        "analysis_status": "inventory_generated", "evidence": [], "uncertainties": [], "limitations": [],
    }
    entry_rec = {
        "entry_id": "entry:test", "kind": "main_guard", "path": "a.py", "start_line": 1,
        "target_symbol_id": None, "target_expression": None, "invocation": "python a.py",
        "static_call_targets": [], "support_status": "unconfirmed", "analysis_status": "inventory_generated",
        "evidence": [], "uncertainties": [], "limitations": [],
    }
    dependency_rec = {
        "dep_id": "dep:example", "top_level_module": "example", "classification": "undeclared_or_unresolved",
        "declared_distribution": None, "declared_in": [], "importing_paths": [], "import_site_count": 0,
        "importing_module_ids": [], "external_call_site_count": 0, "analysis_status": "inventory_generated",
        "evidence": [], "uncertainties": [], "limitations": [],
    }
    for sample in (file_rec, sym_rec, rel_rec, unresolved_rec, entry_rec, dependency_rec):
        sample.update({
            "inventory_status": "inventoried",
            "analysis_status": "static_analyzed",
            "documentation_status": "not_documented",
            "execution_status": "not_verified",
        })
    with_sidecars = {**base, "unresolved": [unresolved_rec], "entries": [entry_rec], "deps": [dependency_rec]}
    counter = lambda _path: 10  # noqa: E731

    def file_schema_ok(record: dict) -> bool:
        return not schema_errors(record, {"$ref": "#/$defs/fileRecord"}, schema)

    def mutated(**changes: Any) -> dict:
        return {**file_rec, **changes}

    results = [
        ("valid baseline data set passes", not global_checks(base, schema, counter)),
        ("absolute POSIX path rejected", not file_schema_ok(mutated(path="/etc/a.py"))),
        ("absolute Windows path rejected", not file_schema_ok(mutated(path="C:/a.py"))),
        ("backslash path rejected", not file_schema_ok(mutated(path="a\\b.py"))),
        ("parent-directory segment rejected", not file_schema_ok(mutated(path="../a.py"))),
        ("unknown enum value rejected", not file_schema_ok(mutated(kind="invented"))),
        ("unexpected property rejected", not file_schema_ok(mutated(extra=1))),
        ("excluded record without reason rejected", not file_schema_ok(mutated(inventory_disposition="excluded"))),
        ("included record with exclusion reason rejected", not file_schema_ok(mutated(inventory_disposition="included", exclusion_reason="x"))),
        ("duplicate file id detected", any("duplicate" in e for e in global_checks({**base, "files": [file_rec, dict(file_rec)]}, schema, counter))),
        ("duplicate symbol id detected", any("duplicate" in e for e in global_checks({**base, "symbols": [sym_rec, dict(sym_rec)]}, schema, counter))),
        ("broken relation target detected", any("unknown target_symbol_id" in e for e in global_checks({**base, "relations": [{**rel_rec, "target_symbol_id": "py:a.py::missing"}]}, schema, counter))),
        ("symbol with unknown file detected", any("unknown file_id" in e for e in global_checks({**base, "symbols": [{**sym_rec, "file_id": "file:zzz.py"}]}, schema, counter))),
        ("line beyond end of file detected", any("invalid line range" in e for e in global_checks({**base, "symbols": [{**sym_rec, "end_line": 99}]}, schema, counter))),
        ("non-deterministic relation id detected", any("not deterministic" in e for e in global_checks({**base, "relations": [{**rel_rec, "relation_id": "rel:wrong"}]}, schema, counter))),
        ("evidence path outside inventory detected", any("evidence path" in e for e in global_checks({**base, "relations": [{**rel_rec, "evidence": [_ev("nope.py", 1, 1, "source", "x")]}]}, schema, counter))),
        ("valid auxiliary records pass their schemas", not global_checks(with_sidecars, schema, counter)),
        ("unresolved record missing required field rejected", any("missing required 'reason'" in e for e in global_checks({**with_sidecars, "unresolved": [{k: v for k, v in unresolved_rec.items() if k != "reason"}]}, schema, counter))),
        ("entry point missing required field rejected", any("missing required 'static_call_targets'" in e for e in global_checks({**with_sidecars, "entries": [{k: v for k, v in entry_rec.items() if k != "static_call_targets"}]}, schema, counter))),
        ("entry point invalid enum rejected", any("support_status" in e for e in global_checks({**with_sidecars, "entries": [{**entry_rec, "support_status": "bogus"}]}, schema, counter))),
        ("external dependency invalid classification rejected", any("classification" in e for e in global_checks({**with_sidecars, "deps": [{**dependency_rec, "classification": "invented"}]}, schema, counter))),
        ("broken unresolved source reference detected", any("unknown source symbol" in e for e in global_checks({**with_sidecars, "unresolved": [{**unresolved_rec, "source_symbol_id": "py:a.py::missing"}]}, schema, counter))),
        ("broken dependency path detected", any("importing path not in file inventory" in e for e in global_checks({**with_sidecars, "deps": [{**dependency_rec, "importing_paths": ["missing.py"]}]}, schema, counter))),
        ("duplicate entry point ID detected", any("duplicate entry_id" in e for e in global_checks({**with_sidecars, "entries": [entry_rec, dict(entry_rec)]}, schema, counter))),
        ("malformed file record returns errors instead of crashing", bool(global_checks({**base, "files": [{"file_id": "file:a.py"}]}, schema, counter))),
    ]
    return results


def validate(write_report: bool) -> int:
    """Validate artifacts on disk; optionally render the Markdown report."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    checks: list[tuple[str, bool, str]] = []
    data: dict[str, list[dict]] = {}
    parse_errors: list[str] = []
    for key, rel_path in STREAMS.items():
        path = REPO_ROOT / rel_path
        if not path.is_file():
            parse_errors.append(f"missing artifact: {rel_path}")
            data[key] = []
            continue
        data[key], errors = load_jsonl(path)
        parse_errors.extend(errors)
    checks.append(("All JSONL artifacts exist and every non-empty line is a JSON object", not parse_errors, "; ".join(parse_errors[:5])))
    line_cache: dict[str, int | None] = {}

    def line_count(rel_path: str) -> int | None:
        if rel_path not in line_cache:
            target = REPO_ROOT / rel_path
            line_cache[rel_path] = _line_count_bytes(target.read_bytes()) if target.is_file() and rel_path not in GENERATED_PATHS else None
        return line_cache[rel_path]

    errors = global_checks(data, schema, line_count)
    schema_msgs = [e for e in errors if e.startswith("schema:")]
    other_msgs = [e for e in errors if not e.startswith("schema:")]
    checks.append(("Every primary and auxiliary record validates against schema.json", not schema_msgs, "; ".join(schema_msgs[:5])))
    checks.append(("Cross-record integrity (unique IDs, references, derived IDs, line ranges, evidence paths)", not other_msgs, "; ".join(other_msgs[:5])))
    missing_artifacts = [p for p in GENERATED_PATHS if p != REPORT_MD_PATH and not (REPO_ROOT / p).is_file()]
    checks.append(("Included files exist on disk", not [f["path"] for f in data["files"] if f.get("inventory_disposition") == "included" and f["path"] not in GENERATED_PATHS and not (REPO_ROOT / f["path"]).is_file()] and not missing_artifacts, ""))
    checks.append(("No relation uses resolution 'unresolved' (unresolved items are kept in unresolved.jsonl)", not any(r.get("resolution") == "unresolved" for r in data["relations"]), ""))
    first = generate_outputs()
    second = generate_outputs()
    first_bytes, second_bytes = serialize(first), serialize(second)
    same_runs = first_bytes == second_bytes
    checks.append(("Two consecutive in-memory generations are byte-identical", same_runs, ""))
    stale = [p for p, content in first_bytes.items() if not (REPO_ROOT / p).is_file() or (REPO_ROOT / p).read_bytes() != content]
    checks.append(("Artifacts on disk equal a fresh regeneration (not stale)", not stale, ", ".join(stale)))
    negatives = _negative_self_tests(schema)
    checks.append(("Negative self-tests reject invalid records and broken data sets", all(ok for _, ok in negatives), ", ".join(name for name, ok in negatives if not ok)))
    failed = [name for name, ok, _ in checks if not ok]
    for name, ok, detail in checks:
        LOG.info("%s: %s%s", "PASS" if ok else "FAIL", name, f" ({detail})" if detail and not ok else "")
    for name, ok in negatives:
        LOG.info("  negative test %s: %s", "PASS" if ok else "FAIL", name)
    if write_report:
        text = render_report(first, checks, negatives)
        target = REPO_ROOT / REPORT_MD_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))
        LOG.info("Report written to %s", REPORT_MD_PATH)
    return 1 if failed else 0


def render_report(out: Outputs, checks: list[tuple[str, bool, str]], negatives: list[tuple[str, bool]]) -> str:
    """Render the Markdown coverage and validation report."""
    report = out.report
    counts = report["counts"]
    lines = [
        "# Inventory Coverage and Validation Report", "",
        "Generated by `docs/book/inventory/inventory_tool.py validate --write-report`. Do not edit by hand.",
        "The inventory is static (AST based). Nothing was executed; no record shows that code runs or that a test passes.", "",
        "## Generation", "",
        f"- Tool version: `{report['generator']['version']}`; schema: `{report['schema_id']}`",
        f"- Git revision (HEAD): `{report['git_revision']}`; the working tree was not clean, so the inventory describes the tree on disk",
        f"- Interpreter used for stdlib classification: Python {report['python_version']}",
        f"- Analysis input digest (Python files, `pyproject.toml`, `start.bat`): `{report['analysis_input_digest']}`",
        f"- Regenerate: `{report['regeneration_command']}`; validate: `python docs/book/inventory/inventory_tool.py validate --write-report`", "",
        "## Coverage", "",
        f"- File records: {len(out.files)} ({counts['files_by_disposition'].get('included', 0)} included, {counts['files_by_disposition'].get('excluded', 0)} excluded by category)",
        f"- Python files parsed: {counts['python_files_parsed']}; failed: {counts['python_files_failed']}",
        f"- Symbols: {len(out.symbols)}; relations: {len(out.relations)}; unresolved items: {len(out.unresolved)}",
        f"- Entry points: {len(out.entries)}; dependency records: {len(out.deps)}", "",
        "No total-coverage percentage is claimed: records are `static_analyzed` only, not human-reviewed, editorially approved, or execution-verified.",
        "The generator leaves `docs_cross_reference.jsonl` and `control_flow.jsonl` empty. Claim records in `claims.jsonl` are authored and preserved, not generated; no complete call/control-flow graph is claimed.", "",
        "### Files by kind", "", "| Kind | Count |", "|---|---|",
    ]
    lines += [f"| `{k}` | {v} |" for k, v in counts["files_by_kind"].items()]
    lines += ["", "### Files by Git state", "", "| Git state | Count |", "|---|---|"]
    lines += [f"| `{k}` | {v} |" for k, v in counts["files_by_git_state"].items()]
    lines += ["", "### Symbols by kind", "", "| Kind | Count |", "|---|---|"]
    lines += [f"| `{k}` | {v} |" for k, v in counts["symbols_by_kind"].items()]
    lines += ["", "### Relations by kind and resolution", "", "| Kind / resolution | Count |", "|---|---|"]
    lines += [f"| `{k}` | {v} |" for k, v in counts["relations_by_kind_and_resolution"].items()]
    lines += ["", "### Call sites seen", "", "| Outcome | Count |", "|---|---|"]
    lines += [f"| `{k}` | {v} |" for k, v in counts["call_sites"].items()]
    lines += ["", "`call_sites_builtin_skipped` are calls to Python builtins or methods on literals; they are counted but not recorded.", "",
              "### Unresolved items by reason", "", "| Reason code | Count | Meaning |", "|---|---|---|"]
    lines += [f"| `{k}` | {v} | {REASONS.get(k, '')} |" for k, v in counts["unresolved_by_reason"].items()]
    lines += ["", "## Entry points (static detection, support status unconfirmed)", "", "| ID | Kind | Path |", "|---|---|---|"]
    lines += [f"| `{e['entry_id']}` | `{e['kind']}` | `{e['path']}` |" for e in out.entries if e["kind"] not in {"pytest_module"}]
    lines += ["", f"Additionally {sum(1 for e in out.entries if e['kind'] == 'pytest_module')} `pytest_module` entries (files matching `test_*.py`) are listed in `entry_points.jsonl`.", "",
              "## External dependencies", "", "| Top-level module | Classification | Declared distribution | Import sites | External call sites |", "|---|---|---|---|---|"]
    lines += [f"| `{d['top_level_module'] or d['dep_id']}` | `{d['classification']}` | {d['declared_distribution'] or '-'} | {d['import_site_count']} | {d['external_call_site_count']} |" for d in out.deps if d["classification"] != "stdlib"]
    stdlib = [d["top_level_module"] for d in out.deps if d["classification"] == "stdlib"]
    lines += ["", f"Standard-library modules imported ({len(stdlib)}): " + ", ".join(f"`{m}`" for m in stdlib), "",
              "## Skipped, failed and excluded", "",
              f"- Tracked paths missing on disk: {len(report['skipped']['tracked_paths_missing_on_disk'])}",
              f"- Python files that failed to parse: {len(report['skipped']['python_files_failed'])}",
              f"- Excluded paths (category only, contents not read): {len(report['skipped']['excluded_paths'])}", ""]
    lines += [f"  - `{p}`" for p in report["skipped"]["excluded_paths"]]
    lines += ["", "## Validation results", "", "| Check | Result |", "|---|---|"]
    lines += [f"| {name} | {'PASS' if ok else 'FAIL'} |" for name, ok, _ in checks]
    lines += ["", "Negative self-tests:", ""]
    lines += [f"- {'PASS' if ok else 'FAIL'}: {name}" for name, ok in negatives]
    lines += ["", "## Limitations of the static analysis", ""]
    lines += [f"- {item}" for item in report["limitations"]]
    return "\n".join(lines) + "\n"


def generate() -> int:
    """Write all generated artifacts."""
    out = generate_outputs()
    for rel_path, content in serialize(out).items():
        target = REPO_ROOT / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        LOG.info("wrote %s (%d bytes)", rel_path, len(content))
    LOG.info("files=%d symbols=%d relations=%d unresolved=%d entries=%d deps=%d", len(out.files), len(out.symbols), len(out.relations), len(out.unresolved), len(out.entries), len(out.deps))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate", help="regenerate inventory artifacts")
    check = sub.add_parser("validate", help="validate artifacts and reproducibility")
    check.add_argument("--write-report", action="store_true", help="render progress/inventory_report.md")
    args = parser.parse_args(argv)
    return generate() if args.command == "generate" else validate(args.write_report)


if __name__ == "__main__":
    raise SystemExit(main())
