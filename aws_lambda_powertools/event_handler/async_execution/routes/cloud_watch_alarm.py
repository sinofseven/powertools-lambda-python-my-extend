from __future__ import annotations

from typing import Any, Callable

from aws_lambda_powertools.utilities.data_classes.cloud_watch_alarm_event import (
    CloudWatchAlarmEvent,
)

from .base import BaseRoute


class CloudWatchAlarmRoute(BaseRoute):
    arn: str | None
    alarm_name: str | None
    alarm_name_prefix: str | None

    def __init__(
        self,
        func: Callable,
        arn: str | None = None,
        alarm_name: str | None = None,
        alarm_name_prefix: str | None = None,
    ):
        self.func = func
        self.arn = arn
        self.alarm_name = alarm_name
        self.alarm_name_prefix = alarm_name_prefix

        if not self.arn and not self.alarm_name and not self.alarm_name_prefix:
            raise ValueError("arn, alarm_name, or alarm_name_prefix must be not null")

    def match(self, event: dict[str, Any]) -> tuple[Callable, CloudWatchAlarmEvent] | None:
        if not isinstance(event, dict):
            return None
        elif self.arn:
            if event.get("alarmArn") == self.arn:
                return self.func, CloudWatchAlarmEvent(event)
            else:
                return None

        alarm_name = event.get("alarmData", {}).get("alarmName", "")
        if self.alarm_name:
            if alarm_name == self.alarm_name:
                return self.func, CloudWatchAlarmEvent(event)
        elif self.alarm_name_prefix:
            if alarm_name.find(self.alarm_name_prefix) == 0:
                return self.func, CloudWatchAlarmEvent(event)

        return None
