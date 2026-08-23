#!/usr/bin/env python3

import importlib.util
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path("/home/dusty/night-shift").resolve()
WRAPPER_PATH = PROJECT_ROOT / "services/agent/bin/run-agent-command.py"


spec = importlib.util.spec_from_file_location(
    "run_agent_command",
    WRAPPER_PATH,
)

module = importlib.util.module_from_spec(spec)
sys.modules["run_agent_command"] = module
spec.loader.exec_module(module)


class PolicyTests(unittest.TestCase):

    def check_allowed(self, command):
        allowed, reason = module.command_is_allowed(
            command,
            PROJECT_ROOT,
        )

        self.assertTrue(
            allowed,
            msg=f"Expected allowed: {command}\nReason: {reason}",
        )

    def check_blocked(self, command):
        allowed, reason = module.command_is_allowed(
            command,
            PROJECT_ROOT,
        )

        self.assertFalse(
            allowed,
            msg=f"Expected blocked: {command}",
        )

    # ------------------------------------------------------------
    # Safe commands
    # ------------------------------------------------------------

    def test_git_status_allowed(self):
        self.check_allowed(["git", "status", "--short"])

    def test_git_log_allowed(self):
        self.check_allowed(["git", "log", "--oneline"])

    def test_ls_project_path_allowed(self):
        self.check_allowed(["ls", "services"])

    def test_find_safe_allowed(self):
        self.check_allowed([
            "find",
            "services",
            "-maxdepth",
            "2",
            "-type",
            "f",
        ])

    def test_sed_print_only_allowed(self):
        self.check_allowed([
            "sed",
            "-n",
            "1,20p",
            "README.md",
        ])

    def test_grep_with_file_allowed(self):
        self.check_allowed([
            "grep",
            "TODO",
            "README.md",
        ])

    def test_rg_with_file_allowed(self):
        self.check_allowed([
            "rg",
            "TODO",
            "README.md",
        ])

    def test_journalctl_bounded_allowed(self):
        self.check_allowed([
            "journalctl",
            "-u",
            "ollama",
            "-n",
            "20",
            "--no-pager",
        ])

    # ------------------------------------------------------------
    # Mutation attempts
    # ------------------------------------------------------------

    def test_touch_blocked(self):
        self.check_blocked([
            "touch",
            "SHOULD_NOT_EXIST",
        ])

    def test_find_delete_blocked(self):
        self.check_blocked([
            "find",
            ".",
            "-delete",
        ])

    def test_find_exec_blocked(self):
        self.check_blocked([
            "find",
            ".",
            "-exec",
            "touch",
            "SHOULD_NOT_EXIST",
            ";",
        ])

    def test_sed_in_place_blocked(self):
        self.check_blocked([
            "sed",
            "-i",
            "s/test/changed/",
            "README.md",
        ])

    def test_git_branch_creation_blocked(self):
        self.check_blocked([
            "git",
            "branch",
            "SHOULD_NOT_EXIST",
        ])

    def test_git_remote_add_blocked(self):
        self.check_blocked([
            "git",
            "remote",
            "add",
            "evil",
            "https://example.invalid/repo.git",
        ])

    def test_journalctl_vacuum_blocked(self):
        self.check_blocked([
            "journalctl",
            "--vacuum-size=1K",
        ])

    def test_rg_preprocessor_blocked(self):
        self.check_blocked([
            "rg",
            "--pre",
            "cat",
            "TODO",
        ])

    # ------------------------------------------------------------
    # Project boundary attempts
    # ------------------------------------------------------------

    def test_external_absolute_path_blocked(self):
        self.check_blocked([
            "cat",
            "/etc/hosts",
        ])

    def test_parent_traversal_blocked(self):
        self.check_blocked([
            "cat",
            "../outside",
        ])

    def test_external_find_path_blocked(self):
        self.check_blocked([
            "find",
            "/tmp",
            "-maxdepth",
            "1",
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
