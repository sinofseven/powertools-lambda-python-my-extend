import pytest

from aws_lambda_powertools.event_handler.async_execution.routes.cloud_watch_alarm import (
    CloudWatchAlarmRoute,
)
from aws_lambda_powertools.utilities.data_classes.cloud_watch_alarm_event import (
    CloudWatchAlarmEvent,
)
from tests.functional.utils import load_event


class TestCloudWatchAlarmRoute:
    def test_constructor_error(self):
        with pytest.raises(ValueError):
            CloudWatchAlarmRoute(func=None)

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            (
                {"func": None, "arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.Main"},
                {"arn": None},
                False,
            ),
            (
                {"func": None, "arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.Main"},
                {"arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.Main"},
                True,
            ),
            (
                {"func": None, "arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.MainV2"},
                {"arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.Main"},
                False,
            ),
            (
                {"func": None, "alarm_name": "SuppressionDemo.Main"},
                {"arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.Main"},
                False,
            ),
        ],
    )
    def test_is_target_with_arn(self, option_constructor, option_func, expected):
        route = CloudWatchAlarmRoute(**option_constructor)
        actual = route.is_target_with_arn(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            # with alarm_name and alarm_name_prefix
            # match all
            (
                {"func": None, "alarm_name": "CompositeDemo.Main", "alarm_name_prefix": "CompositeDemo.M"},
                {"alarm_name": "CompositeDemo.Main"},
                True,
            ),
            # with alarm_name and alarm_name_prefix
            # match 1, unmatch 1
            (
                {"func": None, "alarm_name": "CompositeDemo.Main", "alarm_name_prefix": "ompositeDemo.M"},
                {"alarm_name": "CompositeDemo.Main"},
                True,
            ),
            (
                {"func": None, "alarm_name": "CompositeDemo.MainV2", "alarm_name_prefix": "CompositeDemo.M"},
                {"alarm_name": "CompositeDemo.Main"},
                False,
            ),
            # with alarm_name and alarm_name_prefix
            # unmatch all
            (
                {"func": None, "alarm_name": "CompositeDemo.MainV2", "alarm_name_prefix": "ompositeDemo.M"},
                {"alarm_name": "CompositeDemo.Main"},
                False,
            ),
            # with alarm_name
            (
                {
                    "func": None,
                    "alarm_name": "CompositeDemo.Main",
                },
                {"alarm_name": "CompositeDemo.Main"},
                True,
            ),
            (
                {
                    "func": None,
                    "alarm_name": "CompositeDemo.MainV2",
                },
                {"alarm_name": "CompositeDemo.Main"},
                False,
            ),
            # with alarm_name_prefix
            ({"func": None, "alarm_name_prefix": "CompositeDemo.M"}, {"alarm_name": "CompositeDemo.Main"}, True),
            ({"func": None, "alarm_name_prefix": "ompositeDemo.M"}, {"alarm_name": "CompositeDemo.Main"}, False),
            # without alarm_name and alarm_name_prefix
            (
                {"func": None, "arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.Main"},
                {"alarm_name": "CompositeDemo.Main"},
                False,
            ),
            # without alarm_name at option_func
            ({"func": None, "alarm_name_prefix": "ompositeDemo.M"}, {"alarm_name": None}, False),
        ],
    )
    def test_is_target_with_alarm_name(self, option_constructor, option_func, expected):
        route = CloudWatchAlarmRoute(**option_constructor)
        actual = route.is_target_with_alarm_name(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "event_name, option_constructor, is_match",
        [
            # with arn and alarm_name
            # match all
            (
                "cloudWatchAlarmEventCompositeMetric.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.Main",
                    "alarm_name": "CompositeDemo.Main",
                },
                True,
            ),
            # with arn and alarm_name
            # match 1, unmatch 1
            (
                "cloudWatchAlarmEventCompositeMetric.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.MainV2",
                    "alarm_name": "CompositeDemo.Main",
                },
                False,
            ),
            (
                "cloudWatchAlarmEventCompositeMetric.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.Main",
                    "alarm_name": "CompositeDemo.MainV2",
                },
                False,
            ),
            # with arn and alarm_name
            # unmatch all
            (
                "cloudWatchAlarmEventCompositeMetric.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.MainV2",
                    "alarm_name": "CompositeDemo.MainV2",
                },
                False,
            ),
            # with arn
            (
                "cloudWatchAlarmEventCompositeMetric.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.Main",
                },
                True,
            ),
            (
                "cloudWatchAlarmEventCompositeMetric.json",
                {
                    "func": lambda *_: None,
                    "arn": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.MainV2",
                },
                False,
            ),
            # with alarm_name
            (
                "cloudWatchAlarmEventCompositeMetric.json",
                {"func": lambda *_: None, "alarm_name": "CompositeDemo.Main"},
                True,
            ),
            (
                "cloudWatchAlarmEventCompositeMetric.json",
                {"func": lambda *_: None, "alarm_name": "CompositeDemo.MainV2"},
                False,
            ),
        ],
    )
    def test_match_for_cloud_watch_alarm_event(self, event_name, option_constructor, is_match):
        event = load_event(file_name=event_name)
        route = CloudWatchAlarmRoute(**option_constructor)
        actual = route.match(event=event)
        if is_match:
            expected = route.func, CloudWatchAlarmEvent(event)
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
            "cloudWatchDashboardEvent.json",
            "cloudWatchLogEvent.json",
            "cloudWatchLogEventWithPolicyLevel.json",
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
    def test_match_for_not_cloud_watch_alarm_event(self, event_name):
        event = load_event(file_name=event_name)
        route = CloudWatchAlarmRoute(
            func=None,
            arn="arn:aws:cloudwatch:us-east-1:111122223333:alarm:SuppressionDemo.Main",
        )
        actual = route.match(event=event)
        assert actual is None
