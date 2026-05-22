import unittest

from codex_guardian.enforcer import enforce_proposal
from codex_guardian.models import ActionProposal
from codex_guardian.policy import review_action


class PolicyTests(unittest.TestCase):
    def test_safe_file_edit_is_allowed(self):
        decision = review_action(
            ActionProposal.from_mapping(
                {
                    "user_request": "Fix login validation",
                    "action": {
                        "type": "file_edit",
                        "paths": ["src/auth/login.py"],
                    },
                }
            )
        )

        self.assertEqual(decision.decision, "allow")
        self.assertEqual(decision.risk_level, "low")

    def test_destructive_shell_command_is_declined(self):
        decision = review_action(
            ActionProposal.from_mapping(
                {
                    "user_request": "Clean output",
                    "action": {
                        "type": "shell_command",
                        "command": "rm -rf .",
                    },
                }
            )
        )

        self.assertEqual(decision.decision, "decline")
        self.assertEqual(decision.risk_level, "critical")

    def test_dependency_install_asks_user(self):
        decision = review_action(
            ActionProposal.from_mapping(
                {
                    "user_request": "Run tests",
                    "action": {
                        "type": "shell_command",
                        "command": "pip install -r requirements.txt",
                    },
                }
            )
        )

        self.assertEqual(decision.decision, "ask_user")
        self.assertEqual(decision.risk_level, "medium")

    def test_unknown_shell_command_asks_user(self):
        decision = review_action(
            ActionProposal.from_mapping(
                {
                    "user_request": "Run a local script",
                    "action": {
                        "type": "shell_command",
                        "command": "python tools/do_work.py",
                    },
                }
            )
        )

        self.assertEqual(decision.decision, "ask_user")
        self.assertIn("unknown_shell_requires_user", decision.matched_rules)

    def test_allowlisted_shell_command_runs_automatically(self):
        result = enforce_proposal(
            ActionProposal.from_mapping(
                {
                    "user_request": "Print a harmless test value",
                    "action": {
                        "type": "shell_command",
                        "command": "echo guardian-ok",
                    },
                }
            ),
            capture_output=True,
        )

        self.assertTrue(result.executed)
        self.assertEqual(result.decision.decision, "allow")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "guardian-ok")

    def test_ask_user_command_does_not_run_without_interactive_approval(self):
        result = enforce_proposal(
            ActionProposal.from_mapping(
                {
                    "user_request": "Run an arbitrary script",
                    "action": {
                        "type": "shell_command",
                        "command": "python tools/do_work.py",
                    },
                }
            ),
            capture_output=True,
        )

        self.assertFalse(result.executed)
        self.assertEqual(result.decision.decision, "ask_user")
        self.assertEqual(result.exit_code, 2)

    def test_secret_path_asks_user_even_for_read(self):
        decision = review_action(
            ActionProposal.from_mapping(
                {
                    "user_request": "Debug API",
                    "action": {
                        "type": "file_read",
                        "paths": [".env"],
                    },
                }
            )
        )

        self.assertEqual(decision.decision, "ask_user")
        self.assertEqual(decision.risk_level, "high")

    def test_secret_exposure_is_declined(self):
        decision = review_action(
            ActionProposal.from_mapping(
                {
                    "user_request": "Show the token",
                    "action": {
                        "type": "shell_command",
                        "command": "echo $OPENAI_API_KEY",
                    },
                }
            )
        )

        self.assertEqual(decision.decision, "decline")
        self.assertEqual(decision.risk_level, "critical")


if __name__ == "__main__":
    unittest.main()
