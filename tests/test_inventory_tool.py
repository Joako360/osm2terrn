"""Regression tests for the technical-book inventory validator."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPOSITORY_ROOT / "docs" / "book" / "inventory" / "inventory_tool.py"
SCHEMA_PATH = TOOL_PATH.with_name("schema.json")
SPEC = importlib.util.spec_from_file_location("osm2terrn_inventory_tool", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
inventory_tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = inventory_tool
SPEC.loader.exec_module(inventory_tool)
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALID_REVISION = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, text=True
).strip()
VALID_TIMESTAMP = "2026-10-20T12:00:00Z"


def _valid_unresolved_record() -> dict:
    return {
        "unresolved_id": "unres:test",
        "category": "call",
        "reason_code": "callee_is_variable",
        "source_symbol_id": "py:sample.py::<module>",
        "path": "sample.py",
        "expression": "callback()",
        "reason": "The callback target is not statically known.",
        "resolution": "unresolved",
        "inventory_status": "inventoried",
        "analysis_status": "static_analyzed",
        "documentation_status": "not_documented",
        "execution_status": "not_verified",
        "evidence": [],
        "uncertainties": [],
        "limitations": [],
    }


class InventorySchemaRegressionTests(unittest.TestCase):
    def _base_data(self, *, disposition: str = "included") -> dict:
        file_record = {
            "file_id": "file:sample.py", "path": "sample.py", "kind": "python_source",
            "git_state": "tracked", "inventory_disposition": disposition,
            "inventory_status": "excluded" if disposition == "excluded" else "inventoried",
            "analysis_status": "static_analyzed", "documentation_status": "not_documented",
            "execution_status": "not_verified", "evidence": [], "uncertainties": [], "limitations": [],
        }
        if disposition == "excluded":
            file_record["exclusion_reason"] = "fixture exclusion"
        module = {
            "symbol_id": "py:sample.py::<module>", "file_id": "file:sample.py", "path": "sample.py",
            "qualified_name": "<module>", "kind": "module", "owner_symbol_id": None,
            "start_line": 1, "end_line": 2, "analysis_status": "static_analyzed",
            "inventory_status": "inventoried", "documentation_status": "not_documented",
            "execution_status": "not_verified", "evidence": [], "uncertainties": [], "limitations": [],
        }
        return {"files": [file_record], "symbols": [module], "relations": [], "xrefs": [],
                "flow": [], "claims": [], "unresolved": [], "entries": [], "deps": []}

    def test_v3_01_inventory_state_must_match_file_disposition(self) -> None:
        data = self._base_data()
        data["files"][0]["inventory_status"] = "excluded"
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: 2)
        self.assertTrue(any("contradicts included disposition" in error for error in errors))
        data = self._base_data(disposition="excluded")
        data["files"][0]["inventory_status"] = "inventoried"
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: 2)
        self.assertTrue(any("excluded disposition requires inventory_status excluded" in error for error in errors))

    def test_v3_01_blocked_and_review_states_require_support(self) -> None:
        blocked = _valid_unresolved_record()
        blocked["analysis_status"] = "blocked"
        data = {"files": [], "symbols": [], "relations": [], "xrefs": [], "flow": [],
                "claims": [], "unresolved": [blocked], "entries": [], "deps": []}
        self.assertTrue(any("blocked requires a recorded reason" in error for error in
                            inventory_tool.global_checks(data, SCHEMA, lambda _path: None)))
        blocked["limitations"] = ["Waiting for an unavailable source file."]
        self.assertFalse(any("blocked requires a recorded reason" in error for error in
                             inventory_tool.global_checks(data, SCHEMA, lambda _path: None)))
        blocked["limitations"] = []
        reviewed = _valid_unresolved_record()
        reviewed["analysis_status"] = "human_reviewed"
        data["unresolved"] = [reviewed]
        self.assertTrue(any("requires passed review evidence" in error for error in
                            inventory_tool.global_checks(data, SCHEMA, lambda _path: None)))
        evidence = {"evidence_id": "ev:review", "path": "sample.py", "type": "review",
                    "description": "Independent review", "review_id": "review:unit-review", "reviewer": "Reviewer",
                    "observed_at": VALID_TIMESTAMP, "repository_revision": VALID_REVISION, "result": "passed"}
        self.assertEqual(inventory_tool.schema_errors([evidence], {"$ref": "#/$defs/evidence"}, SCHEMA), [])
        for field, invalid in (("description", "   "), ("review_id", "review:   "),
                               ("reviewer", "  "), ("observed_at", "yesterday"),
                               ("repository_revision", "x")):
            bad = {**evidence, field: invalid}
            self.assertTrue(inventory_tool.schema_errors([bad], {"$ref": "#/$defs/evidence"}, SCHEMA),
                            (field, invalid))
        impossible_date = {**evidence, "observed_at": "2026-02-30T12:00:00Z"}
        reviewed_file = self._base_data()
        reviewed_file["files"][0]["evidence"] = [impossible_date]
        self.assertTrue(any("valid UTC calendar timestamp" in error for error in
                            inventory_tool.global_checks(reviewed_file, SCHEMA, lambda _path: 2)))
        unknown_commit = {**evidence, "repository_revision": "0" * 40}
        reviewed_file["files"][0]["evidence"] = [unknown_commit]
        self.assertTrue(any("not an available Git commit" in error for error in
                            inventory_tool.global_checks(reviewed_file, SCHEMA, lambda _path: 2)))
        evidence.pop("reviewer")
        self.assertTrue(any("reviewer" in error for error in inventory_tool.schema_errors(
            [evidence], {"$ref": "#/$defs/evidence"}, SCHEMA)))
        data = self._base_data()
        data["files"][0]["documentation_status"] = "approved"
        self.assertTrue(any("requires passed review evidence" in error for error in
                            inventory_tool.global_checks(data, SCHEMA, lambda _path: 2)))
        data["files"][0]["evidence"] = [{**evidence, "reviewer": "Reviewer"}]
        self.assertEqual(inventory_tool.global_checks(data, SCHEMA, lambda _path: 2), [])
        blocked["uncertainties"] = ["   "]
        self.assertTrue(inventory_tool.global_checks(
            {"files": [], "symbols": [], "relations": [], "xrefs": [], "flow": [],
             "claims": [], "unresolved": [blocked], "entries": [], "deps": []},
            SCHEMA, lambda _path: None))

    def test_v3_02_runtime_relation_requires_real_passed_observation(self) -> None:
        data = self._base_data()
        relation = {
            "relation_id": inventory_tool._rel_id("calls", "py:sample.py::<module>", "py:sample.py::<module>", "runtime_observed"),
            "source_symbol_id": "py:sample.py::<module>", "target_symbol_id": "py:sample.py::<module>",
            "kind": "calls", "resolution": "runtime_observed", "analysis_status": "static_analyzed",
            "inventory_status": "inventoried", "documentation_status": "not_documented",
            "execution_status": "not_verified", "evidence": [{"evidence_id": "ev:src", "path": "sample.py",
                "type": "source", "description": "Static source"}], "uncertainties": [], "limitations": [],
        }
        data["relations"] = [relation]
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: 2)
        self.assertTrue(any("runtime_observed requires passed execution_status" in error for error in errors))
        relation["execution_status"] = "passed"
        runtime_evidence = {"evidence_id": "ev:runtime", "path": "sample.py", "type": "runtime_observation",
            "description": "Observed call", "command": "python -m unittest", "environment": "Python 3.12",
            "result": "passed", "repository_revision": VALID_REVISION, "observed_at": VALID_TIMESTAMP}
        self.assertEqual(inventory_tool.schema_errors([runtime_evidence], {"$ref": "#/$defs/evidence"}, SCHEMA), [])
        incomplete_runtime = dict(runtime_evidence)
        incomplete_runtime.pop("command")
        self.assertTrue(inventory_tool.schema_errors([incomplete_runtime], {"$ref": "#/$defs/evidence"}, SCHEMA))
        relation["evidence"] = [{"evidence_id": "ev:runtime", "path": "sample.py", "type": "runtime_observation",
            "description": "Observed call", "command": "python -m unittest", "environment": "Python 3.12",
            "result": "passed", "repository_revision": VALID_REVISION, "observed_at": VALID_TIMESTAMP}]
        self.assertEqual(inventory_tool.global_checks(data, SCHEMA, lambda _path: 2), [])
        for field, invalid in (("command", "  "), ("environment", ""),
                               ("description", "  "), ("repository_revision", "x"),
                               ("observed_at", "yesterday")):
            bad = {**runtime_evidence, field: invalid}
            self.assertTrue(inventory_tool.schema_errors([bad], {"$ref": "#/$defs/evidence"}, SCHEMA),
                            (field, invalid))
        relation["execution_status"] = "failed"
        self.assertTrue(any("contradicts execution_status" in error for error in
                            inventory_tool.global_checks(data, SCHEMA, lambda _path: 2)))
        relation["execution_status"] = "passed"

    def test_v3_03_control_flow_ranges_are_bounded(self) -> None:
        data = self._base_data()
        flow = {"control_id": "flow:sample:if:1", "source_symbol_id": "py:sample.py::<module>",
            "path": "sample.py", "start_line": 1, "end_line": 3, "kind": "conditional_branch",
            "condition": "ready", "resolution": "static", "inventory_status": "inventoried",
            "analysis_status": "static_analyzed", "documentation_status": "not_documented",
            "execution_status": "not_verified", "evidence": [], "uncertainties": [], "limitations": []}
        data["flow"] = [flow]
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: 2)
        self.assertTrue(any("exceeds 2 lines" in error for error in errors))
        flow["start_line"], flow["end_line"] = 2, 1
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: 2)
        self.assertTrue(any("invalid line range 2-1" in error for error in errors))
        flow["start_line"] = 1
        flow["end_line"] = 2
        self.assertEqual(inventory_tool.global_checks(data, SCHEMA, lambda _path: 2), [])
        self.assertTrue(any("cannot be verified on disk" in error for error in
                            inventory_tool.global_checks(data, SCHEMA, lambda _path: None)))
        self.assertEqual(inventory_tool._line_count_bytes(b"one\ntwo\n"), 2)
        self.assertEqual(inventory_tool._line_count_bytes(b"one\ntwo"), 2)
        self.assertEqual(inventory_tool._line_count_bytes(b"one\r\ntwo\r\n"), 2)
        self.assertEqual(inventory_tool._line_count_bytes(b""), 0)
        self.assertEqual(inventory_tool._line_count_bytes(b"one\rtwo\r"), 2)

    def test_v3_03_physical_line_ranges_match_temp_files(self) -> None:
        samples = {
            "empty": (b"", 0), "lf": (b"one\ntwo\n", 2),
            "crlf": (b"one\r\ntwo\r\n", 2), "cr": (b"one\rtwo\r", 2),
            "no_final": (b"one\ntwo", 2), "single": (b"one", 1),
        }
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            for name, (content, expected) in samples.items():
                path = Path(directory) / f"{name}.py"
                path.write_bytes(content)
                relative_path = path.relative_to(REPOSITORY_ROOT).as_posix()
                count = inventory_tool._line_count_bytes(path.read_bytes())
                self.assertEqual(count, expected, name)
                data = self._base_data()
                data["files"][0]["file_id"] = f"file:{relative_path}"
                data["files"][0]["path"] = relative_path
                data["symbols"][0]["symbol_id"] = f"py:{relative_path}::<module>"
                data["symbols"][0]["file_id"] = f"file:{relative_path}"
                data["symbols"][0]["path"] = relative_path
                data["symbols"][0]["start_line"] = 1 if count else None
                data["symbols"][0]["end_line"] = count if count else None
                line_count = lambda requested, source_path=relative_path: inventory_tool._line_count_bytes(
                    (REPOSITORY_ROOT / requested).read_bytes()
                ) if requested == source_path else None
                if expected == 0:
                    self.assertEqual(inventory_tool.global_checks(data, SCHEMA, line_count), [], name)
                    flow = {"control_id": f"flow:{name}:if:1", "source_symbol_id": f"py:{relative_path}::<module>",
                        "path": relative_path, "start_line": 1, "end_line": 1, "kind": "conditional_branch",
                        "condition": "ready", "resolution": "static", "inventory_status": "inventoried",
                        "analysis_status": "static_analyzed", "documentation_status": "not_documented",
                        "execution_status": "not_verified", "evidence": [], "uncertainties": [], "limitations": []}
                    data["flow"] = [flow]
                    self.assertTrue(any("exceeds 0 lines" in error for error in inventory_tool.global_checks(
                        data, SCHEMA, line_count)))
                else:
                    flow = {"control_id": f"flow:{name}:if:1", "source_symbol_id": f"py:{relative_path}::<module>",
                        "path": relative_path, "start_line": 1, "end_line": count, "kind": "conditional_branch",
                        "condition": "ready", "resolution": "static", "inventory_status": "inventoried",
                        "analysis_status": "static_analyzed", "documentation_status": "not_documented",
                        "execution_status": "not_verified", "evidence": [], "uncertainties": [], "limitations": []}
                    data["flow"] = [flow]
                    self.assertEqual(inventory_tool.global_checks(data, SCHEMA, line_count), [], name)
                    flow["end_line"] = count + 1
                    self.assertTrue(any("exceeds" in error for error in inventory_tool.global_checks(
                        data, SCHEMA, line_count)), name)

    def test_v3_04_resolved_reference_rejects_excluded_but_keeps_unknown(self) -> None:
        data = self._base_data(disposition="excluded")
        xref = {"reference_id": "xref:chapter:1", "documentation_path": "sample.py",
            "original_reference": "sample implementation", "status": "resolved", "target_path": "sample.py",
            "inventory_status": "inventoried", "analysis_status": "static_analyzed",
            "documentation_status": "not_documented", "execution_status": "not_verified",
            "evidence": [], "uncertainties": [], "limitations": []}
        data["xrefs"] = [xref]
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: 2)
        self.assertTrue(any("resolved target is excluded" in error for error in errors))
        data = self._base_data()
        data["xrefs"] = [xref]
        self.assertEqual(inventory_tool.global_checks(data, SCHEMA, lambda _path: 2), [])
        self.assertTrue(any("cannot be verified on disk" in error for error in
                            inventory_tool.global_checks(data, SCHEMA, lambda _path: None)))
        del xref["target_path"]
        xref["status"] = "unknown"
        data["files"][0]["inventory_disposition"] = "excluded"
        data["files"][0]["inventory_status"] = "excluded"
        data["files"][0]["exclusion_reason"] = "fixture exclusion"
        self.assertEqual(inventory_tool.global_checks(data, SCHEMA, lambda _path: 2), [])
        xref["status"] = "unverifiable"
        self.assertEqual(inventory_tool.global_checks(data, SCHEMA, lambda _path: 2), [])
        xref["status"] = "expected_missing"
        self.assertEqual(inventory_tool.global_checks(data, SCHEMA, lambda _path: 2), [])
        xref["target_symbol_id"] = "py:sample.py::missing"
        for status in ("unknown", "unverifiable", "expected_missing"):
            xref["status"] = status
            self.assertTrue(any("unknown target symbol" in error for error in
                                inventory_tool.global_checks(data, SCHEMA, lambda _path: 2)), status)
        xref["target_symbol_id"] = "py:sample.py::<module>"
        xref["status"] = "unknown"
        self.assertEqual(inventory_tool.global_checks(data, SCHEMA, lambda _path: 2), [])

    def test_work_status_axes_are_independent_and_enumerated(self) -> None:
        record = _valid_unresolved_record()
        record["documentation_status"] = "runtime_verified"
        errors = inventory_tool.schema_errors(
            record, {"$ref": "#/$defs/unresolvedRecord"}, SCHEMA
        )
        self.assertTrue(any("documentation_status" in error for error in errors))

    def test_test_execution_evidence_requires_reproducible_context(self) -> None:
        evidence = {
            "evidence_id": "ev:test-run", "path": "tests/test_sample.py",
            "type": "test_execution", "description": "Focused test run",
            "command": "python -m unittest", "test_id": "tests.test_sample.TestExample.test_ok",
            "environment": "Python 3.12 on Windows", "result": "passed",
            "repository_revision": VALID_REVISION, "observed_at": VALID_TIMESTAMP,
        }
        errors = inventory_tool.schema_errors([evidence], {"$ref": "#/$defs/evidence"}, SCHEMA)
        self.assertEqual(errors, [])
        evidence.pop("test_id")
        errors = inventory_tool.schema_errors([evidence], {"$ref": "#/$defs/evidence"}, SCHEMA)
        self.assertTrue(any("test_id" in error for error in errors))

    def test_control_flow_contract_requires_branch_condition(self) -> None:
        record = {
            "control_id": "flow:sample:if:1", "source_symbol_id": "py:sample.py::run",
            "path": "sample.py", "start_line": 1, "end_line": 2,
            "kind": "conditional_branch", "resolution": "static",
            "inventory_status": "inventoried", "analysis_status": "static_analyzed",
            "documentation_status": "not_documented", "execution_status": "not_verified",
            "evidence": [], "uncertainties": [], "limitations": [],
        }
        errors = inventory_tool.schema_errors(record, {"$ref": "#/$defs/controlFlowRecord"}, SCHEMA)
        self.assertTrue(any("condition" in error for error in errors))
        record["condition"] = "ready"
        self.assertEqual(inventory_tool.schema_errors(record, {"$ref": "#/$defs/controlFlowRecord"}, SCHEMA), [])

    def test_unknown_documentation_reference_needs_no_target_path(self) -> None:
        record = {
            "reference_id": "xref:chapter:claim-1", "documentation_path": "docs/chapter.md",
            "original_reference": "implementation details for the loader", "status": "unknown",
            "inventory_status": "inventoried", "analysis_status": "static_analyzed",
            "documentation_status": "not_documented", "execution_status": "not_verified",
            "evidence": [], "uncertainties": [], "limitations": [],
        }
        self.assertEqual(inventory_tool.schema_errors(record, {"$ref": "#/$defs/documentationReferenceRecord"}, SCHEMA), [])
        record["status"] = "resolved"
        errors = inventory_tool.schema_errors(record, {"$ref": "#/$defs/documentationReferenceRecord"}, SCHEMA)
        self.assertTrue(any("target_path" in error for error in errors))

    def test_claim_evidence_foreign_key_and_execution_status_are_checked(self) -> None:
        file_record = {
            "file_id": "file:chapter.md", "path": "chapter.md", "kind": "documentation",
            "git_state": "tracked", "inventory_disposition": "included",
            "inventory_status": "inventoried", "analysis_status": "static_analyzed",
            "documentation_status": "draft", "execution_status": "not_verified",
            "evidence": [{"evidence_id": "ev:source", "path": "chapter.md", "type": "documentation", "description": "Chapter source"}],
            "uncertainties": [], "limitations": [],
        }
        claim = {
            "claim_id": "claim:chapter:1", "chapter_path": "chapter.md",
            "statement": "A documented assertion.", "evidence_ids": ["ev:source"],
            "inventory_status": "inventoried", "analysis_status": "static_analyzed",
            "documentation_status": "draft", "execution_status": "not_verified",
            "evidence": [], "uncertainties": [], "limitations": [],
        }
        data = {
            "files": [file_record], "symbols": [], "relations": [], "xrefs": [],
            "flow": [], "claims": [claim], "unresolved": [], "entries": [], "deps": [],
        }
        self.assertEqual(inventory_tool.global_checks(data, SCHEMA, lambda _path: None), [])
        claim["evidence_ids"] = ["ev:missing"]
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: None)
        self.assertTrue(any("unknown evidence IDs" in error for error in errors))
        claim["evidence_ids"] = ["ev:source"]
        claim["execution_status"] = "passed"
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: None)
        self.assertTrue(any("requires matching execution evidence" in error for error in errors))

    def test_generation_preserves_authored_claim_records(self) -> None:
        claim = {
            "claim_id": "claim:sample:stable",
            "chapter_path": "docs/book/chapters/sample.md",
            "statement": "A stable authored claim.",
            "evidence_ids": ["ev:sample-source"],
            "inventory_status": "inventoried",
            "analysis_status": "static_analyzed",
            "documentation_status": "draft",
            "execution_status": "not_verified",
            "evidence": [{
                "evidence_id": "ev:sample-source",
                "path": "sample.py",
                "symbol_id": "py:sample.py::run",
                "start_line": 4,
                "end_line": 8,
                "type": "source",
                "description": "Source for the claim.",
            }],
            "uncertainties": [],
            "limitations": [],
        }
        second_claim = {**claim, "claim_id": "claim:sample:second", "statement": "A second authored claim."}
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            claims_path = root / inventory_tool.STREAMS["claims"]
            claims_path.parent.mkdir(parents=True)
            claims_path.write_text(
                json.dumps(claim) + "\n" + json.dumps(second_claim) + "\n",
                encoding="utf-8",
            )
            empty_outputs = inventory_tool.Outputs([], [], [], [], [], [], {})

            with (
                patch.object(inventory_tool, "REPO_ROOT", root),
                patch.object(inventory_tool, "Inventory") as inventory_class,
            ):
                inventory_class.return_value.outputs.return_value = empty_outputs
                self.assertEqual(inventory_tool.generate(), 0)

            generated_claims = [
                json.loads(line)
                for line in claims_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(generated_claims, [claim, second_claim])
            self.assertEqual(len(generated_claims), 2)
            self.assertEqual(
                len({item["claim_id"] for item in generated_claims}),
                2,
            )

    def test_generation_rejects_duplicate_json_object_keys_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            claims_path = root / inventory_tool.STREAMS["claims"]
            claims_path.parent.mkdir(parents=True)
            claims_path.write_text(
                '{"claim_id":"claim:sample:first","claim_id":"claim:sample:second"}\n',
                encoding="utf-8",
            )
            generated_path = root / inventory_tool.STREAMS["files"]
            generated_path.parent.mkdir(parents=True, exist_ok=True)
            generated_path.write_text("keep this prior artifact\n", encoding="utf-8")
            empty_outputs = inventory_tool.Outputs([], [], [], [], [], [], {})

            with (
                patch.object(inventory_tool, "REPO_ROOT", root),
                patch.object(inventory_tool, "Inventory") as inventory_class,
            ):
                inventory_class.return_value.outputs.return_value = empty_outputs
                with self.assertRaisesRegex(ValueError, "duplicate object key 'claim_id'"):
                    inventory_tool.generate()

            self.assertEqual(generated_path.read_text(encoding="utf-8"), "keep this prior artifact\n")

    def test_evidence_symbol_reference_must_exist_in_same_file(self) -> None:
        # A focused fixture exercises evidence-to-symbol integrity independently
        # of the generator's repository scan.
        file_record = {
            "file_id": "file:sample.py", "path": "sample.py", "kind": "python_source",
            "git_state": "tracked", "inventory_disposition": "included",
            "inventory_status": "inventoried", "analysis_status": "static_analyzed",
            "documentation_status": "not_documented", "execution_status": "not_verified",
            "evidence": [], "uncertainties": [], "limitations": [],
        }
        module = {
            "symbol_id": "py:sample.py::<module>", "file_id": "file:sample.py",
            "path": "sample.py", "qualified_name": "<module>", "kind": "module",
            "owner_symbol_id": None, "start_line": 1, "end_line": 10,
            "analysis_status": "static_analyzed", "inventory_status": "inventoried",
            "documentation_status": "not_documented", "execution_status": "not_verified",
            "evidence": [], "uncertainties": [], "limitations": [],
        }
        claim = {
            "claim_id": "claim:sample:locator", "chapter_path": "sample.md",
            "statement": "A located assertion.", "evidence_ids": ["ev:locator"],
            "inventory_status": "inventoried", "analysis_status": "static_analyzed",
            "documentation_status": "draft", "execution_status": "not_verified",
            "evidence": [{
                "evidence_id": "ev:locator", "path": "sample.py",
                "symbol_id": "py:sample.py::missing", "start_line": 2, "end_line": 3,
                "type": "source", "description": "Located source.",
            }],
            "uncertainties": [], "limitations": [],
        }
        chapter = {
            "file_id": "file:sample.md", "path": "sample.md", "kind": "documentation",
            "git_state": "tracked", "inventory_disposition": "included",
            "inventory_status": "inventoried", "analysis_status": "static_analyzed",
            "documentation_status": "draft", "execution_status": "not_verified",
            "evidence": [], "uncertainties": [], "limitations": [],
        }
        other_file = {
            **file_record,
            "file_id": "file:other.py",
            "path": "other.py",
            "kind": "python_source",
        }
        other_module = {
            **module,
            "symbol_id": "py:other.py::<module>",
            "file_id": "file:other.py",
            "path": "other.py",
        }
        data = {
            "files": [file_record, chapter, other_file], "symbols": [module, other_module], "relations": [],
            "xrefs": [], "flow": [], "claims": [claim], "unresolved": [], "entries": [], "deps": [],
        }
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: 10)
        self.assertTrue(any("evidence references unknown symbol" in error for error in errors))
        claim["evidence"][0]["symbol_id"] = "py:sample.py::<module>"
        self.assertEqual(inventory_tool.global_checks(data, SCHEMA, lambda _path: 10), [])
        claim["evidence"][0]["start_line"] = 2
        claim["evidence"][0]["end_line"] = 11
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: 11)
        self.assertTrue(any("outside symbol" in error for error in errors))
        claim["evidence"][0]["end_line"] = 3
        claim["evidence"][0]["symbol_id"] = "py:other.py::<module>"
        errors = inventory_tool.global_checks(data, SCHEMA, lambda _path: 10)
        self.assertTrue(any("evidence symbol" in error and "is not in sample.py" in error for error in errors))

    def test_unresolved_record_requires_reason(self) -> None:
        record = _valid_unresolved_record()
        record.pop("reason")

        errors = inventory_tool.schema_errors(
            record, {"$ref": "#/$defs/unresolvedRecord"}, SCHEMA
        )

        self.assertTrue(any("missing required 'reason'" in error for error in errors))

    def test_entry_point_rejects_unknown_support_status(self) -> None:
        record = {
            "entry_id": "entry:sample",
            "kind": "main_guard",
            "path": "sample.py",
            "start_line": 1,
            "target_symbol_id": None,
            "target_expression": None,
            "invocation": "python sample.py",
            "static_call_targets": [],
            "support_status": "bogus",
            "inventory_status": "inventoried", "analysis_status": "static_analyzed",
            "documentation_status": "not_documented", "execution_status": "not_verified",
            "evidence": [],
            "uncertainties": [],
            "limitations": [],
        }

        errors = inventory_tool.schema_errors(
            record, {"$ref": "#/$defs/entryPointRecord"}, SCHEMA
        )

        self.assertTrue(any("support_status" in error for error in errors))

    def test_external_dependency_requires_typed_counts_and_classification(self) -> None:
        record = {
            "dep_id": "dep:sample",
            "top_level_module": "sample",
            "classification": "invented",
            "declared_distribution": None,
            "declared_in": [],
            "importing_paths": [],
            "import_site_count": "many",
            "external_call_site_count": 0,
            "inventory_status": "inventoried", "analysis_status": "static_analyzed",
            "documentation_status": "not_documented", "execution_status": "not_verified",
            "evidence": [],
            "uncertainties": [],
            "limitations": [],
        }

        errors = inventory_tool.schema_errors(
            record, {"$ref": "#/$defs/externalDependencyRecord"}, SCHEMA
        )

        self.assertTrue(any("classification" in error for error in errors))
        self.assertTrue(any("import_site_count" in error for error in errors))

    def test_global_validation_reports_malformed_records_without_crashing(self) -> None:
        malformed = {
            "files": [{"file_id": "file:sample.py"}],
            "symbols": [],
            "relations": [],
            "xrefs": [],
            "unresolved": [],
            "entries": [],
            "deps": [],
        }

        errors = inventory_tool.global_checks(malformed, SCHEMA, lambda _path: None)

        self.assertTrue(errors)
        self.assertTrue(any("missing required 'path'" in error for error in errors))

    def test_jsonl_loader_reports_invalid_utf8_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "broken.jsonl"
            path.write_bytes(b"{\xff}\n")

            records, errors = inventory_tool.load_jsonl(path)

        self.assertEqual(records, [])
        self.assertTrue(any("UTF-8 JSONL" in error for error in errors))


class InventoryGitDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_directory.name)
        self.original_repo_root = inventory_tool.REPO_ROOT
        inventory_tool.REPO_ROOT = self.repo_root
        self._git("init", "-q")
        self._git("config", "user.email", "inventory-test@example.invalid")
        self._git("config", "user.name", "Inventory Test")
        (self.repo_root / ".gitignore").write_bytes((REPOSITORY_ROOT / ".gitignore").read_bytes())

    def tearDown(self) -> None:
        inventory_tool.REPO_ROOT = self.original_repo_root
        self.temp_directory.cleanup()

    def _git(self, *args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=self.repo_root, check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    def test_ignored_package_source_is_inventoried_but_nested_venv_is_excluded(self) -> None:
        package_source = self.repo_root / "osm2terrn" / "cache" / "manager.py"
        package_source.parent.mkdir(parents=True)
        package_source.write_text("VALUE = 1\n", encoding="utf-8")
        private_source = self.repo_root / "osm2terrn" / ".venv" / "site-packages" / "private.py"
        private_source.parent.mkdir(parents=True)
        private_source.write_text("SECRET = 'must not be parsed'\n", encoding="utf-8")
        self._git("add", ".gitignore")
        self._git("commit", "-qm", "Add ignore rules")

        entries, _missing = inventory_tool.collect_paths()
        by_path = {entry.path: entry for entry in entries}

        self.assertIn("osm2terrn/cache/manager.py", by_path)
        self.assertFalse(by_path["osm2terrn/cache/manager.py"].excluded)
        self.assertIn("osm2terrn/.venv", by_path)
        self.assertTrue(by_path["osm2terrn/.venv"].excluded)
        self.assertNotIn("osm2terrn/.venv/site-packages/private.py", by_path)

    def test_porcelain_z_rename_with_spaces_marks_destination(self) -> None:
        old_path = self.repo_root / "old source.py"
        old_path.write_text("VALUE = 1\n", encoding="utf-8")
        self._git("add", ".gitignore", "old source.py")
        self._git("commit", "-qm", "Add source")
        self._git("mv", "old source.py", "renamed source.py")

        modified = inventory_tool._modified_paths()

        self.assertIn("renamed source.py", modified)
        self.assertNotIn("old source.py", modified)
        entries, missing = inventory_tool.collect_paths()
        by_path = {entry.path: entry for entry in entries}
        self.assertEqual(by_path["renamed source.py"].git_state, "modified")
        self.assertNotIn("old source.py", by_path)
        self.assertNotIn("old source.py", missing)

    def test_modified_deleted_and_untracked_files_are_distinguished(self) -> None:
        modified_file = self.repo_root / "modified.py"
        deleted_file = self.repo_root / "deleted.py"
        modified_file.write_text("VALUE = 1\n", encoding="utf-8")
        deleted_file.write_text("VALUE = 2\n", encoding="utf-8")
        self._git("add", ".gitignore", "modified.py", "deleted.py")
        self._git("commit", "-qm", "Add tracked files")
        modified_file.write_text("VALUE = 3\n", encoding="utf-8")
        deleted_file.unlink()
        untracked_file = self.repo_root / "new file.py"
        untracked_file.write_text("VALUE = 4\n", encoding="utf-8")

        entries, missing = inventory_tool.collect_paths()
        by_path = {entry.path: entry for entry in entries}

        self.assertEqual(by_path["modified.py"].git_state, "modified")
        self.assertEqual(by_path["new file.py"].git_state, "untracked")
        self.assertIn("deleted.py", missing)


if __name__ == "__main__":
    unittest.main()
