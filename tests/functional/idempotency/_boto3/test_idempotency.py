import copy
import dataclasses
import datetime
import warnings
from typing import Any, Optional
from unittest.mock import MagicMock, Mock

import jmespath
import pytest
from botocore import stub
from botocore.config import Config
from pytest import FixtureRequest
from pytest_mock import MockerFixture

from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEventV2,
    event_source,
)
from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
    idempotent_function,
)
from aws_lambda_powertools.utilities.idempotency.base import (
    MAX_RETRIES,
    IdempotencyHandler,
    _prepare_data,
)
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyAlreadyInProgressError,
    IdempotencyInconsistentStateError,
    IdempotencyInvalidStatusError,
    IdempotencyKeyError,
    IdempotencyNoSerializationModelError,
    IdempotencyPersistenceLayerError,
    IdempotencyValidationError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    BasePersistenceLayer,
    DataRecord,
)
from aws_lambda_powertools.utilities.idempotency.serialization.custom_dict import (
    CustomDictSerializer,
)
from aws_lambda_powertools.utilities.idempotency.serialization.dataclass import (
    DataclassSerializer,
)
from aws_lambda_powertools.utilities.validation import envelopes, validator
from aws_lambda_powertools.warnings import PowertoolsUserWarning
from tests.functional.idempotency.utils import (
    build_idempotency_put_item_response_stub,
    build_idempotency_put_item_stub,
    build_idempotency_update_item_stub,
    hash_idempotency_key,
)
from tests.functional.utils import json_serialize, load_event

TABLE_NAME = "TEST_TABLE"
TESTS_MODULE_PREFIX = "test-func.tests.functional.idempotency._boto3.test_idempotency"


