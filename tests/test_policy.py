import unittest

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
