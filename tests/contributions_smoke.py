#!/usr/bin/env python3
"""Contribution evidence/attribution checks; no models or scoring benchmark."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from contributions import record, report, validate_ledger


def event(**changes):
    value = {"id": "route", "task": "parser-fix", "persona": "rebel", "mode": "perspective",
             "actor": "maverick", "trigger": "Two repairs did not change the result.",
             "kind": "direction", "contribution": "Check the input contract first.",
             "status": "proposed", "outcome": "", "evidence": [], "impact": None}
    value.update(changes)
    return value


class Contributions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="maverick contributions ")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.ledger = self.project / ".maverick/contributions.jsonl"

    def test_revision_appends_and_report_uses_latest_confirmed_result(self):
        record(self.project, event())
        original = self.ledger.read_bytes()
        result = record(self.project, event(status="confirmed", outcome="Removed the incorrect fallback.",
                                           evidence=["src/parser.py: normalize_input"], impact=3,
                                           shift={"before": "The parser is broken.", "after": "The caller supplies the wrong shape."}))
        self.assertTrue(result["revision"])
        self.assertTrue(self.ledger.read_bytes().startswith(original))
        self.assertEqual(len(self.ledger.read_text().splitlines()), 2)
        self.assertEqual(validate_ledger(self.project), [])
        text = report(self.project, "parser-fix")
        self.assertIn("3 · 关键", text)
        self.assertNotIn("待验证建议", text)
        self.assertEqual(text.count("Check the input contract first."), 1)
        self.assertIn("Maverick 采用 Rebel 视角（主对话，非子 Agent）", text)
        self.assertIn("| Maverick | 主对话采用了其他人格视角", text)
        self.assertIn("不重复计分", text)
        self.assertIn("The caller supplies the wrong shape.", text)

    def test_unconfirmed_work_cannot_receive_credit(self):
        for index, status in enumerate(("proposed", "unknown", "not_adopted")):
            record(self.project, event(id=str(index), status=status, outcome="No confirmed effect."))
        text = report(self.project, "parser-fix")
        self.assertNotIn("1 · 辅助", text)
        self.assertNotIn("2 · 实质", text)
        self.assertNotIn("3 · 关键", text)
        self.assertIn("无已记录、已确认的关键思维转变", text)
        before = self.ledger.read_bytes()
        with self.assertRaises(ValueError):
            record(self.project, event(status="proposed", impact=3))
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_subagent_identity_and_task_scope_are_not_inferred(self):
        record(self.project, event(id="experiment", persona="scientist", mode="native_subagent",
                                   actor="thread-actual-7", reused=True, kind="correction", status="confirmed",
                                   outcome="Rejected the original diagnosis.", evidence=["run: minimal repro exit 0"], impact=2))
        record(self.project, event(task="unrelated-task", contribution="Keep this other task out of the report."))
        text = report(self.project, "parser-fix")
        self.assertIn("原生人格子 Agent：thread-actual-7，复用", text)
        self.assertNotIn("Keep this other task", text)
        self.assertIn("| Rebel | 未记录参与", text)
        before = self.ledger.read_bytes()
        with self.assertRaises(ValueError):
            record(self.project, event(id="experiment", persona="rebel", mode="native_subagent", actor="thread-actual-7"))
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_invalid_schema_and_damaged_ledger_leave_file_unchanged(self):
        invalid = (event(mode="direct"), event(mode="native_subagent"),
                   event(status="confirmed", impact=2, evidence=[]), event(evidence="not a list"),
                   event(reused=True), event(status="confirmed", impact=True, outcome="x", evidence=["x"]))
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                record(self.project, item)
        self.assertFalse(self.ledger.exists())
        record(self.project, event())
        with self.ledger.open("a") as target:
            target.write("{broken json\n")
        before = self.ledger.read_bytes()
        self.assertIn("line 2", validate_ledger(self.project)[0])
        with self.assertRaises(ValueError):
            record(self.project, event(id="new"))
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_text_is_escaped_and_external_symlink_is_rejected(self):
        record(self.project, event(contribution="x | y\n<script>bad</script> [fake](url)"))
        text = report(self.project, "parser-fix")
        self.assertIn("x \\| y &lt;script&gt;bad&lt;/script&gt; \\[fake\\]", text)
        self.assertIn("本任务没有贡献记录", report(self.project, "missing-task"))
        self.ledger.unlink()
        with tempfile.TemporaryDirectory() as external:
            outside = Path(external) / "ledger.jsonl"
            outside.write_text("do not change")
            self.ledger.symlink_to(outside)
            with self.assertRaises(ValueError):
                record(self.project, event())
            self.assertEqual(outside.read_text(), "do not change")


if __name__ == "__main__":
    unittest.main(verbosity=2)
