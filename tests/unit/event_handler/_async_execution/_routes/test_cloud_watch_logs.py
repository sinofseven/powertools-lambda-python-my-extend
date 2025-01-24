import pytest

from aws_lambda_powertools.event_handler.async_execution.routes.cloud_watch_logs import (
    CloudWatchLogsRoute,
)
from aws_lambda_powertools.utilities.data_classes.cloud_watch_logs_event import (
    CloudWatchLogsEvent,
)
from tests.functional.utils import load_event


class TestCloudWatchLogsRoute:
    def test_constructor_error(self):
        with pytest.raises(ValueError):
            CloudWatchLogsRoute(func=None)

    @pytest.mark.parametrize(
        "option, expected",
        [
            (
                {"func": None, "log_group": "test"},
                {
                    "func": None,
                    "log_group": "test",
                    "log_group_prefix": None,
                    "log_stream": None,
                    "log_stream_prefix": None,
                    "subscription_filters": None,
                },
            ),
            (
                {"func": None, "log_group_prefix": "test"},
                {
                    "func": None,
                    "log_group": None,
                    "log_group_prefix": "test",
                    "log_stream": None,
                    "log_stream_prefix": None,
                    "subscription_filters": None,
                },
            ),
            (
                {"func": None, "log_stream": "test"},
                {
                    "func": None,
                    "log_group": None,
                    "log_group_prefix": None,
                    "log_stream": "test",
                    "log_stream_prefix": None,
                    "subscription_filters": None,
                },
            ),
            (
                {"func": None, "log_stream_prefix": "test"},
                {
                    "func": None,
                    "log_group": None,
                    "log_group_prefix": None,
                    "log_stream": None,
                    "log_stream_prefix": "test",
                    "subscription_filters": None,
                },
            ),
            (
                {"func": None, "subscription_filters": "test"},
                {
                    "func": None,
                    "log_group": None,
                    "log_group_prefix": None,
                    "log_stream": None,
                    "log_stream_prefix": None,
                    "subscription_filters": ["test"],
                },
            ),
            (
                {"func": None, "subscription_filters": ["test", "name"]},
                {
                    "func": None,
                    "log_group": None,
                    "log_group_prefix": None,
                    "log_stream": None,
                    "log_stream_prefix": None,
                    "subscription_filters": ["test", "name"],
                },
            ),
        ],
    )
    def test_constructor_normal(self, option, expected):
        route = CloudWatchLogsRoute(**option)
        assert route.__dict__ == expected

    @pytest.mark.parametrize(
        "option_constructor, option, expected",
        [
            # with log_group and log_group_prefix
            # match all
            (
                {"func": None, "log_group": "testLogGroup", "log_group_prefix": "testL"},
                {"log_group": "testLogGroup"},
                True,
            ),
            # with log_group and log_group_prefix
            # match 1, unmatch 1
            (
                {"func": None, "log_group": "testLogGroup", "log_group_prefix": "estL"},
                {"log_group": "testLogGroup"},
                True,
            ),
            (
                {"func": None, "log_group": "testLogGroupV2", "log_group_prefix": "testL"},
                {"log_group": "testLogGroup"},
                False,
            ),
            # with log_group and log_group_prefix
            # unmatch all
            (
                {"func": None, "log_group": "testLogGroupV2", "log_group_prefix": "estL"},
                {"log_group": "testLogGroup"},
                False,
            ),
            # with log_group
            (
                {
                    "func": None,
                    "log_group": "testLogGroup",
                },
                {"log_group": "testLogGroup"},
                True,
            ),
            (
                {
                    "func": None,
                    "log_group": "testLogGroupV2",
                },
                {"log_group": "testLogGroup"},
                False,
            ),
            # with log_group_prefix
            ({"func": None, "log_group_prefix": "testL"}, {"log_group": "testLogGroup"}, True),
            ({"func": None, "log_group_prefix": "estL"}, {"log_group": "testLogGroup"}, False),
            # without log_group and log_group_prefix
            ({"func": None, "log_stream": "testLogStream"}, {"log_group": "testLogGroup"}, False),
            # without log_group at option_func
            ({"func": None, "log_group": "testLogGroup"}, {"log_group": None}, False),
        ],
    )
    def test_is_target_with_log_group(self, option_constructor, option, expected):
        route = CloudWatchLogsRoute(**option_constructor)
        actual = route.is_target_with_log_group(**option)
        assert actual == expected

    @pytest.mark.parametrize(
        "option_constructor, option, expected",
        [
            # with log_stream and log_stream_prefix
            # match all
            (
                {"func": None, "log_stream": "testLogStream", "log_stream_prefix": "testL"},
                {"log_stream": "testLogStream"},
                True,
            ),
            # with log_stream and log_stream_prefix
            # match 1, unmatch 1
            (
                {"func": None, "log_stream": "testLogStream", "log_stream_prefix": "estL"},
                {"log_stream": "testLogStream"},
                True,
            ),
            (
                {"func": None, "log_stream": "testLogStreamV2", "log_stream_prefix": "testL"},
                {"log_stream": "testLogStream"},
                False,
            ),
            # with log_stream and log_stream_prefix
            # unmatch all
            (
                {"func": None, "log_stream": "testLogStreamV2", "log_stream_prefix": "estL"},
                {"log_stream": "testLogStream"},
                False,
            ),
            # with log_stream
            (
                {
                    "func": None,
                    "log_stream": "testLogStream",
                },
                {"log_stream": "testLogStream"},
                True,
            ),
            (
                {
                    "func": None,
                    "log_stream": "testLogStreamV2",
                },
                {"log_stream": "testLogStream"},
                False,
            ),
            # with log_stream_prefix
            ({"func": None, "log_stream_prefix": "testL"}, {"log_stream": "testLogStream"}, True),
            ({"func": None, "log_stream_prefix": "estL"}, {"log_stream": "testLogStream"}, False),
            # without log_stream and log_stream_prefix
            ({"func": None, "log_group": "testLogGroup"}, {"log_stream": "testLogStream"}, False),
            # without log_stream at option_func
            ({"func": None, "log_stream_prefix": "testL"}, {"log_stream": None}, False),
        ],
    )
    def test_is_target_with_log_stream(self, option_constructor, option, expected):
        route = CloudWatchLogsRoute(**option_constructor)
        actual = route.is_target_with_log_stream(**option)
        assert actual == expected

    @pytest.mark.parametrize(
        "option_constructor, option, expected",
        [
            # without subscription_filters at option_func
            ({"func": None, "subscription_filters": ["test"]}, {"subscription_filters": None}, False),
            # without subscription_filters
            ({"func": None, "log_group": "test"}, {"subscription_filters": ["test"]}, False),
            # with subscription_filters
            # match
            ({"func": None, "subscription_filters": ["test"]}, {"subscription_filters": ["test"]}, True),
            ({"func": None, "subscription_filters": ["test", "name"]}, {"subscription_filters": ["test"]}, True),
            ({"func": None, "subscription_filters": ["test"]}, {"subscription_filters": ["test", "name"]}, True),
            # with subscription_filters
            # unmatch
            ({"func": None, "subscription_filters": ["test"]}, {"subscription_filters": ["name"]}, False),
        ],
    )
    def test_is_target_with_subscription_filters(self, option_constructor, option, expected):
        route = CloudWatchLogsRoute(**option_constructor)
        actual = route.is_target_with_subscription_filters(**option)
        assert actual == expected

    @pytest.mark.parametrize(
        "event_name, option_constructor, is_match",
        [
            # with log_group, log_stream, and subscription_filters
            # match all
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroup",
                    "log_stream": "testLogStream",
                    "subscription_filters": ["testFilter"],
                },
                True,
            ),
            # with log_group, log_stream, and subscription_filters
            # match 2, unmatch 1
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroup",
                    "log_stream": "testLogStream",
                    "subscription_filters": ["testFilterV2"],
                },
                False,
            ),
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroup",
                    "log_stream": "testLogStreamV2",
                    "subscription_filters": ["testFilter"],
                },
                False,
            ),
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroupV2",
                    "log_stream": "testLogStream",
                    "subscription_filters": ["testFilter"],
                },
                False,
            ),
            # with log_group, log_stream, and subscription_filters
            # match 1, unmatch 2
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroup",
                    "log_stream": "testLogStreamV2",
                    "subscription_filters": ["testFilterV2"],
                },
                False,
            ),
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroupV2",
                    "log_stream": "testLogStream",
                    "subscription_filters": ["testFilterV2"],
                },
                False,
            ),
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroupV2",
                    "log_stream": "testLogStreamV2",
                    "subscription_filters": ["testFilter"],
                },
                False,
            ),
            # with log_group, log_stream, and subscription_filters
            # unmatch all
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroupV2",
                    "log_stream": "testLogStreamV2",
                    "subscription_filters": ["testFilterV2"],
                },
                False,
            ),
            # with log_group and log_stream
            # match all
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroup",
                    "log_stream": "testLogStream",
                },
                True,
            ),
            # with log_group and log_stream
            # match 1, unmatch 1
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroup",
                    "log_stream": "testLogStreamV2",
                },
                False,
            ),
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroupV2",
                    "log_stream": "testLogStream",
                },
                False,
            ),
            # with log_group and log_stream
            # unmatch all
            (
                "cloudWatchLogEvent.json",
                {
                    "func": lambda *_: None,
                    "log_group": "testLogGroupV2",
                    "log_stream": "testLogStreamV2",
                },
                False,
            ),
            # with log_group and subscription_filters
            # match all
            (
                "cloudWatchLogEvent.json",
                {"func": lambda *_: None, "log_group": "testLogGroup", "subscription_filters": ["testFilter"]},
                True,
            ),
            # with log_group and subscription_filters
            # match 1, unmatch 1
            (
                "cloudWatchLogEvent.json",
                {"func": lambda *_: None, "log_group": "testLogGroupV2", "subscription_filters": ["testFilter"]},
                False,
            ),
            (
                "cloudWatchLogEvent.json",
                {"func": lambda *_: None, "log_group": "testLogGroup", "subscription_filters": ["testFilterV2"]},
                False,
            ),
            # with log_group and subscription_filters
            # unmatch all
            (
                "cloudWatchLogEvent.json",
                {"func": lambda *_: None, "log_group": "testLogGroupV2", "subscription_filters": ["testFilterV2"]},
                False,
            ),
            # with log_stream and subscription_filters
            # match all
            (
                "cloudWatchLogEvent.json",
                {"func": lambda *_: None, "log_stream": "testLogStream", "subscription_filters": ["testFilter"]},
                True,
            ),
            # with log_stream and subscription_filters
            # match 1, unmatch 1
            (
                "cloudWatchLogEvent.json",
                {"func": lambda *_: None, "log_stream": "testLogStream", "subscription_filters": ["testFilterV2"]},
                False,
            ),
            (
                "cloudWatchLogEvent.json",
                {"func": lambda *_: None, "log_stream": "testLogStreamV2", "subscription_filters": ["testFilter"]},
                False,
            ),
            # with log_stream and subscription_filters
            # unmatch all
            (
                "cloudWatchLogEvent.json",
                {"func": lambda *_: None, "log_stream": "testLogStreamV2", "subscription_filters": ["testFilter"]},
                False,
            ),
            # with log_group
            ("cloudWatchLogEvent.json", {"func": lambda *_: None, "log_group": "testLogGroup"}, True),
            ("cloudWatchLogEvent.json", {"func": lambda *_: None, "log_group": "testLogGroupV2"}, False),
            # with log_stream
            ("cloudWatchLogEvent.json", {"func": lambda *_: None, "log_stream": "testLogStream"}, True),
            ("cloudWatchLogEvent.json", {"func": lambda *_: None, "log_stream": "testLogStreamV2"}, False),
            # with subscription_filters
            ("cloudWatchLogEvent.json", {"func": lambda *_: None, "subscription_filters": ["testFilter"]}, True),
            ("cloudWatchLogEvent.json", {"func": lambda *_: None, "subscription_filters": ["testFilterV2"]}, False),
        ],
    )
    def test_match_for_cloud_watch_logs_event(self, event_name, option_constructor, is_match):
        event = load_event(file_name=event_name)
        route = CloudWatchLogsRoute(**option_constructor)
        actual = route.match(event=event)
        if is_match:
            expected = route.func, CloudWatchLogsEvent(event)
            assert actual == expected
        else:
            assert actual is None

    @pytest.mark.parametrize(
        "event_name",
        [
            "activeMQEvent.json",
            "albEvent.json",
            "albEventPathTrailingSlash.json",
            "albMultiValueHeadersEvent.json",
            "albMultiValueQueryStringEvent.json",
            "apiGatewayAuthorizerRequestEvent.json",
            "apiGatewayAuthorizerTokenEvent.json",
            "apiGatewayAuthorizerV2Event.json",
            "apiGatewayProxyEvent.json",
            "apiGatewayProxyEventAnotherPath.json",
            "apiGatewayProxyEventNoOrigin.json",
            "apiGatewayProxyEventPathTrailingSlash.json",
            "apiGatewayProxyEventPrincipalId.json",
            "apiGatewayProxyEvent_noVersionAuth.json",
            "apiGatewayProxyOtherEvent.json",
            "apiGatewayProxyV2Event.json",
            "apiGatewayProxyV2EventPathTrailingSlash.json",
            "apiGatewayProxyV2Event_GET.json",
            "apiGatewayProxyV2IamEvent.json",
            "apiGatewayProxyV2LambdaAuthorizerEvent.json",
            "apiGatewayProxyV2OtherGetEvent.json",
            "apiGatewayProxyV2SchemaMiddlwareInvalidEvent.json",
            "apiGatewayProxyV2SchemaMiddlwareValidEvent.json",
            "apigatewayeSchemaMiddlwareInvalidEvent.json",
            "apigatewayeSchemaMiddlwareValidEvent.json",
            "appSyncAuthorizerEvent.json",
            "appSyncAuthorizerResponse.json",
            "appSyncBatchEvent.json",
            "appSyncDirectResolver.json",
            "appSyncResolverEvent.json",
            "awsConfigRuleConfigurationChanged.json",
            "awsConfigRuleOversizedConfiguration.json",
            "awsConfigRuleScheduled.json",
            "bedrockAgentEvent.json",
            "bedrockAgentEventWithPathParams.json",
            "bedrockAgentPostEvent.json",
            "cloudWatchAlarmEventCompositeMetric.json",
            "cloudWatchAlarmEventSingleMetric.json",
            "cloudWatchDashboardEvent.json",
            "cloudformationCustomResourceCreate.json",
            "cloudformationCustomResourceDelete.json",
            "cloudformationCustomResourceUpdate.json",
            "codeDeployLifecycleHookEvent.json",
            "codePipelineEvent.json",
            "codePipelineEventData.json",
            "codePipelineEventEmptyUserParameters.json",
            "codePipelineEventWithEncryptionKey.json",
            "cognitoCreateAuthChallengeEvent.json",
            "cognitoCustomEmailSenderEvent.json",
            "cognitoCustomMessageEvent.json",
            "cognitoCustomSMSSenderEvent.json",
            "cognitoDefineAuthChallengeEvent.json",
            "cognitoPostAuthenticationEvent.json",
            "cognitoPostConfirmationEvent.json",
            "cognitoPreAuthenticationEvent.json",
            "cognitoPreSignUpEvent.json",
            "cognitoPreTokenGenerationEvent.json",
            "cognitoPreTokenV2GenerationEvent.json",
            "cognitoUserMigrationEvent.json",
            "cognitoVerifyAuthChallengeResponseEvent.json",
            "connectContactFlowEventAll.json",
            "connectContactFlowEventMin.json",
            "dynamoStreamEvent.json",
            "eventBridgeEvent.json",
            "kafkaEventMsk.json",
            "kafkaEventSelfManaged.json",
            "kinesisFirehoseKinesisEvent.json",
            "kinesisFirehosePutEvent.json",
            "kinesisFirehoseSQSEvent.json",
            "kinesisStreamCloudWatchLogsEvent.json",
            "kinesisStreamEvent.json",
            "kinesisStreamEventOneRecord.json",
            "lambdaFunctionUrlEvent.json",
            "lambdaFunctionUrlEventPathTrailingSlash.json",
            "lambdaFunctionUrlEventWithHeaders.json",
            "lambdaFunctionUrlIAMEvent.json",
            "rabbitMQEvent.json",
            "s3BatchOperationEventSchemaV1.json",
            "s3BatchOperationEventSchemaV2.json",
            "s3Event.json",
            "s3EventBridgeNotificationObjectCreatedEvent.json",
            "s3EventBridgeNotificationObjectDeletedEvent.json",
            "s3EventBridgeNotificationObjectExpiredEvent.json",
            "s3EventBridgeNotificationObjectRestoreCompletedEvent.json",
            "s3EventDecodedKey.json",
            "s3EventDeleteObject.json",
            "s3EventGlacier.json",
            "s3ObjectEventIAMUser.json",
            "s3ObjectEventTempCredentials.json",
            "s3SqsEvent.json",
            "secretsManagerEvent.json",
            "sesEvent.json",
            "snsEvent.json",
            "snsSqsEvent.json",
            "snsSqsFifoEvent.json",
            "sqsDlqTriggerEvent.json",
            "sqsEvent.json",
            "vpcLatticeEvent.json",
            "vpcLatticeEventPathTrailingSlash.json",
            "vpcLatticeEventV2PathTrailingSlash.json",
            "vpcLatticeV2Event.json",
            "vpcLatticeV2EventWithHeaders.json",
        ],
    )
    def test_match_for_not_cloud_watch_logs_event(self, event_name):
        event = load_event(file_name=event_name)
        route = CloudWatchLogsRoute(func=None, log_group="testLogGroup")
        actual = route.match(event=event)
        assert actual is None
