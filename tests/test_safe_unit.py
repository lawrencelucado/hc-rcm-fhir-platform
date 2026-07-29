"""Dependency-free tests that never contact the homelab."""

from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MIRTH = load_module("mirth_integration", "tests/test_mirth_integration.py")
SMART = load_module("smart_gateway", "tests/test_smart_gateway.py")


class HL7UnitTests(unittest.TestCase):
    def test_hl7_uses_carriage_return_segment_delimiters(self) -> None:
        message = MIRTH.hl7("MSH|example", "PID|example")
        self.assertEqual(message, "MSH|example\rPID|example\r")

    def test_ack_code_extracts_acceptance(self) -> None:
        response = "MSH|^~\\&|MIRTH\rMSA|AA|ADT0001\r"
        self.assertEqual(MIRTH.ack_code(response), "AA")

    def test_ack_code_rejects_response_without_msa(self) -> None:
        with self.assertRaises(AssertionError):
            MIRTH.ack_code("MSH|^~\\&|MIRTH\r")


class LiveTestGateTests(unittest.TestCase):
    def test_mirth_live_test_fails_closed(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                MIRTH.require_live_test_acknowledgement()

    def test_smart_live_test_fails_closed(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                SMART.require_live_test_acknowledgement()


if __name__ == "__main__":
    unittest.main()
