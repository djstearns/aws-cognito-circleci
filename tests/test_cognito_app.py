import os
from typing import Any

import boto3
import dotenv
import pytest
from botocore.exceptions import ClientError
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient

dotenv.load_dotenv()

USER_POOL_ID = os.getenv("USER_POOL_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


@pytest.fixture
def cognito_idp_client() -> Any:
    client = boto3.client("cognito-idp", region_name="us-east-1")
    return client


def test_user_pool_and_app_client_exist(cognito_idp_client: CognitoIdentityProviderClient) -> None:
    assert USER_POOL_ID is not None, "USER_POOL_ID is not set in .env"
    assert CLIENT_ID is not None, "CLIENT_ID is not set in .env"
    assert GOOGLE_CLIENT_ID is not None, "GOOGLE_CLIENT_ID is not set in .env"

    # Check if User Pool exists
    try:
        pool_response = cognito_idp_client.describe_user_pool(UserPoolId=USER_POOL_ID)
        assert "UserPool" in pool_response
        assert pool_response["UserPool"]["Id"] == USER_POOL_ID
        print(f"✅ User Pool '{USER_POOL_ID}' exists.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.fail(f"❌ User Pool '{USER_POOL_ID}' does not exist.")
        else:
            pytest.fail(f"⚠️ Error while fetching User Pool: {str(e)}")

    # Check if App Client exists
    try:
        client_response = cognito_idp_client.describe_user_pool_client(UserPoolId=USER_POOL_ID, ClientId=CLIENT_ID)
        assert "UserPoolClient" in client_response
        assert client_response["UserPoolClient"]["ClientId"] == CLIENT_ID
        print("✅ App Client exists in User Pool.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.fail(f"❌ App Client '{CLIENT_ID}' does not exist in User Pool '{USER_POOL_ID}'.")
        else:
            pytest.fail(f"⚠️ Error while fetching App Client: {str(e)}")

    # Check if Google Identity Provider exists and has correct client ID
    try:
        idp_response = cognito_idp_client.describe_identity_provider(UserPoolId=USER_POOL_ID, ProviderName="Google")
        google_idp = idp_response["IdentityProvider"]
        assert google_idp["ProviderType"] == "Google", "ProviderType is not Google"
        configured_client_id = google_idp["ProviderDetails"].get("client_id")
        assert configured_client_id == GOOGLE_CLIENT_ID, (
            f"Google IdP client_id mismatch: expected '{GOOGLE_CLIENT_ID}', got '{configured_client_id}'"
        )
        print("✅ Google Identity Provider exists and has correct client ID.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.fail("❌ Google Identity Provider does not exist.")
        else:
            pytest.fail(f"⚠️ Error while fetching Identity Provider: {str(e)}")
