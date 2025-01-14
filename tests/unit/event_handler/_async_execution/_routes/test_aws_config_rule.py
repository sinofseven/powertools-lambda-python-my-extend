import pytest

from aws_lambda_powertools.event_handler.async_execution.router import (
    AwsConfigRuleRoute,
)
from aws_lambda_powertools.utilities.data_classes.aws_config_rule_event import (
    AWSConfigRuleEvent,
)
from tests.functional.utils import load_event


class TestAwsConfigRuleRoute:
    def test_constructor_error(self):
        with pytest.raises(ValueError):
            AwsConfigRuleRoute(func=lambda _: None)

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            ({"func": None, "arn": "test-arn"}, {"arn": None}, False),
            ({"func": None, "arn": "test-arn"}, {"arn": "test-arn"}, True),
            ({"func": None, "arn": "test-arn-v2"}, {"arn": "test-arn"}, False),
            ({"func": None, "rule_name": "test-rule"}, {"arn": "test-arn"}, False),
        ],
    )
    def test_is_target_with_arn(self, option_constructor, option_func, expected):
        route = AwsConfigRuleRoute(**option_constructor)
        actual = route.is_target_with_arn(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            ({"func": None, "rule_name": "test-rule"}, {"rule_name": None}, False),
            ({"func": None, "rule_name": "test-rule"}, {"rule_name": "test-rule"}, True),
            ({"func": None, "rule_name": "test-rule-v2"}, {"rule_name": "test-rule"}, False),
            ({"func": None, "rule_name_prefix": "test-r"}, {"rule_name": "test-rule"}, True),
            ({"func": None, "rule_name_prefix": "test-rr"}, {"rule_name": "test-rule"}, False),
            ({"func": None, "rule_name": "test-rule", "rule_name_prefix": "test-r"}, {"rule_name": "test-rule"}, True),
            ({"func": None, "rule_name": "test-rule", "rule_name_prefix": "test-rr"}, {"rule_name": "test-rule"}, True),
            (
                {"func": None, "rule_name": "test-rule-v2", "rule_name_prefix": "test-r"},
                {"rule_name": "test-rule"},
                False,
            ),
            (
                {"func": None, "rule_name": "test-rule-v2", "rule_name_prefix": "test-r"},
                {"rule_name": "test-rule"},
                False,
            ),
            ({"func": None, "arn": "test-arn"}, {"rule_name": "test-rule"}, False),
        ],
    )
    def test_is_target_with_rule_name(self, option_constructor, option_func, expected):
        route = AwsConfigRuleRoute(**option_constructor)
        actual = route.is_target_with_rule_name(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            ({"func": None, "rule_id": "test-id"}, {"rule_id": None}, False),
            ({"func": None, "rule_id": "test-id"}, {"rule_id": "test-id"}, True),
            ({"func": None, "rule_id": "test-id-v2"}, {"rule_id": "test-id"}, False),
            ({"func": None, "arn": "test-arn"}, {"rule_id": "test-id"}, False),
        ],
    )
    def test_is_target_with_rule_id(self, option_constructor, option_func, expected):
        route = AwsConfigRuleRoute(**option_constructor)
        actual = route.is_target_with_rule_id(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "event_name, option_constructor, expected_true",
        [
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, rule_name_prefix, and rule_id
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-i9y8j9",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, rule_name_prefix, and rule_id
            # match 3, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-i9y8j9",
                },
                True,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, rule_name_prefix, and rule_id
            # match 2, unmatch 2
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, rule_name_prefix, and rule_id
            # match 1, unmatch 3
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, rule_name_prefix, and rule_id
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, and rule_name_prefix
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyR",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, and rule_name_prefix
            # match 2, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyRR",
                },
                True,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyR",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyR",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, and rule_name_prefix
            # match 1, unmatch 2
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyRR",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyRR",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyR",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, and rule_name_prefix
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyRR",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, and rule_id
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRule",
                    "rule_id": "config-rule-i9y8j9",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, and rule_id
            # match 2, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRule",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRuleV2",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRule",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, and rule_id
            # match 1, unmatch 2
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRuleV2",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRule",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRuleV2",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name, and rule_id
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRuleV2",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name_prefix, and rule_id
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-i9y8j9",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name_prefix, and rule_id
            # match 2, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name_prefix, and rule_id
            # match 1, unmatch 2
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn, rule_name_prefix, and rule_id
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name, rule_name_prefix, and rule_id
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-i9y8j9",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name, rule_name_prefix, and rule_id
            # match 2, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-i9y8j9",
                },
                True,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name, rule_name_prefix, and rule_id
            # match 1, unmatch 2
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name, rule_name_prefix, and rule_id
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyRR",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn and rule_name
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRule",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn and rule_name
            # match 1, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name": "MyRuleV2",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRule",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn and rule_name
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name": "MyRuleV2",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn and rule_name_prefix
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name_prefix": "MyR",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn and rule_name_prefix
            # match 1, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_name_prefix": "MyRR",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name_prefix": "MyR",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn and rule_name_prefix
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_name_prefix": "MyRR",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn and rule_id
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_id": "config-rule-i9y8j9",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn and rule_id
            # match 1, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_id": "config-rule-i9y8j9",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn and rule_id
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                    "rule_id": "config-rule-000000",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name and rule_name_prefix
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyR",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name and rule_name_prefix
            # match 1, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRule",
                    "rule_name_prefix": "MyRR",
                },
                True,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyR",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name and rule_name_prefix
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "MyRR",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name and rule_id
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": lambda *_: None, "rule_name": "MyRule", "rule_id": "config-rule-i9y8j9"},
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name and rule_id
            # match 1, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": lambda *_: None, "rule_name": "MyRule", "rule_id": "config-rule-000000"},
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": lambda *_: None, "rule_name": "MyRuleV2", "rule_id": "config-rule-i9y8j9"},
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name and rule_id
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": lambda *_: None, "rule_name": "MyRuleV2", "rule_id": "config-rule-000000"},
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name_prefix and rule_id
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": lambda *_: None, "rule_name_prefix": "MyR", "rule_id": "config-rule-i9y8j9"},
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name_prefix and rule_id
            # match 1, unmatch 1
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": lambda *_: None, "rule_name_prefix": "MyR", "rule_id": "config-rule-000000"},
                False,
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": lambda *_: None, "rule_name_prefix": "MyRR", "rule_id": "config-rule-i9y8j9"},
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name_prefix and rule_id
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": lambda *_: None, "rule_name_prefix": "MyRR", "rule_id": "config-rule-000000"},
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with arn
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-000000",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRule",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name": "MyRuleV2",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name_prefix
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name_prefix": "MyR",
                },
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_name_prefix
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": lambda *_: None,
                    "rule_name_prefix": "MyRR",
                },
                False,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_id
            # match all
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": lambda *_: None, "rule_id": "config-rule-i9y8j9"},
                True,
            ),
            # awsConfigRuleConfigurationChanged.json
            # with rule_id
            # unmatch all
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": lambda *_: None, "rule_id": "config-rule-000000"},
                False,
            ),
        ],
    )
    def test_match(self, event_name, option_constructor, expected_true):
        event = load_event(file_name=event_name)
        route = AwsConfigRuleRoute(**option_constructor)
        expected_return = (route.func, AWSConfigRuleEvent(event))
        actual = route.match(event=event)
        if expected_true:
            assert actual == expected_return
        else:
            assert actual is None
