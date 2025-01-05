from __future__ import annotations

from typing import Any, Callable

from aws_lambda_powertools.utilities.data_classes.aws_config_rule_event import (
    AWSConfigRuleEvent,
)

from .base import BaseRoute


class AwsConfigRuleRoute(BaseRoute):
    arn: str | None
    rule_name: str | None
    rule_name_prefix: str | None
    rule_id: str | None

    def __init__(
        self,
        func: Callable,
        arn: str | None = None,
        rule_name: str | None = None,
        rule_name_prefix: str | None = None,
        rule_id: str | None = None,
    ):
        self.func = func
        self.arn = arn
        self.rule_name = rule_name
        self.rule_name_prefix = rule_name_prefix
        self.rule_id = rule_id

        if not self.arn and not self.rule_name and not self.rule_name_prefix and not self.rule_id:
            raise ValueError("arn, rule_name, rule_name_prefix, or rule_id must be not null")

    def match(self, event: dict[str, Any]) -> tuple[Callable, AWSConfigRuleEvent] | None:
        if not isinstance(event, dict):
            return None
        elif self.arn:
            if event.get("configRuleArn") == self.arn:
                return self.func, AWSConfigRuleEvent(event)
        elif self.rule_name:
            if event.get("configRuleName") == self.rule_name:
                return self.func, AWSConfigRuleEvent(event)
        elif self.rule_name_prefix:
            if event.get("configRuleName", "").find(self.rule_name_prefix) == 0:
                return self.func, AWSConfigRuleEvent(event)
        elif self.rule_id:
            if event.get("configRuleId") == self.rule_id:
                return self.func, AWSConfigRuleEvent(event)

        return None
