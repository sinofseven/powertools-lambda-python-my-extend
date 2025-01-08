from __future__ import annotations

from typing import Any, Callable

from aws_lambda_powertools.utilities.data_classes.event_bridge_event import (
    EventBridgeEvent,
)

from .base import BaseRoute


class EventBridgeRoute(BaseRoute):
    detail_type: str | None
    source: str | None
    resources: list[str] | None

    def __init__(
        self,
        func: Callable,
        detail_type: str | None = None,
        source: str | None = None,
        resources: str | list[str] | None = None,
    ):
        self.func = func
        self.detail_type = detail_type
        self.source = source

        if isinstance(resources, str):
            self.resources = [resources]
        else:
            self.resources = resources

        if not self.detail_type and not self.source and not self.resources:
            raise ValueError("detail_type, source, or resources must be not null")

    def is_target_with_detail_type(self, detail_type: str | None) -> bool:
        if detail_type and self.detail_type:
            return self.detail_type == detail_type
        else:
            return False

    def is_target_with_source(self, source: str | None) -> bool:
        if source and self.source:
            return self.source == source
        else:
            return False

    def is_target_with_resources(self, resources: list[str] | None) -> bool:
        if resources and self.resources:
            for item in self.resources:
                if item in resources:
                    return True

        return False

    def is_target(self, detail_type: str | None, source: str | None, resources: list[str] | None) -> bool:
        flag_detail_type = self.is_target_with_detail_type(detail_type=detail_type)
        flag_source = self.is_target_with_source(source=source)
        flag_resources = self.is_target_with_resources(resources=resources)

        if detail_type and source and resources:
            text = "detail_type, source, resources"
        elif detail_type and source and not resources:
            text = "detail_type, source"
        elif detail_type and not source and resources:
            text = "detail_type, resources"
        elif not detail_type and source and resources:
            text = "source, resources"
        elif detail_type and not source and not resources:
            text = "detail_type"
        elif not detail_type and source and not resources:
            text = "source"
        elif not detail_type and not source and resources:
            text = "resources"
        else:  # not detail_type and not source and not resources
            text = ""

        mapping = {
            "detail_type, source, resources": flag_detail_type and flag_source and flag_resources,
            "detail_type, source": flag_detail_type and flag_source,
            "detail_type, resources": flag_detail_type and flag_resources,
            "source, resources": flag_source and flag_resources,
            "detail_type": flag_detail_type,
            "source": flag_source,
            "resources": flag_resources,
            "": False,
        }

        return mapping[text]

    def match(self, event: dict[str, Any]) -> tuple[Callable, EventBridgeEvent] | None:
        if not isinstance(event, dict):
            return None

        detail_type: str | None = event.get("detail-type")
        source: str | None = event.get("source")
        resources: list[str] | None = event.get("resources")

        if not detail_type and not source and not resources:
            return None

        if not self.detail_type:
            detail_type = None

        if not self.source:
            source = None

        if not self.resources:
            resources = None

        if self.is_target(detail_type, source, resources):
            return self.func, EventBridgeEvent(event)
        else:
            return None
