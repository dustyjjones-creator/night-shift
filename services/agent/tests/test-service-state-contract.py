#!/usr/bin/env python3

import copy
import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path("/home/dusty/night-shift").resolve()
AGENT_ROOT = PROJECT_ROOT / "services" / "agent"
FIXTURE_DIR = AGENT_ROOT / "fixtures" / "service_state"

if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from lib.service_state_contract import validate_service_state


class ServiceStateContractTests(unittest.TestCase):

    def load_fixture(self, name):
        with (FIXTURE_DIR / name).open(encoding="utf-8") as file:
            return json.load(file)

    def test_valid_fixtures_are_accepted(self):
        for fixture in [
            "healthy-ollama.json",
            "degraded-forwarder.json",
            "stopped-n8n-ai-pipeline.json",
            "unavailable-forwarder.json",
        ]:
            with self.subTest(fixture=fixture):
                self.assertEqual(validate_service_state(self.load_fixture(fixture)), [])

    def test_unknown_fields_are_rejected(self):
        record = self.load_fixture("healthy-ollama.json")
        record["unexpected_field"] = "value"
        self.assertIn("Unknown field: unexpected_field.", validate_service_state(record))

    def test_missing_required_fields_are_rejected(self):
        record = self.load_fixture("healthy-ollama.json")
        del record["service_role"]
        self.assertIn("Missing required field: service_role.", validate_service_state(record))

    def test_invalid_enum_values_are_rejected(self):
        record = self.load_fixture("healthy-ollama.json")
        record["observed_state"] = "running"
        self.assertIn("observed_state is invalid.", validate_service_state(record))

    def test_sensitive_prohibited_fields_are_rejected(self):
        record = self.load_fixture("healthy-ollama.json")
        record["environment_variables"] = {"secret": "fictional"}
        self.assertIn("Prohibited field: environment_variables.", validate_service_state(record))

    def test_free_form_raw_output_is_rejected(self):
        record = self.load_fixture("healthy-ollama.json")
        record["raw_output"] = "fictional service output"
        self.assertIn("Prohibited field: raw_output.", validate_service_state(record))

    def test_reason_is_only_allowed_when_collection_is_unavailable(self):
        record = copy.deepcopy(self.load_fixture("healthy-ollama.json"))
        record["reason_unavailable"] = "Not applicable."
        self.assertIn(
            "reason_unavailable is only allowed for unavailable collection.",
            validate_service_state(record),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