# Using parametrize to run test twice, with two separate instances of persistence store. One instance with caching
# enabled, and one without.
@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_already_completed(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    hashed_idempotency_key,
    serialized_lambda_response,
    deserialized_lambda_response,
    lambda_context,
):
    """
    Test idempotent decorator where event with matching event key has already been successfully processed
    """

    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": serialized_lambda_response},
            "status": {"S": "COMPLETED"},
        },
    }
    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=ddb_response)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception

    lambda_resp = lambda_handler(lambda_apigw_event, lambda_context)
    assert lambda_resp == deserialized_lambda_response

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_in_progress(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    lambda_response,
    timestamp_future,
    hashed_idempotency_key,
    lambda_context,
):
    """
    Test idempotent decorator where lambda_handler is already processing an event with matching event key
    """

    stubber = stub.Stubber(persistence_store.client)

    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "status": {"S": "INPROGRESS"},
        },
    }

    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=ddb_response)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    with pytest.raises(IdempotencyAlreadyInProgressError) as ex:
        lambda_handler(lambda_apigw_event, lambda_context)
        assert (
            ex.value.args[0] == "Execution already in progress with idempotency key: "
            "body=a3edd699125517bb49d562501179ecbd"
        )

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_in_progress_with_cache(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    lambda_response,
    timestamp_future,
    hashed_idempotency_key,
    mocker,
    lambda_context,
):
    """
    Test idempotent decorator where lambda_handler is already processing an event with matching event key, cache
    enabled.
    """
    save_to_cache_spy = mocker.spy(persistence_store, "_save_to_cache")
    retrieve_from_cache_spy = mocker.spy(persistence_store, "_retrieve_from_cache")
    stubber = stub.Stubber(persistence_store.client)

    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "status": {"S": "INPROGRESS"},
        },
    }

    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=ddb_response)

    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=copy.deepcopy(ddb_response))

    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=copy.deepcopy(ddb_response))

    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    loops = 3
    for _ in range(loops):
        with pytest.raises(IdempotencyAlreadyInProgressError) as ex:
            lambda_handler(lambda_apigw_event, lambda_context)
            assert (
                ex.value.args[0] == "Execution already in progress with idempotency key: "
                "body=a3edd699125517bb49d562501179ecbd"
            )

    assert retrieve_from_cache_spy.call_count == loops
    retrieve_from_cache_spy.assert_called_with(idempotency_key=hashed_idempotency_key)

    save_to_cache_spy.assert_called()
    assert persistence_store._cache.get(hashed_idempotency_key) is None

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_first_execution(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    expected_params_update_item,
    expected_params_put_item,
    lambda_response,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key
    """

    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_expired(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    lambda_response,
    expected_params_update_item,
    expected_params_put_item,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is called with an event it successfully handled already, but outside of the
    expiry window
    """

    stubber = stub.Stubber(persistence_store.client)

    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_first_execution_cached(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    expected_params_update_item,
    expected_params_put_item,
    lambda_response,
    hashed_idempotency_key,
    mocker,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key. Ensure
    result is cached locally on the persistence store instance.
    """
    save_to_cache_spy = mocker.spy(persistence_store, "_save_to_cache")
    retrieve_from_cache_spy = mocker.spy(persistence_store, "_retrieve_from_cache")
    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, lambda_context)

    retrieve_from_cache_spy.assert_called_once()
    save_to_cache_spy.assert_called_once()
    assert save_to_cache_spy.call_args[1]["data_record"].status == "COMPLETED"
    assert persistence_store._cache.get(hashed_idempotency_key).status == "COMPLETED"

    # This lambda call should not call AWS API
    lambda_handler(lambda_apigw_event, lambda_context)
    assert retrieve_from_cache_spy.call_count == 3
    retrieve_from_cache_spy.assert_called_with(idempotency_key=hashed_idempotency_key)

    # This assertion fails if an AWS API operation was called more than once
    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True, "event_key_jmespath": "body"}], indirect=True)
def test_idempotent_lambda_first_execution_event_mutation(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    lambda_response,
    lambda_context,
):
    """
    Test idempotent decorator where lambda_handler mutates the event.
    Ensures we're passing data by value, not reference.
    """
    event = copy.deepcopy(lambda_apigw_event)
    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {}
    stubber.add_response(
        "put_item",
        ddb_response,
        build_idempotency_put_item_stub(data=event["body"]),
    )
    stubber.add_response(
        "update_item",
        ddb_response,
        build_idempotency_update_item_stub(data=event["body"], handler_response=lambda_response),
    )
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        event.pop("body")  # remove exact key we're using for idempotency
        return lambda_response

    lambda_handler(event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_exception(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    hashed_idempotency_key,
    expected_params_put_item,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception which is retryable.
    """

    # Create a new provider

    # Stub the boto3 client
    stubber = stub.Stubber(persistence_store.client)

    ddb_response = {}
    expected_params_delete_item = {"TableName": TABLE_NAME, "Key": {"id": {"S": hashed_idempotency_key}}}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("delete_item", ddb_response, expected_params_delete_item)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception("Something went wrong!")

    with pytest.raises(Exception, match="Something went wrong!"):
        lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize(
    "idempotency_config",
    [
        {"use_local_cache": False, "payload_validation_jmespath": "requestContext"},
    ],
    indirect=True,
)
def test_idempotent_lambda_already_completed_with_validation_bad_payload(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    hashed_validation_key,
    lambda_context,
):
    """
    Test idempotent decorator where event with matching event key has already been successfully processed
    """

    # GIVEN an idempotent record already exists for the same transaction
    # and payload validation was enabled ('validation' key)
    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "COMPLETED"},
            "validation": {"S": hashed_validation_key},
        },
    }
    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=ddb_response)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    # WHEN the subsequent request is the same but validated field is tampered
    lambda_apigw_event["requestContext"]["accountId"] += "1"  # Alter the request payload

    # THEN we should raise
    with pytest.raises(IdempotencyValidationError):
        lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_expired_during_request(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_expired,
    lambda_response,
    hashed_idempotency_key,
    mocker,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is called with an event it successfully handled already. Persistence store
    returns inconsistent/rapidly changing result between put_item and get_item calls.
    """

    stubber = stub.Stubber(persistence_store.client)

    ddb_response_get_item = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_expired},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "INPROGRESS"},
        },
    }
    ddb_response_get_item_missing = {}
    expected_params_get_item = {
        "TableName": TABLE_NAME,
        "Key": {"id": {"S": hashed_idempotency_key}},
        "ConsistentRead": True,
    }

    # Simulate record repeatedly changing state between put_item and get_item
    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response_get_item, expected_params_get_item)

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response_get_item_missing)

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", copy.deepcopy(ddb_response_get_item), copy.deepcopy(expected_params_get_item))

    stubber.activate()

    submethod_mocked = mocker.patch.object(persistence_store, "boto3_supports_condition_check_failure")
    submethod_mocked.return_value = False

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    # max retries exceeded before get_item and put_item agree on item state, so exception gets raised
    with pytest.raises(IdempotencyInconsistentStateError):
        lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize(
    "idempotency_config",
    [{"use_local_cache": True, "payload_validation_jmespath": "requestContext"}],
    indirect=True,
)
def test_idempotent_lambda_already_completed_with_validation_bad_payload_from_local_cache(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    hashed_validation_key,
    lambda_context,
):
    """
    Test idempotent decorator where event with matching event key has already been successfully processed
    Fetching record from local cache
    """

    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "COMPLETED"},
            "validation": {"S": hashed_validation_key},
        },
    }

    expected_params = {"TableName": TABLE_NAME, "Key": {"id": {"S": hashed_idempotency_key}}, "ConsistentRead": True}

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response, expected_params)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    with pytest.raises(IdempotencyValidationError):
        lambda_apigw_event["requestContext"]["accountId"] += "1"  # Alter the request payload
        lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_persistence_exception_deleting(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    expected_params_put_item,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception which is retryable.
    """
    stubber = stub.Stubber(persistence_store.client)

    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_client_error("delete_item", "UnrecoverableError")
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception("Something went wrong!")

    with pytest.raises(IdempotencyPersistenceLayerError) as exc:
        lambda_handler(lambda_apigw_event, lambda_context)

    assert exc.value.args[0] == "Failed to delete record from idempotency store"
    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_persistence_exception_updating(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    expected_params_put_item,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception which is retryable.
    """
    stubber = stub.Stubber(persistence_store.client)

    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_client_error("update_item", "UnrecoverableError")
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return {"message": "success!"}

    with pytest.raises(IdempotencyPersistenceLayerError) as exc:
        lambda_handler(lambda_apigw_event, lambda_context)

    assert exc.value.args[0] == "Failed to update record state to success in idempotency store"
    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_persistence_exception_getting(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception which is retryable.
    """
    stubber = stub.Stubber(persistence_store.client)

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_client_error("get_item", "UnexpectedException")
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return {"message": "success!"}

    with pytest.raises(IdempotencyPersistenceLayerError) as exc:
        lambda_handler(lambda_apigw_event, lambda_context)

    assert exc.value.args[0] == "Failed to get record from idempotency store"
    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize(
    "idempotency_config",
    [
        {"use_local_cache": False, "payload_validation_jmespath": "requestContext"},
        {"use_local_cache": True, "payload_validation_jmespath": "requestContext"},
    ],
    indirect=True,
)
def test_idempotent_lambda_first_execution_with_validation(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    expected_params_update_item_with_validation,
    expected_params_put_item_with_validation,
    lambda_response,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key
    """
    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item_with_validation)
    stubber.add_response("update_item", ddb_response, expected_params_update_item_with_validation)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize(
    "config_without_jmespath",
    [{"use_local_cache": False}, {"use_local_cache": True}],
    indirect=True,
)
def test_idempotent_lambda_with_validator_util(
    config_without_jmespath: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    serialized_lambda_response,
    deserialized_lambda_response,
    hashed_idempotency_key_with_envelope,
    mock_function,
    lambda_context,
):
    """
    Test idempotent decorator where event with matching event key has already been succesfully processed, using the
    validator utility to unwrap the event
    """

    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key_with_envelope},
            "expiration": {"N": timestamp_future},
            "data": {"S": serialized_lambda_response},
            "status": {"S": "COMPLETED"},
        },
    }

    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=ddb_response)
    stubber.activate()

    @validator(envelope=envelopes.API_GATEWAY_HTTP)
    @idempotent(config=config_without_jmespath, persistence_store=persistence_store)
    def lambda_handler(event, context):
        mock_function()
        return "shouldn't get here!"

    mock_function.assert_not_called()
    lambda_resp = lambda_handler(lambda_apigw_event, lambda_context)
    assert lambda_resp == deserialized_lambda_response

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_expires_in_progress_before_expire(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    lambda_context,
):
    stubber = stub.Stubber(persistence_store.client)

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")

    now = datetime.datetime.now()
    period = datetime.timedelta(seconds=5)
    timestamp_expires_in_progress = int((now + period).timestamp() * 1000)

    expected_params_get_item = {
        "TableName": TABLE_NAME,
        "Key": {"id": {"S": hashed_idempotency_key}},
        "ConsistentRead": True,
    }
    ddb_response_get_item = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "in_progress_expiration": {"N": str(timestamp_expires_in_progress)},
            "data": {"S": '{"message": "test", "statusCode": 200'},
            "status": {"S": "INPROGRESS"},
        },
    }
    stubber.add_response("get_item", ddb_response_get_item, expected_params_get_item)

    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    with pytest.raises(IdempotencyAlreadyInProgressError):
        lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_expires_in_progress_after_expire(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    lambda_context,
):
    stubber = stub.Stubber(persistence_store.client)

    for _ in range(MAX_RETRIES + 1):
        stubber.add_client_error("put_item", "ConditionalCheckFailedException")

        one_second_ago = datetime.datetime.now() - datetime.timedelta(seconds=1)
        expected_params_get_item = {
            "TableName": TABLE_NAME,
            "Key": {"id": {"S": hashed_idempotency_key}},
            "ConsistentRead": True,
        }
        ddb_response_get_item = {
            "Item": {
                "id": {"S": hashed_idempotency_key},
                "expiration": {"N": timestamp_future},
                "in_progress_expiration": {"N": str(int(one_second_ago.timestamp() * 1000))},
                "data": {"S": '{"message": "test", "statusCode": 200'},
                "status": {"S": "INPROGRESS"},
            },
        }
        stubber.add_response("get_item", ddb_response_get_item, expected_params_get_item)

    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    with pytest.raises(IdempotencyInconsistentStateError):
        lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotent_lambda_expires_in_progress_unavailable_remaining_time():
    mock_event = {"data": "value"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_lambda_expires_in_progress_unavailable_remaining_time.<locals>.function#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}

    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
    def function(record):
        return expected_result

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")
        function(record=mock_event)
        assert len(w) == 1
        assert (
            str(w[-1].message)
            == "Couldn't determine the remaining time left. Did you call register_lambda_context on IdempotencyConfig?"
        )


def test_data_record_invalid_status_value():
    data_record = DataRecord("key", status="UNSUPPORTED_STATUS")
    with pytest.raises(IdempotencyInvalidStatusError) as e:
        _ = data_record.status

    assert e.value.args[0] == "UNSUPPORTED_STATUS"


def test_data_record_json_to_dict_mapping():
    # GIVEN a data record with status "INPROGRESS" and provided response data
    data_record = DataRecord(
        "key",
        status="INPROGRESS",
        response_data='{"body": "execution finished","statusCode": "200"}',
    )

    # WHEN translating response data to dictionary
    response_data = data_record.response_json_as_dict()

    # THEN return dictionary
    assert isinstance(response_data, dict)


def test_data_record_json_to_dict_mapping_when_response_data_none():
    # GIVEN a data record with status "INPROGRESS" and not set response data
    data_record = DataRecord("key", status="INPROGRESS", response_data=None)
    # WHEN translating response data to dictionary
    response_data = data_record.response_json_as_dict()

    # THEN return null value
    assert response_data is None


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_handler_for_status_expired_data_record(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
):
    idempotency_handler = IdempotencyHandler(
        function=lambda a: a,
        function_payload={},
        config=idempotency_config,
        persistence_store=persistence_store,
    )
    data_record = DataRecord("key", status="EXPIRED", response_data=None)

    with pytest.raises(IdempotencyInconsistentStateError):
        idempotency_handler._handle_for_status(data_record)


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_handler_for_status_inprogress_data_record_inconsistent(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
):
    idempotency_handler = IdempotencyHandler(
        function=lambda a: a,
        function_payload={},
        config=idempotency_config,
        persistence_store=persistence_store,
    )

    now = datetime.datetime.now()
    period = datetime.timedelta(milliseconds=100)
    timestamp = int((now - period).timestamp() * 1000)
    data_record = DataRecord("key", in_progress_expiry_timestamp=timestamp, status="INPROGRESS", response_data=None)

    with pytest.raises(IdempotencyInconsistentStateError):
        idempotency_handler._handle_for_status(data_record)


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_handler_for_status_inprogress_data_record_consistent(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
):
    idempotency_handler = IdempotencyHandler(
        function=lambda a: a,
        function_payload={},
        config=idempotency_config,
        persistence_store=persistence_store,
    )

    now = datetime.datetime.now()
    period = datetime.timedelta(milliseconds=100)
    timestamp = int((now + period).timestamp() * 1000)
    data_record = DataRecord("key", in_progress_expiry_timestamp=timestamp, status="INPROGRESS", response_data=None)

    with pytest.raises(IdempotencyAlreadyInProgressError):
        idempotency_handler._handle_for_status(data_record)


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_in_progress_never_saved_to_cache(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
):
    # GIVEN a data record with status "INPROGRESS"
    # and persistence_store has use_local_cache = True
    persistence_store.configure(idempotency_config)
    data_record = DataRecord("key", status="INPROGRESS")

    # WHEN saving to local cache
    persistence_store._save_to_cache(data_record)

    # THEN don't save to local cache
    assert persistence_store._cache.get("key") is None


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}], indirect=True)
def test_user_local_disabled(idempotency_config: IdempotencyConfig, persistence_store: DynamoDBPersistenceLayer):
    # GIVEN a persistence_store with use_local_cache = False
    persistence_store.configure(idempotency_config)

    # WHEN calling any local cache options
    data_record = DataRecord("key", status="COMPLETED")
    try:
        persistence_store._save_to_cache(data_record)
        cache_value = persistence_store._retrieve_from_cache("key")
        assert cache_value is None
        persistence_store._delete_from_cache("key")
    except AttributeError as e:
        pytest.fail(f"AttributeError should not be raised: {e}")

    # THEN raise AttributeError
    # AND don't have a _cache attribute
    assert not hasattr("persistence_store", "_cache")


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_delete_from_cache_when_empty(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
):
    # GIVEN use_local_cache is True AND the local cache is empty
    persistence_store.configure(idempotency_config)

    try:
        # WHEN we _delete_from_cache
        persistence_store._delete_from_cache("key_does_not_exist")
    except KeyError:
        # THEN we should not get a KeyError
        pytest.fail("KeyError should not happen")


def test_is_missing_idempotency_key():
    # GIVEN an empty tuple THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key(())
    # GIVEN an empty list THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key([])
    # GIVEN an empty dictionary THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key({})
    # GIVEN an empty str THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key("")
    # GIVEN None THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key(None)
    # GIVEN a list of Nones THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key([None, None])
    # GIVEN a tuples of Nones THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key((None, None))
    # GIVEN a dict of Nones THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key({None: None})

    # GIVEN True THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key(True) is False
    # GIVEN False THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key(False) is False
    # GIVEN number 0 THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key(0) is False
    # GIVEN number 0.0 THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key(0.0) is False
    # GIVEN a str THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key("Value") is False
    # GIVEN str "False" THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key("False") is False
    # GIVEN a number THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key(1000) is False
    # GIVEN a float THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key(10.01) is False
    # GIVEN a list with some items THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key([None, "Value"]) is False


@pytest.mark.parametrize(
    "idempotency_config",
    [{"use_local_cache": False, "event_key_jmespath": "body"}],
    indirect=True,
)
def test_default_no_raise_on_missing_idempotency_key(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
):
    # GIVEN a persistence_store with use_local_cache = False and event_key_jmespath = "body"
    function_name = "foo"
    persistence_store.configure(idempotency_config, function_name)
    assert persistence_store.use_local_cache is False
    assert "body" in persistence_store.event_key_jmespath

    # WHEN getting the hashed idempotency key for an event with no `body` key
    hashed_key = persistence_store._get_hashed_idempotency_key({})

    # THEN return the hash of None
    assert hashed_key is None


@pytest.mark.parametrize(
    "idempotency_config",
    [
        {"use_local_cache": False, "event_key_jmespath": "[body, x]"},
    ],
    indirect=True,
)
def test_raise_on_no_idempotency_key(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
):
    # GIVEN a persistence_store with raise_on_no_idempotency_key and no idempotency key in the request
    persistence_store.configure(idempotency_config)
    persistence_store.raise_on_no_idempotency_key = True
    assert persistence_store.use_local_cache is False
    assert "body" in persistence_store.event_key_jmespath

    # WHEN getting the hashed idempotency key for an event with no `body` key
    with pytest.raises(IdempotencyKeyError) as excinfo:
        persistence_store._get_hashed_idempotency_key({})

    # THEN raise IdempotencyKeyError error
    assert "No data found to create a hashed idempotency_key" in str(excinfo.value)


@pytest.mark.parametrize(
    "idempotency_config",
    [
        {
            "use_local_cache": False,
            "event_key_jmespath": "[requestContext.authorizer.claims.sub, powertools_json(body).id]",
        },
    ],
    indirect=True,
)
def test_jmespath_with_powertools_json(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
):
    # GIVEN an event_key_jmespath with powertools_json custom function
    persistence_store.configure(idempotency_config, "handler")
    sub_attr_value = "cognito_user"
    static_pk_value = "some_key"
    expected_value = [sub_attr_value, static_pk_value]
    api_gateway_proxy_event = {
        "requestContext": {"authorizer": {"claims": {"sub": sub_attr_value}}},
        "body": json_serialize({"id": static_pk_value}),
    }

    # WHEN calling _get_hashed_idempotency_key
    result = persistence_store._get_hashed_idempotency_key(api_gateway_proxy_event)

    # THEN the hashed idempotency key should match the extracted values generated hash
    assert result == "test-func.handler#" + persistence_store._generate_hash(expected_value)


@pytest.mark.parametrize("config_with_jmespath_options", ["powertools_json(data).payload"], indirect=True)
def test_custom_jmespath_function_overrides_builtin_functions(
    config_with_jmespath_options: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
):
    # GIVEN a persistence store with a custom jmespath_options
    # AND use a builtin Powertools for AWS Lambda (Python) custom function
    persistence_store.configure(config_with_jmespath_options)

    with pytest.raises(jmespath.exceptions.UnknownFunctionError, match="Unknown function: powertools_json()"):
        # WHEN calling _get_hashed_idempotency_key
        # THEN raise unknown function
        persistence_store._get_hashed_idempotency_key({})


def test_idempotent_lambda_save_inprogress_error(persistence_store: DynamoDBPersistenceLayer, lambda_context):
    # GIVEN a miss configured persistence layer
    # like no table was created for the idempotency persistence layer
    stubber = stub.Stubber(persistence_store.client)
    service_error_code = "ResourceNotFoundException"
    service_message = "Custom message"

    exception_message = "Failed to save in progress record to idempotency store"
    exception_details = (
        f"An error occurred ({service_error_code}) when calling the PutItem operation: {service_message}"
    )

    stubber.add_client_error(
        "put_item",
        service_error_code,
        service_message,
    )
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        return {}

    # WHEN handling the idempotent call
    # AND save_inprogress raises a ClientError
    with pytest.raises(IdempotencyPersistenceLayerError) as e:
        lambda_handler({"data": "some"}, lambda_context)

    # THEN idempotent should raise an IdempotencyPersistenceLayerError
    # AND append downstream exception details
    stubber.assert_no_pending_responses()
    stubber.deactivate()
    assert exception_message == e.value.args[0]
    assert isinstance(e.value.args[1], Exception)
    assert exception_details in e.value.args[1].args
    assert f"{exception_message} - ({exception_details})" in str(e.value)


def test_handler_raise_idempotency_key_error(persistence_store: DynamoDBPersistenceLayer, lambda_context):
    # GIVEN raise_on_no_idempotency_key is True
    idempotency_config = IdempotencyConfig(event_key_jmespath="idemKey", raise_on_no_idempotency_key=True)

    # WHEN handling the idempotent call
    # AND save_inprogress raises a IdempotencyKeyError
    @idempotent(persistence_store=persistence_store, config=idempotency_config)
    def handler(event, context):
        raise ValueError("Should not be raised")

    # THEN idempotent should re-raise the IdempotencyKeyError
    with pytest.raises(IdempotencyKeyError) as e:
        handler({}, lambda_context)

    assert "No data found to create a hashed idempotency_key" == e.value.args[0]


class MockPersistenceLayer(BasePersistenceLayer):
    def __init__(self, expected_idempotency_key: str):
        self.expected_idempotency_key = expected_idempotency_key
        super().__init__()

    def _put_record(self, data_record: DataRecord) -> None:
        assert data_record.idempotency_key == self.expected_idempotency_key

    def _update_record(self, data_record: DataRecord) -> None:
        assert data_record.idempotency_key == self.expected_idempotency_key

    def _get_record(self, idempotency_key) -> DataRecord: ...

    def _delete_record(self, data_record: DataRecord) -> None: ...


def test_idempotent_lambda_event_source(lambda_context):
    # Scenario to validate that we can use the event_source decorator before or after the idempotent decorator
    mock_event = load_event("apiGatewayProxyV2Event.json")
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_lambda_event_source.<locals>.lambda_handler#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(idempotency_key)
    expected_result = {"message": "Foo"}

    # GIVEN an event_source decorator
    # AND then an idempotent decorator
    @event_source(data_class=APIGatewayProxyEventV2)
    @idempotent(persistence_store=persistence_layer)
    def lambda_handler(event, _):
        assert isinstance(event, APIGatewayProxyEventV2)
        return expected_result

    # WHEN calling the lambda handler
    result = lambda_handler(mock_event, lambda_context)
    # THEN we expect the handler to execute successfully
    assert result == expected_result


def test_idempotent_function():
    # Scenario to validate we can use idempotent_function with any function
    mock_event = {"data": "value"}
    idempotency_key = (
        f"{TESTS_MODULE_PREFIX}.test_idempotent_function.<locals>.record_handler#{hash_idempotency_key(mock_event)}"
    )
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}

    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
    def record_handler(record):
        return expected_result

    # WHEN calling the function
    result = record_handler(record=mock_event)
    # THEN we expect the function to execute successfully
    assert result == expected_result


def test_idempotent_function_serialization_custom_dict():
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_custom_dict.<locals>.record_handler#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    to_dict_called = False
    from_dict_called = False

    def to_dict(data):
        nonlocal to_dict_called
        to_dict_called = True
        return data

    def from_dict(data):
        nonlocal from_dict_called
        from_dict_called = True
        return data

    expected_result = {"message": "Foo"}
    output_serializer = CustomDictSerializer(
        to_dict=to_dict,
        from_dict=from_dict,
    )

    @idempotent_function(
        persistence_store=persistence_layer,
        data_keyword_argument="record",
        config=config,
        output_serializer=output_serializer,
    )
    def record_handler(record):
        return expected_result

    record_handler(record=mock_event)
    assert to_dict_called
    record_handler(record=mock_event)
    assert from_dict_called


def test_idempotent_function_serialization_no_response():
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_no_response.<locals>.record_handler#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    to_dict_called = False
    from_dict_called = False

    def to_dict(data):
        nonlocal to_dict_called
        to_dict_called = True
        return data

    def from_dict(data):
        nonlocal from_dict_called
        from_dict_called = True
        return data

    output_serializer = CustomDictSerializer(
        to_dict=to_dict,
        from_dict=from_dict,
    )

    @idempotent_function(
        persistence_store=persistence_layer,
        data_keyword_argument="record",
        config=config,
        output_serializer=output_serializer,
    )
    def record_handler(record):
        return None

    record_handler(record=mock_event)
    assert to_dict_called is False, "in case response is None, to_dict should not be called"
    response = record_handler(record=mock_event)
    assert response is None
    assert from_dict_called is False, "in case response is None, from_dict should not be called"


@pytest.mark.parametrize("output_serializer_type", ["explicit", "deduced"])
def test_idempotent_function_serialization_dataclass(output_serializer_type: str):
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_dataclass.<locals>.collect_payment#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @dataclasses.dataclass
    class PaymentInput:
        customer_id: str
        transaction_id: str

    @dataclasses.dataclass
    class PaymentOutput:
        customer_id: str
        transaction_id: str

    if output_serializer_type == "explicit":
        output_serializer = DataclassSerializer(
            model=PaymentOutput,
        )
    else:
        output_serializer = DataclassSerializer

    @idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
        output_serializer=output_serializer,
    )
    def collect_payment(payment: PaymentInput) -> PaymentOutput:
        return PaymentOutput(**dataclasses.asdict(payment))

    # WHEN
    payment = PaymentInput(**mock_event)
    first_call: PaymentOutput = collect_payment(payment=payment)
    assert first_call.customer_id == payment.customer_id
    assert first_call.transaction_id == payment.transaction_id
    assert isinstance(first_call, PaymentOutput)
    second_call: PaymentOutput = collect_payment(payment=payment)
    assert isinstance(second_call, PaymentOutput)
    assert second_call.customer_id == payment.customer_id
    assert second_call.transaction_id == payment.transaction_id


def test_idempotent_function_serialization_dataclass_failure_no_return_type():
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_pydantic_failure_no_return_type.<locals>.collect_payment#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @dataclasses.dataclass
    class PaymentInput:
        customer_id: str
        transaction_id: str

    @dataclasses.dataclass
    class PaymentOutput:
        customer_id: str
        transaction_id: str

    idempotent_function_decorator = idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
        output_serializer=DataclassSerializer,
    )
    with pytest.raises(IdempotencyNoSerializationModelError, match="No serialization model was supplied"):

        @idempotent_function_decorator
        def collect_payment(payment: PaymentInput):
            return PaymentOutput(**payment.dict())


def test_idempotent_function_arbitrary_args_kwargs():
    # Scenario to validate we can use idempotent_function with a function
    # with an arbitrary number of args and kwargs
    mock_event = {"data": "value"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_arbitrary_args_kwargs.<locals>.record_handler#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}

    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
    def record_handler(arg_one, arg_two, record, is_record):
        return expected_result

    # WHEN calling the function
    result = record_handler("foo", "bar", record=mock_event, is_record=True)
    # THEN we expect the function to execute successfully
    assert result == expected_result


def test_idempotent_function_invalid_data_kwarg():
    mock_event = {"data": "value"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_invalid_data_kwarg.<locals>.record_handler#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}
    keyword_argument = "payload"

    # GIVEN data_keyword_argument does not match fn signature
    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument=keyword_argument)
    def record_handler(record):
        return expected_result

    # WHEN calling the function
    # THEN we expect to receive a Runtime error
    with pytest.raises(RuntimeError, match=f"Unable to extract '{keyword_argument}'"):
        record_handler(record=mock_event)


def test_idempotent_function_arg_instead_of_kwarg():
    mock_event = {"data": "value"}
    idempotency_key = "test-func.record_handler#" + hash_idempotency_key(mock_event)
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}
    keyword_argument = "record"

    # GIVEN data_keyword_argument matches fn signature
    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument=keyword_argument)
    def record_handler(record):
        return expected_result

    # WHEN calling the function without named argument
    # THEN we expect to receive a Runtime error
    with pytest.raises(RuntimeError, match=f"Unable to extract '{keyword_argument}'"):
        record_handler(mock_event)


def test_idempotent_function_and_lambda_handler(lambda_context):
    # Scenario to validate we can use both idempotent_function and idempotent decorators
    mock_event = {"data": "value"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_and_lambda_handler.<locals>.record_handler#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}

    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
    def record_handler(record):
        return expected_result

    persistence_layer = MockPersistenceLayer(
        f"{TESTS_MODULE_PREFIX}.test_idempotent_function_and_lambda_handler.<locals>.lambda_handler#{hash_idempotency_key(mock_event)}"  # noqa E501
    )

    @idempotent(persistence_store=persistence_layer)
    def lambda_handler(event, _):
        return expected_result

    # WHEN calling the function
    fn_result = record_handler(record=mock_event)

    # WHEN calling lambda handler
    handler_result = lambda_handler(mock_event, lambda_context)

    # THEN we expect the function and lambda handler to execute successfully
    assert fn_result == expected_result
    assert handler_result == expected_result


@pytest.mark.parametrize("data", [None, 0, False])
def test_idempotent_function_falsy_values(data):
    # Scenario to validate we can use idempotent_function with any function
    # receiving a falsy value (`None`, `False`, `0`, etc.)
    # shouldn't cause a RuntimeError
    mock_event = data
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_falsy_values.<locals>.record_handler#{hash_idempotency_key(mock_event)}"  # noqa: E501

    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}

    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
    def record_handler(record):
        return expected_result

    # WHEN calling the function
    result = record_handler(record=mock_event)
    # THEN we expect the function to execute successfully
    assert result == expected_result


@pytest.mark.parametrize("data", [None, 0, False])
def test_idempotent_function_falsy_values_with_raise_on_no_idempotency_key(
    data,
    persistence_store: DynamoDBPersistenceLayer,
):
    # GIVEN raise_on_no_idempotency_key is True
    idempotency_config = IdempotencyConfig(event_key_jmespath="idemKey", raise_on_no_idempotency_key=True)

    @idempotent_function(data_keyword_argument="record", persistence_store=persistence_store, config=idempotency_config)
    def record_handler(record):
        return ValueError("Should not be raised")

    # WHEN calling the function
    with pytest.raises(IdempotencyKeyError) as e:
        record_handler(record=data)

    # THEN we expect an idempotency key error message
    assert "No data found to create a hashed idempotency_key" == e.value.args[0]


def test_idempotent_data_sorting():
    # Scenario to validate same data in different order hashes to the same idempotency key
    data_one = {"data": "test message 1", "more_data": "more data 1"}
    data_two = {"more_data": "more data 1", "data": "test message 1"}
    idempotency_key = (
        f"{TESTS_MODULE_PREFIX}.test_idempotent_data_sorting.<locals>.dummy#{hash_idempotency_key(data_one)}"
    )
    # Assertion will happen in MockPersistenceLayer
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    # GIVEN
    @idempotent_function(data_keyword_argument="payload", persistence_store=persistence_layer)
    def dummy(payload):
        return {"message": "hello"}

    # WHEN/THEN assertion will happen at MockPersistenceLayer
    dummy(payload=data_two)


@pytest.mark.parametrize("idempotency_disabled_value", ["1", "y", "yes", "t", "true", "on"])
def test_idempotency_enabled_envvar_in_dev_environment(
    monkeypatch,
    lambda_context,
    persistence_store: DynamoDBPersistenceLayer,
    idempotency_disabled_value,
):
    # Scenario to validate no requests sent to dynamodb table when 'POWERTOOLS_IDEMPOTENCY_DISABLED' is set
    mock_event = {"data": "value"}

    persistence_store.client = MagicMock()

    monkeypatch.setenv("POWERTOOLS_IDEMPOTENCY_DISABLED", str(idempotency_disabled_value))
    monkeypatch.setenv("POWERTOOLS_DEV", "true")

    @idempotent_function(data_keyword_argument="data", persistence_store=persistence_store)
    def dummy(data):
        return {"message": "hello"}

    @idempotent(persistence_store=persistence_store)
    def dummy_handler(event, context):
        return {"message": "hi"}

    dummy(data=mock_event)
    dummy_handler(mock_event, lambda_context)

    assert len(persistence_store.client.method_calls) == 0


@pytest.mark.parametrize("idempotency_disabled_value", ["1", "y", "yes", "t", "true", "on"])
def test_idempotency_enabled_envvar_in_non_dev_environment(
    monkeypatch,
    lambda_context,
    persistence_store: DynamoDBPersistenceLayer,
    idempotency_disabled_value,
):
    # Scenario to validate no requests sent to dynamodb table when 'POWERTOOLS_IDEMPOTENCY_DISABLED' is set
    mock_event = {"data": "value"}

    persistence_store.client = MagicMock()

    monkeypatch.setenv("POWERTOOLS_IDEMPOTENCY_DISABLED", str(idempotency_disabled_value))

    @idempotent_function(data_keyword_argument="data", persistence_store=persistence_store)
    def dummy(data):
        return {"message": "hello"}

    @idempotent(persistence_store=persistence_store)
    def dummy_handler(event, context):
        return {"message": "hi"}

    with pytest.warns(PowertoolsUserWarning, match="Disabling idempotency is intended for development environments*"):
        dummy(data=mock_event)
        dummy_handler(mock_event, lambda_context)

        assert len(persistence_store.client.method_calls) == 0


@pytest.mark.parametrize("idempotency_disabled_value", ["0", "n", "no", "f", "false", "off"])
def test_idempotency_disabled_envvar(
    monkeypatch,
    lambda_context,
    persistence_store: DynamoDBPersistenceLayer,
    idempotency_disabled_value,
):
    # Scenario to validate no requests sent to dynamodb table when 'POWERTOOLS_IDEMPOTENCY_DISABLED' is false
    mock_event = {"data": "value"}

    persistence_store.client = MagicMock()

    monkeypatch.setenv("POWERTOOLS_IDEMPOTENCY_DISABLED", str(idempotency_disabled_value))

    @idempotent_function(data_keyword_argument="data", persistence_store=persistence_store)
    def dummy(data):
        return {"message": "hello"}

    @idempotent(persistence_store=persistence_store)
    def dummy_handler(event, context):
        return {"message": "hi"}

    dummy(data=mock_event)
    dummy_handler(mock_event, lambda_context)

    assert len(persistence_store.client.method_calls) == 4


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_idempotent_function_duplicates(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
):
    # Scenario to validate the both methods are called
    mock_event = {"data": "value"}
    persistence_store.client = MagicMock()

    @idempotent_function(data_keyword_argument="data", persistence_store=persistence_store, config=idempotency_config)
    def one(data):
        return "one"

    @idempotent_function(data_keyword_argument="data", persistence_store=persistence_store, config=idempotency_config)
    def two(data):
        return "two"

    assert one(data=mock_event) == "one"
    assert two(data=mock_event) == "two"
    assert len(persistence_store.client.method_calls) == 0


def test_invalid_dynamodb_persistence_layer():
    # Scenario constructing a DynamoDBPersistenceLayer with a key_attr matching sort_key_attr should fail
    with pytest.raises(ValueError) as ve:
        DynamoDBPersistenceLayer(
            table_name="Foo",
            key_attr="id",
            sort_key_attr="id",
            boto_config=Config(region_name="eu-west-1"),
        )
    # and raise a ValueError
    assert str(ve.value) == "key_attr [id] and sort_key_attr [id] cannot be the same!"


def test_idempotent_function_dataclasses():
    # Scenario _prepare_data should convert a python dataclasses to a dict

    @dataclasses.dataclass
    class Foo:
        name: str

    expected_result = {"name": "Bar"}
    data = Foo(name="Bar")
    as_dict = _prepare_data(data)
    assert as_dict == dataclasses.asdict(data)
    assert as_dict == expected_result


def test_idempotent_function_dataclass_with_jmespath():
    # GIVEN
    config = IdempotencyConfig(event_key_jmespath="transaction_id", use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_dataclass_with_jmespath.<locals>.collect_payment#{hash_idempotency_key(mock_event['transaction_id'])}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @dataclasses.dataclass
    class Payment:
        customer_id: str
        transaction_id: str

    @idempotent_function(data_keyword_argument="payment", persistence_store=persistence_layer, config=config)
    def collect_payment(payment: Payment):
        return payment.transaction_id

    # WHEN
    payment = Payment(**mock_event)
    result = collect_payment(payment=payment)

    # THEN idempotency key assertion happens at MockPersistenceLayer
    assert result == payment.transaction_id


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}], indirect=True)
def test_idempotent_lambda_compound_already_completed(
    idempotency_config: IdempotencyConfig,
    persistence_store_compound: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    hashed_idempotency_key,
    serialized_lambda_response,
    deserialized_lambda_response,
    lambda_context,
):
    """
    Test idempotent decorator having a DynamoDBPersistenceLayer with a compound key
    """

    stubber = stub.Stubber(persistence_store_compound.client)
    ddb_response = {
        "Item": {
            "id": {"S": "idempotency#"},
            "sk": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": serialized_lambda_response},
            "status": {"S": "COMPLETED"},
        },
    }
    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=ddb_response)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store_compound)
    def lambda_handler(event, context):
        raise ValueError

    lambda_resp = lambda_handler(lambda_apigw_event, lambda_context)
    assert lambda_resp == deserialized_lambda_response

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}], indirect=True)
def test_idempotent_lambda_compound_static_pk_value_has_correct_pk(
    idempotency_config: IdempotencyConfig,
    persistence_store_compound_static_pk_value: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    expected_params_put_item_compound_key_static_pk_value,
    expected_params_update_item_compound_key_static_pk_value,
    lambda_response,
    lambda_context,
):
    """
    Test idempotent decorator having a DynamoDBPersistenceLayer with a compound key and a static PK value
    """

    stubber = stub.Stubber(persistence_store_compound_static_pk_value.client)
    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item_compound_key_static_pk_value)
    stubber.add_response("update_item", ddb_response, expected_params_update_item_compound_key_static_pk_value)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store_compound_static_pk_value)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotency_payload_validation_with_tampering_nested_object(
    persistence_store: DynamoDBPersistenceLayer,
    timestamp_future,
    lambda_context,
    request: FixtureRequest,
):
    # GIVEN an idempotency config with a compound idempotency key (refund, customer_id)
    # AND with payload validation key to prevent tampering

    validation_key = "details"
    idempotency_config = IdempotencyConfig(
        event_key_jmespath='["refund_id", "customer_id"]',
        payload_validation_jmespath=validation_key,
        use_local_cache=False,
    )

    # AND a previous transaction already processed in the persistent store
    transaction = {
        "refund_id": "ffd11882-d476-4598-bbf1-643f2be5addf",
        "customer_id": "9e9fc440-9e65-49b5-9e71-1382ea1b1658",
        "details": [
            {
                "company_name": "Parker, Johnson and Rath",
                "currency": "Turkish Lira",
            },
        ],
    }

    stubber = stub.Stubber(persistence_store.client)
    ddb_response = build_idempotency_put_item_response_stub(
        data=transaction,
        expiration=timestamp_future,
        status="COMPLETED",
        request=request,
        validation_data=transaction[validation_key],
    )

    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=ddb_response)
    stubber.activate()

    # AND an upcoming tampered transaction
    tampered_transaction = copy.deepcopy(transaction)
    tampered_transaction["details"][0]["currency"] = "Euro"

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return event

    # WHEN the tampered request is made
    # THEN we should raise
    with pytest.raises(IdempotencyValidationError):
        lambda_handler(tampered_transaction, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotency_cache_with_payload_tampering(
    persistence_store: DynamoDBPersistenceLayer,
    timestamp_future,
    lambda_context,
    request: FixtureRequest,
    mocker: MockerFixture,
):
    # GIVEN an idempotency config with a compound idempotency key (refund, customer_id)
    # AND with payload validation key to prevent tampering

    cache_spy = mocker.spy(persistence_store, "_save_to_cache")

    validation_key = "amount"
    idempotency_config = IdempotencyConfig(
        event_key_jmespath='["refund_id", "customer_id"]',
        payload_validation_jmespath=validation_key,
        use_local_cache=True,
    )

    # AND a previous transaction already processed in the persistent store
    transaction = {
        "refund_id": "ffd11882-d476-4598-bbf1-643f2be5addf",
        "customer_id": "9e9fc440-9e65-49b5-9e71-1382ea1b1658",
        "amount": 100,
    }

    stubber = stub.Stubber(persistence_store.client)
    ddb_response = build_idempotency_put_item_response_stub(
        data=transaction,
        expiration=timestamp_future,
        status="COMPLETED",
        request=request,
        validation_data=transaction[validation_key],
    )

    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=ddb_response)
    stubber.activate()

    # AND an upcoming tampered transaction
    tampered_transaction = copy.deepcopy(transaction)
    tampered_transaction["amount"] = 10_000

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return event

    # WHEN the tampered request is made
    with pytest.raises(IdempotencyValidationError):
        lambda_handler(tampered_transaction, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()

    # THEN we should not cache a transaction that failed validation
    assert cache_spy.call_count == 0


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_responsehook_lambda_first_execution(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    expected_params_update_item,
    expected_params_put_item,
    lambda_response,
    lambda_context,
):
    """
    Test response_hook is not called for the idempotent decorator when lambda is executed
    with an event with a previously unknown event key
    """

    idempotent_response_hook = Mock()

    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    idempotency_config.response_hook = idempotent_response_hook

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()

    assert not idempotent_response_hook.called


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_already_completed_response_hook_is_called(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    hashed_idempotency_key,
    serialized_lambda_response,
    deserialized_lambda_response,
    lambda_context,
):
    """
    Test idempotent decorator where event with matching event key has already been successfully processed
    """

    def idempotent_response_hook(response: Any, idempotent_data: DataRecord) -> Any:
        """Modify the response provided by adding a new key"""
        response["idempotent_response"] = True
        response["idempotent_expiration"] = idempotent_data.get_expiration_datetime()

        return response

    idempotency_config.response_hook = idempotent_response_hook

    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": serialized_lambda_response},
            "status": {"S": "COMPLETED"},
        },
    }
    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=ddb_response)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception

    lambda_resp = lambda_handler(lambda_apigw_event, lambda_context)

    # Then idempotent_response value will be added to the response
    assert lambda_resp["idempotent_response"]
    assert lambda_resp["idempotent_expiration"] == datetime.datetime.fromtimestamp(int(timestamp_future))

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_already_completed_response_hook_is_called_with_none(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    hashed_idempotency_key,
    lambda_context,
):
    """
    Test idempotent decorator where event with matching event key has already been successfully processed
    """

    def idempotent_response_hook(response: Any, idempotent_data: DataRecord) -> Any:
        """Modify the response provided by adding a new key"""
        new_response: dict = {}
        new_response["idempotent_response"] = True
        new_response["response"] = response
        new_response["idempotent_expiration"] = idempotent_data.get_expiration_datetime()

        return new_response

    idempotency_config.response_hook = idempotent_response_hook

    stubber = stub.Stubber(persistence_store.client)
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": "null"},
            "status": {"S": "COMPLETED"},
        },
    }
    stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields=ddb_response)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception

    lambda_resp = lambda_handler(lambda_apigw_event, lambda_context)

    # Then idempotent_response value will be added to the response
    assert lambda_resp["idempotent_response"]
    assert lambda_resp["response"] is None
    assert lambda_resp["idempotent_expiration"] == datetime.datetime.fromtimestamp(int(timestamp_future))

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("output_serializer_type", ["explicit", "deduced"])
def test_idempotent_function_serialization_dataclass_with_optional_return(output_serializer_type: str):
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_dataclass_with_optional_return.<locals>.collect_payment#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @dataclasses.dataclass
    class PaymentInput:
        customer_id: str
        transaction_id: str

    @dataclasses.dataclass
    class PaymentOutput:
        customer_id: str
        transaction_id: str

    if output_serializer_type == "explicit":
        output_serializer = DataclassSerializer(
            model=PaymentOutput,
        )
    else:
        output_serializer = DataclassSerializer

    @idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
        output_serializer=output_serializer,
    )
    def collect_payment(payment: PaymentInput) -> Optional[PaymentOutput]:
        return PaymentOutput(**dataclasses.asdict(payment))

    # WHEN
    payment = PaymentInput(**mock_event)
    first_call: PaymentOutput = collect_payment(payment=payment)
    assert first_call.customer_id == payment.customer_id
    assert first_call.transaction_id == payment.transaction_id
    assert isinstance(first_call, PaymentOutput)
    second_call: PaymentOutput = collect_payment(payment=payment)
    assert isinstance(second_call, PaymentOutput)
    assert second_call.customer_id == payment.customer_id
    assert second_call.transaction_id == payment.transaction_id


def test_idempotent_function_with_custom_prefix_standalone_function():
    # Scenario to validate we can use idempotent_function with any function
    mock_event = {"data": "value"}
    idempotency_key = f"my-custom-prefix#{hash_idempotency_key(mock_event)}"
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}

    @idempotent_function(
        persistence_store=persistence_layer,
        data_keyword_argument="record",
        key_prefix="my-custom-prefix",
    )
    def record_handler(record):
        return expected_result

    # WHEN calling the function
    result = record_handler(record=mock_event)
    # THEN we expect the function to execute successfully
    assert result == expected_result


def test_idempotent_function_with_custom_prefix_lambda_handler(lambda_context):
    # Scenario to validate we can use idempotent_function with any function
    mock_event = {"data": "value"}
    idempotency_key = f"my-custom-prefix#{hash_idempotency_key(mock_event)}"
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}

    @idempotent(persistence_store=persistence_layer, key_prefix="my-custom-prefix")
    def lambda_handler(record, context):
        return expected_result

    # WHEN calling the function
    result = lambda_handler(mock_event, lambda_context)
    # THEN we expect the function to execute successfully
    assert result == expected_result
