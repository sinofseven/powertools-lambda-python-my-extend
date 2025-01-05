from __future__ import annotations

from typing import Any, Callable

from aws_lambda_powertools.utilities.data_classes.ses_event import SESEvent

from .base import BaseRoute


class SESRoute(BaseRoute):
    mail_to: list[str] | None
    mail_from: list[str] | None
    mail_subject: str | None

    def __init__(
        self,
        func: Callable,
        mail_to: str | list[str] | None = None,
        mail_from: str | list[str] | None = None,
        mail_subject: str | None = None,
    ):
        self.func = func

        if isinstance(mail_to, str):
            self.mail_to = [mail_to]
        else:
            self.mail_to = mail_to

        if isinstance(mail_from, str):
            self.mail_from = [mail_from]
        else:
            self.mail_from = mail_from

        self.mail_subject = mail_subject

        if not self.mail_to and not self.mail_from and not self.mail_subject:
            raise ValueError("mail_to, mail_from, or mail_subject must be not null")

    def is_target_with_mail_to(self, mail_to: list[str] | None) -> bool:
        if not mail_to or not self.mail_to:
            return False

        for address in self.mail_to:
            if address in mail_to:
                return True

        return False

    def is_target_with_mail_from(self, mail_from: list[str] | None) -> bool:
        if not mail_from or not self.mail_from:
            return False

        for address in self.mail_from:
            if address in mail_from:
                return True

        return False

    def is_target_with_mail_subject(self, mail_subject: str | None) -> bool:
        if mail_subject and self.mail_subject:
            return self.mail_subject == mail_subject
        else:
            return False

    def is_target(self, mail_to: list[str] | None, mail_from: list[str] | None, mail_subject: str | None) -> bool:
        flag_mail_to = self.is_target_with_mail_to(mail_to=mail_to)
        flag_mail_from = self.is_target_with_mail_from(mail_from=mail_from)
        flag_mail_subject = self.is_target_with_mail_subject(mail_subject=mail_subject)

        if mail_to and mail_from and mail_subject:
            text = "mail_to, mail_from, mail_subject"
        elif mail_to and mail_from and not mail_subject:
            text = "mail_to, mail_from"
        elif mail_to and not mail_from and mail_subject:
            text = "mail_to, mail_subject"
        elif not mail_to and mail_from and mail_subject:
            text = "mail_from, mail_subject"
        elif mail_to and not mail_from and not mail_subject:
            text = "mail_to"
        elif not mail_to and mail_from and not mail_subject:
            text = "mail_from"
        elif not mail_to and not mail_from and mail_subject:
            text = "mail_subject"
        else:  # not mail_to and not mail_from and not mail_subject
            text = ""

        mapping = {
            "mail_to, mail_from, mail_subject": flag_mail_to and flag_mail_from and flag_mail_subject,
            "mail_to, mail_from": flag_mail_to and flag_mail_from,
            "mail_to, mail_subject": flag_mail_to and flag_mail_subject,
            "mail_from, mail_subject": flag_mail_from and flag_mail_subject,
            "mail_to": flag_mail_to,
            "mail_from": flag_mail_from,
            "mail_subject": flag_mail_subject,
            "": False,
        }
        return mapping[text]

    def match(self, event: dict[str, Any]) -> tuple[Callable, SESEvent] | None:
        if not isinstance(event, dict):
            return None

        all_records: list[dict[str, Any]] = event.get("Records", [])

        if len(all_records) == 0:
            return None

        common_header: dict[str, Any] | None = all_records[0].get("ses", {}).get("mail", {}).get("commonHeaders")

        if common_header is None:
            return None

        if self.mail_to:
            mail_to = common_header.get("to")
        else:
            mail_to = None

        if self.mail_from:
            mail_from = common_header.get("from")
        else:
            mail_from = None

        if self.mail_subject:
            mail_subject = common_header.get("subject")
        else:
            mail_subject = None

        if self.is_target(mail_to, mail_from, mail_subject):
            return self.func, SESEvent(event)
        else:
            return None
