from __future__ import annotations

from typing import Any, Callable

from aws_lambda_powertools.utilities.data_classes.cloud_watch_logs_event import (
    CloudWatchLogsEvent,
)

from .base import BaseRoute


class CloudWatchLogsRoute(BaseRoute):
    log_group: str | None
    log_group_prefix: str | None
    log_stream: str | None
    log_stream_prefix: str | None
    subscription_filters: list[str] | None

    def __init__(
        self,
        func: Callable,
        log_group: str | None = None,
        log_group_prefix: str | None = None,
        log_stream: str | None = None,
        log_stream_prefix: str | None = None,
        subscription_filters: str | list[str] | None = None,
    ):
        self.func = func
        self.log_group = log_group
        self.log_group_prefix = log_group_prefix
        self.log_stream = log_stream
        self.log_stream_prefix = log_stream_prefix

        if isinstance(subscription_filters, str):
            self.subscription_filters = [subscription_filters]
        else:
            self.subscription_filters = subscription_filters

        if (
            not self.log_group
            and not self.log_group_prefix
            and not self.log_stream
            and not self.log_stream_prefix
            and not self.subscription_filters
        ):
            raise ValueError(
                "log_group, log_group_prefix, log_stream, log_stream_prefix, or subscription_filters must be not null",
            )

    def is_target_with_log_group(self, log_group: str | None) -> bool:
        if not log_group:
            return False
        elif self.log_group:
            return self.log_group == log_group
        elif self.log_group_prefix:
            return log_group.find(self.log_group_prefix) == 0
        else:
            return False

    def is_target_with_log_stream(self, log_stream: str | None) -> bool:
        if not log_stream:
            return False
        elif self.log_stream:
            return self.log_stream == log_stream
        elif self.log_stream_prefix:
            return log_stream.find(self.log_stream_prefix) == 0
        else:
            return False

    def is_target_with_subscription_filters(self, subscription_filters: list[str] | None) -> bool:
        if not subscription_filters:
            return False
        elif not self.subscription_filters:
            return False

        for name in self.subscription_filters:
            if name in subscription_filters:
                return True

        return False

    def is_target(self, log_group: str | None, log_stream: str | None, subscription_filters: list[str] | None) -> bool:
        flag_log_group = self.is_target_with_log_group(log_group=log_group)
        flag_log_stream = self.is_target_with_log_stream(log_stream=log_stream)
        flag_subscription_filters = self.is_target_with_subscription_filters(subscription_filters=subscription_filters)

        if log_group and log_stream and subscription_filters:
            text = "log_group, log_stream, subscription_filters"
        elif log_group and log_stream and not subscription_filters:
            text = "log_group, log_stream"
        elif log_group and not log_stream and subscription_filters:
            text = "log_group, subscription_filters"
        elif not log_group and log_stream and subscription_filters:
            text = "log_stream, subscription_filters"
        elif log_group and not log_stream and not subscription_filters:
            text = "log_group"
        elif not log_group and log_stream and not subscription_filters:
            text = "log_stream"
        elif not log_group and not log_stream and subscription_filters:
            text = "subscription_filters"
        else:  # not log_group and not log_stream and not subscription_filters
            text = ""

        mapping = {
            "log_group, log_stream, subscription_filters": flag_log_group
            and flag_log_stream
            and flag_subscription_filters,
            "log_group, log_stream": flag_log_group and flag_log_stream,
            "log_group, subscription_filters": flag_log_group and flag_subscription_filters,
            "log_stream, subscription_filters": flag_log_stream and flag_subscription_filters,
            "log_group": flag_log_group,
            "log_stream": flag_log_stream,
            "subscription_filters": flag_subscription_filters,
            "": False,
        }

        return mapping[text]

    def match(self, event: dict[str, Any]) -> tuple[Callable, CloudWatchLogsEvent] | None:
        if not isinstance(event, dict):
            return None

        text = event.get("awslogs", {}).get("data")

        if not isinstance(text, str):
            return None

        data = CloudWatchLogsEvent(event)
        decoded = data.parse_logs_data()

        if self.log_group or self.log_group_prefix:
            log_group = decoded.log_group
        else:
            log_group = None

        if self.log_stream or self.log_stream_prefix:
            log_stream = decoded.log_stream
        else:
            log_stream = None

        if self.subscription_filters:
            subscription_filters = decoded.subscription_filters
        else:
            subscription_filters = None

        if self.is_target(log_group, log_stream, subscription_filters):
            return self.func, data
        else:
            return None
