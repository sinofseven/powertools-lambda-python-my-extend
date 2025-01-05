from __future__ import annotations

from typing import Any, Callable

from aws_lambda_powertools.utilities.data_classes.s3_event import S3Event

from .base import BaseRoute


class S3Route(BaseRoute):
    bucket: str | None
    bucket_prefix: str | None
    key: str | None
    key_prefix: str | None
    key_suffix: str | None
    event_name: str | None

    def __init__(
        self,
        func: Callable,
        bucket: str | None = None,
        bucket_prefix: str | None = None,
        key: str | None = None,
        key_prefix: str | None = None,
        key_suffix: str | None = None,
        event_name: str | None = None,
    ):
        self.func = func
        self.bucket = bucket
        self.bucket_prefix = bucket_prefix
        self.key = key
        self.key_prefix = key_prefix
        self.key_suffix = key_suffix
        self.event_name = event_name

        if (
            not self.bucket
            and not self.bucket_prefix
            and not self.key
            and not self.key_prefix
            and not self.key_suffix
            and not self.event_name
        ):
            raise ValueError("bucket, bucket_prefix, key, key_prefix, key_suffix, or event_name must be not null")

    def is_target_with_bucket(self, bucket: str | None) -> bool:
        if not bucket:
            return False
        elif self.bucket and self.bucket == bucket:
            return True
        elif self.bucket_prefix and bucket.find(self.bucket_prefix) == 0:
            return True
        else:
            return False

    def is_target_with_key(self, key: str | None) -> bool:
        if not key:
            return False
        elif self.key:
            return self.key == key
        elif self.key_prefix and not self.key_suffix:
            return key.find(self.key_prefix) == 0
        elif not self.key_prefix and self.key_suffix:
            length_suffix = len(self.key_suffix)
            suffix = key[-length_suffix:]
            return self.key_suffix == suffix
        elif self.key_prefix and self.key_suffix:
            length_suffix = len(self.key_suffix)
            suffix = key[-length_suffix:]
            return key.find(self.key_prefix) == 0 and self.key_suffix == suffix
        else:
            return False

    def is_target_with_event_name(self, event_name: str | None) -> bool:
        if not event_name:
            return False
        elif self.event_name:
            return self.event_name == event_name
        else:
            return False

    def is_target(self, bucket: str | None, key: str | None, event_name: str | None) -> bool:
        flag_bucket = self.is_target_with_bucket(bucket=bucket)
        flag_key = self.is_target_with_key(key=key)
        flag_event_name = self.is_target_with_event_name(event_name=event_name)

        if bucket and key and event_name:
            text = "bucket, key, event_name"
        elif bucket and key and not event_name:
            text = "bucket, key"
        elif bucket and not key and event_name:
            text = "bucket, event_name"
        elif not bucket and key and event_name:
            text = "key, event_name"
        elif bucket and not key and not event_name:
            text = "bucket"
        elif not bucket and key and not event_name:
            text = "key"
        elif not bucket and not key and event_name:
            text = "event_name"
        else:  # not bucket and not key and not event_name
            text = ""

        mapping = {
            "bucket, key, event_name": flag_bucket and flag_key and flag_event_name,
            "bucket, key": flag_bucket and flag_key,
            "bucket, event_name": flag_bucket and flag_event_name,
            "key, event_name": flag_key and flag_event_name,
            "bucket": flag_bucket,
            "key": flag_key,
            "event_name": flag_event_name,
            "": False,
        }

        return mapping[text]

    def match(self, event: dict[str, Any]) -> tuple[Callable, S3Event] | None:
        if not isinstance(event, dict):
            return None

        all_records: list[dict[str, Any]] = event.get("Records", [])

        if len(all_records) == 0:
            return None

        record = all_records[0]
        event_name = record.get("eventName")
        s3_data = record.get("s3")
        if not event_name or not s3_data:
            return None

        bucket: str | None = s3_data.get("bucket", {}).get("name")
        key: str | None = s3_data.get("object", {}).get("key")

        if not bucket and not key:
            return None

        if not self.event_name:
            event_name = None

        if not self.bucket and not self.bucket_prefix:
            bucket = None

        if not self.key and not self.key_prefix and not self.key_suffix:
            key = None

        if self.is_target(bucket, key, event_name):
            return self.func, S3Event(event)
        else:
            return None
