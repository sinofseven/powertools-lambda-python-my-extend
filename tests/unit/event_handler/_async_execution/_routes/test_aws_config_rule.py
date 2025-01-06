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
        "event_name, option_constructor",
        [
            # other events
            ("activeMQEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("albEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("albEventPathTrailingSlash.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("albMultiValueHeadersEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("albMultiValueQueryStringEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayAuthorizerRequestEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayAuthorizerTokenEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayAuthorizerV2Event.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyEventAnotherPath.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyEventNoOrigin.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyEventPathTrailingSlash.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyEventPrincipalId.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyEvent_noVersionAuth.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyOtherEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyV2Event.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyV2EventPathTrailingSlash.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyV2Event_GET.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyV2IamEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyV2LambdaAuthorizerEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyV2OtherGetEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyV2SchemaMiddlwareInvalidEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apiGatewayProxyV2SchemaMiddlwareValidEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apigatewayeSchemaMiddlwareInvalidEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("apigatewayeSchemaMiddlwareValidEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("appSyncAuthorizerEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("appSyncAuthorizerResponse.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("appSyncBatchEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("appSyncDirectResolver.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("appSyncResolverEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("bedrockAgentEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("bedrockAgentEventWithPathParams.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("bedrockAgentPostEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cloudWatchAlarmEventCompositeMetric.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cloudWatchAlarmEventSingleMetric.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cloudWatchDashboardEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cloudWatchLogEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cloudWatchLogEventWithPolicyLevel.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cloudformationCustomResourceCreate.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cloudformationCustomResourceDelete.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cloudformationCustomResourceUpdate.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("codeDeployLifecycleHookEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("codePipelineEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("codePipelineEventData.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("codePipelineEventEmptyUserParameters.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("codePipelineEventWithEncryptionKey.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoCreateAuthChallengeEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoCustomEmailSenderEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoCustomMessageEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoCustomSMSSenderEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoDefineAuthChallengeEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoPostAuthenticationEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoPostConfirmationEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoPreAuthenticationEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoPreSignUpEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoPreTokenGenerationEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoPreTokenV2GenerationEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoUserMigrationEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("cognitoVerifyAuthChallengeResponseEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("connectContactFlowEventAll.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("connectContactFlowEventMin.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("dynamoStreamEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("eventBridgeEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("kafkaEventMsk.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("kafkaEventSelfManaged.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("kinesisFirehoseKinesisEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("kinesisFirehosePutEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("kinesisFirehoseSQSEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("kinesisStreamCloudWatchLogsEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("kinesisStreamEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("kinesisStreamEventOneRecord.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("lambdaFunctionUrlEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("lambdaFunctionUrlEventPathTrailingSlash.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("lambdaFunctionUrlEventWithHeaders.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("lambdaFunctionUrlIAMEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("rabbitMQEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3BatchOperationEventSchemaV1.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3BatchOperationEventSchemaV2.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3Event.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3EventBridgeNotificationObjectCreatedEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3EventBridgeNotificationObjectDeletedEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3EventBridgeNotificationObjectExpiredEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            (
                "s3EventBridgeNotificationObjectRestoreCompletedEvent.json",
                {"func": None, "rule_id": "config-rule-i1y1j1"},
            ),
            ("s3EventDecodedKey.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3EventDeleteObject.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3EventGlacier.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3ObjectEventIAMUser.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3ObjectEventTempCredentials.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("s3SqsEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("secretsManagerEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("sesEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("snsEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("snsSqsEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("snsSqsFifoEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("sqsDlqTriggerEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("sqsEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("vpcLatticeEvent.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("vpcLatticeEventPathTrailingSlash.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("vpcLatticeEventV2PathTrailingSlash.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("vpcLatticeV2Event.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            ("vpcLatticeV2EventWithHeaders.json", {"func": None, "rule_id": "config-rule-i1y1j1"}),
            # aws_config_rule_event, not match arn, without rule_name, rule_name_prefix, or rule_id
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": None, "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i1y1j1"},
            ),
            (
                "awsConfigRuleOversizedConfiguration.json",
                {
                    "func": None,
                    "arn": "/".join(
                        [
                            "arn:aws:config:us-east-2:123456789012:config-rule",
                            "config-rule-ec2-managed-instance-inventory-v2",
                        ],
                    ),
                },
            ),
            (
                "awsConfigRuleScheduled.json",
                {"func": None, "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-pdmyw3"},
            ),
            # awsConfigRuleConfigurationChanged.json, not match arn, with rule_name, rule_name_prefix, or rule_id
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i1y1j1",
                    "rule_name": "MyRule",
                },
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i1y1j1",
                    "rule_name_prefix": "My",
                },
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": None,
                    "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i1y1j1",
                    "rule_id": "config-rule-i9y8j9",
                },
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": None,
                    "rule_name": "MyRuleV2",
                    "rule_name_prefix": "My",
                    "rule_id": "config-rule-i9y8j9",
                },
            ),
            # awsConfigRuleConfigurationChanged.json, not match rule_name, without rule_name_prefix, or rule_id
            (
                "awsConfigRuleConfigurationChanged.json",
                {
                    "func": None,
                    "rule_name": "MyRuleV2",
                },
            ),
            # awsConfigRuleConfigurationChanged.json, not match rule_name, with rule_name_prefix, or rule_id
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": None, "rule_name": "MyRuleV2", "rule_name_prefix": "My"},
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": None, "rule_name": "MyRuleV2", "rule_id": "config-rule-i9y8j9"},
            ),
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": None, "rule_name": "MyRuleV2", "rule_name_prefix": "My", "rule_id": "config-rule-i9y8j9"},
            ),
            # awsConfigRuleConfigurationChanged.json, not match rule_name_prefix, without rule_id
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": None, "rule_name_prefix": "Me"},
            ),
            # awsConfigRuleConfigurationChanged.json, not match rule_name_prefix, with rule_id
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": None, "rule_name_prefix": "Me", "rule_id": "config-rule-i9y8j9"},
            ),
            # awsConfigRuleConfigurationChanged.json, not match rule_id
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": None, "rule_id": "config-rule-i1y1j1"},
            ),
        ],
    )
    def test_match_false(self, event_name, option_constructor):
        route = AwsConfigRuleRoute(**option_constructor)
        event = load_event(file_name=event_name)
        actual = route.match(event=event)
        assert actual is None

    @pytest.mark.parametrize(
        "event_name, option_constructor",
        [
            # awsConfigRuleConfigurationChanged.json, match arn
            (
                "awsConfigRuleConfigurationChanged.json",
                {"func": None, "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-i9y8j9"},
            ),
            # awsConfigRuleConfigurationChanged.json, match rule_name
            ("awsConfigRuleConfigurationChanged.json", {"func": None, "rule_name": "MyRule"}),
            # awsConfigRuleConfigurationChanged.json, match rule_name_prefix
            ("awsConfigRuleConfigurationChanged.json", {"func": None, "rule_name_prefix": "MyR"}),
            # awsConfigRuleConfigurationChanged.json, match rule_id
            ("awsConfigRuleConfigurationChanged.json", {"func": None, "rule_id": "config-rule-i9y8j9"}),
            # awsConfigRuleOversizedConfiguration.json, match arn
            (
                "awsConfigRuleOversizedConfiguration.json",
                {
                    "func": None,
                    "arn": "/".join(
                        [
                            "arn:aws:config:us-east-2:123456789012:config-rule",
                            "config-rule-ec2-managed-instance-inventory",
                        ],
                    ),
                },
            ),
            # awsConfigRuleOversizedConfiguration.json, match rule_name
            (
                "awsConfigRuleOversizedConfiguration.json",
                {"func": None, "rule_name": "change-triggered-config-rule"},
            ),
            # awsConfigRuleOversizedConfiguration.json, match rule_name_prefix
            (
                "awsConfigRuleOversizedConfiguration.json",
                {"func": None, "rule_name_prefix": "change-t"},
            ),
            # awsConfigRuleOversizedConfiguration.json, match rule_id
            (
                "awsConfigRuleOversizedConfiguration.json",
                {"func": None, "rule_id": "config-rule-0123456"},
            ),
            # awsConfigRuleScheduled.json, match arn
            (
                "awsConfigRuleScheduled.json",
                {"func": None, "arn": "arn:aws:config:us-east-1:0123456789012:config-rule/config-rule-pdmyw1"},
            ),
            # awsConfigRuleScheduled.json, match rule_name
            ("awsConfigRuleScheduled.json", {"func": None, "rule_name": "rule-ec2-test"}),
            # awsConfigRuleScheduled.json, match rule_name_prefix
            ("awsConfigRuleScheduled.json", {"func": None, "rule_name_prefix": "rule-e"}),
            # awsConfigRuleScheduled.json, match rule_id
            ("awsConfigRuleScheduled.json", {"func": None, "rule_id": "config-rule-pdmyw1"}),
        ],
    )
    def test_match_true(self, event_name, option_constructor):
        route = AwsConfigRuleRoute(**option_constructor)
        event = load_event(file_name=event_name)
        expect = (route.func, AWSConfigRuleEvent(event))
        actual = route.match(event=event)
        assert actual == expect
