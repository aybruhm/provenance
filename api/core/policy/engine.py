import fnmatch
from datetime import datetime
from typing import Any
from uuid import UUID

from core.policy.dtos import (
    ConditionDTO,
    MatchRuleDTO,
    NormalizedOperation,
    PolicyDTO,
    ViolationRuleDTO,
)
from core.policy.service import PolicyService


class PolicyEngine:
    """
    Policy Engine

    Loads a policy and evaluates tool-call requests against it.

    Rule evaluation order (first terminal match wins):
      1. action pattern must match (fnmatch glob)
      2. If conditions defined:
           - All conditions PASS  → apply on_match (if set), else continue
           - Any condition FAILS  → apply on_violation (if set), else continue
      3. If no conditions: apply on_match (if set), else continue
      4. Fallback: ALLOW
    """

    def __init__(self, service: PolicyService):
        self.service = service

    # ── condition evaluator ───────────────────────────────────────────────────────
    def _evaluate_conditions(
        self,
        conditions: list[ConditionDTO],
        parameters: dict[str, Any],
    ) -> tuple[bool, str]:
        """
        Evaluate conditions against parameters.

        Args:
            conditions: list of ConditionDTO
            parameters: dict of parameter_key → value (e.g. from tool call)

        Returns (passed: bool, failing_condition: str).
        failing_condition is empty when all conditions pass.
        """

        for condition in conditions:
            field_value = parameters.get(condition.field)
            expected = condition.value
            op = condition.operator

            match op:
                case NormalizedOperation.EQ:
                    passed = field_value == expected
                case NormalizedOperation.NE:
                    passed = field_value != expected
                case NormalizedOperation.GT:
                    passed = field_value > expected
                case NormalizedOperation.GE:
                    passed = field_value >= expected
                case NormalizedOperation.LT:
                    passed = field_value < expected
                case NormalizedOperation.LE:
                    passed = field_value <= expected
                case NormalizedOperation.IN:
                    passed = field_value in expected
                case NormalizedOperation.NOT_IN:
                    passed = field_value not in expected
                case _:
                    raise ValueError(f"Unknown operator: {op}")

            if not passed:
                return (
                    False,
                    f"{condition.field} {op} {expected} failed (got {field_value})",
                )

        return True, ""

    # ── loader ────────────────────────────────────────────────────────────────────
    async def load_policy(self, tenant_policy_id: str) -> PolicyDTO:
        policy = await self.service.get_tenant_policy(
            tenant_policy_id=UUID(tenant_policy_id)
        )
        if not policy:
            return PolicyDTO(
                id=tenant_policy_id,
                name="default-passthrough",
                version="0.0",
                description="Default passthrough policy",
                rules=[
                    MatchRuleDTO(
                        action="*",
                        on_match="BLOCK",
                        reason="Looks like the specified policy file is missing or malformed, so we're blocking all actions just to be safe. Please check your policy configuration.",
                    )
                ],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )

        return policy

    # ── rule evaluator ────────────────────────────────────────────────────────────
    def evaluate_policy(
        self,
        policy: PolicyDTO,
        action: str,
        parameters: dict[str, Any],
    ) -> tuple[str, str]:
        """
        Evaluate a policy against an action + parameters.

        Args:
            policy: PolicyDTO
            action: the action being requested (e.g. "transfer_funds")
            parameters: dict of parameters relevant to the action (e.g. amount, currency, recipient_id)

        Returns:
            (decision, reason)  where decision ∈ {"ALLOW", "BLOCK", "ESCALATE"}
        """

        rules = policy.rules
        for rule in rules:
            pattern = rule.action

            # ── step 1: does the action match this rule's pattern? ──
            if not fnmatch.fnmatch(action, pattern):
                continue

            conditions = rule.conditions or []
            if not conditions and isinstance(rule, MatchRuleDTO):
                outcome = rule.on_match
                if outcome:
                    reason = (
                        rule.reason or f"Rule matched: {pattern} | conditions satisfied"
                    )
                    return outcome, reason

                # No conditions: unconditional outcome
                continue

            passed, failing = self._evaluate_conditions(conditions, parameters)
            if not passed and isinstance(rule, ViolationRuleDTO):
                outcome = rule.on_violation
                if outcome:
                    reason = rule.reason or f"Condition failed: {failing}"
                    return outcome, reason

                # Conditions fail but no on_violation → keep evaluating
                continue

            if isinstance(rule, MatchRuleDTO):
                outcome = rule.on_match
                if outcome:
                    reason = (
                        rule.reason or f"Rule matched: {pattern} | conditions satisfied"
                    )
                    return outcome, reason

                # Conditions pass but no on_match → keep evaluating
                continue

        return "ALLOW", "No rule matched; default ALLOW"
