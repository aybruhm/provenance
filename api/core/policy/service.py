from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

import aiofiles
import yaml

from utils.logger_utils import logger


class PolicyEngine:
    """
    Policy Engine

    Loads a YAML policy file and evaluates tool-call requests against it.

    Rule evaluation order (first terminal match wins):
      1. action pattern must match (fnmatch glob)
      2. If conditions defined:
           - All conditions PASS  → apply on_match (if set), else continue
           - Any condition FAILS  → apply on_violation (if set), else continue
      3. If no conditions: apply on_match (if set), else continue
      4. Fallback: ALLOW

    Supported condition keys:
      max_amount          parameters["amount"] <= value
      min_amount          parameters["amount"] >= value
      allowed_currencies  parameters["currency"] in list
      blocked_recipients  parameters["recipient_id"] not in list
      {field}_equals      parameters[field] == value
      {field}_contains    value substring in str(parameters[field])
    """

    def __init__(self):
        try:
            self.POLICIES_DIR = Path("policies")
        except FileNotFoundError as e:
            logger.error(
                f"Error initializing PolicyEngine due to missing directory: {e}"
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing PolicyEngine: {e}")
            raise

    # ── condition evaluator ───────────────────────────────────────────────────────
    def _evaluate_conditions(
        self,
        conditions: dict[str, Any],
        parameters: dict[str, Any],
    ) -> tuple[bool, str]:
        """
        Evaluate conditions against parameters.

        Args:
            conditions: dict of condition_key → value
            parameters: dict of parameter_key → value (e.g. from tool call)

        Returns (passed: bool, failing_condition: str).
        failing_condition is empty when all conditions pass.
        """

        for key, value in conditions.items():
            if key == "max_amount":
                if parameters.get("amount", 0) > value:
                    return False, f"amount {parameters.get('amount')} > max {value}"

            elif key == "min_amount":
                if parameters.get("amount", 0) < value:
                    return False, f"amount {parameters.get('amount')} < min {value}"

            elif key == "allowed_currencies":
                currency = parameters.get("currency")
                if currency not in value:
                    return False, f"currency '{currency}' not in {value}"

            elif key == "blocked_recipients":
                recipient = parameters.get("recipient_id")
                if recipient in value:
                    return False, f"recipient '{recipient}' is blocked"

            elif key.endswith("_equals"):
                field = key[:-7]
                if parameters.get(field) != value:
                    return False, f"{field} != {value}"

            elif key.endswith("_contains"):
                field = key[:-9]
                if value not in str(parameters.get(field, "")):
                    return False, f"'{value}' not in {field}"

        return True, ""

    # ── loader ────────────────────────────────────────────────────────────────────
    async def load_policy(self, policy_id: str) -> dict[str, Any]:
        path = self.POLICIES_DIR / f"{policy_id}.yaml"
        if not path.exists():
            return {
                "name": "default-passthrough",
                "rules": [
                    {
                        "action": "*",
                        "on_match": "BLOCK",
                        "reason": "Looks like the specified policy file is missing or malformed, so we're blocking all actions just to be safe. Please check your policy configuration.",
                    }
                ],
            }

        async with aiofiles.open(path, "r") as f:
            content = await f.read()
            return yaml.safe_load(content)

    # ── rule evaluator ────────────────────────────────────────────────────────────
    def evaluate_policy(
        self,
        policy: dict[str, Any],
        action: str,
        parameters: dict[str, Any],
    ) -> tuple[str, str]:
        """
        Evaluate a policy against an action + parameters.

        Args:
            policy: dict with "rules" key containing list of rules
            action: the action being requested (e.g. "transfer_funds")
            parameters: dict of parameters relevant to the action (e.g. amount, currency, recipient_id)

        Returns:
            (decision, reason)  where decision ∈ {"ALLOW", "BLOCK", "ESCALATE"}
        """

        rules: list[dict[str, Any]] = policy.get("rules", [])
        for rule in rules:
            pattern = rule.get("action", "*")

            # ── step 1: does the action match this rule's pattern? ──
            if not fnmatch.fnmatch(action, pattern):
                continue

            conditions: dict[str, Any] = rule.get("conditions", {})
            if conditions:
                passed, failing = self._evaluate_conditions(conditions, parameters)
                if passed:
                    outcome = rule.get("on_match")
                    if outcome:
                        reason = rule.get(
                            "reason", f"Rule matched: {pattern} | conditions satisfied"
                        )
                        return outcome, reason

                    # Conditions pass but no on_match → keep evaluating
                    continue
                else:
                    outcome = rule.get("on_violation")
                    if outcome:
                        reason = rule.get(
                            "violation_reason", f"Condition failed: {failing}"
                        )
                        return outcome, reason

                    # Conditions fail but no on_violation → keep evaluating
                    continue

            else:
                # No conditions: unconditional outcome
                outcome = rule.get("on_match")
                if outcome:
                    reason = rule.get("reason", f"Unconditional match: {pattern}")
                    return outcome, reason
                continue

        return "ALLOW", "No rule matched; default ALLOW"
