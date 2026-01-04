import os

import boto3
import dotenv
from botocore.exceptions import ClientError
from loguru import logger

# Load environment variables
dotenv.load_dotenv()

# Get environment variables
USER_POOL_ID = os.getenv("USER_POOL_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")

# Ensure required parameters are provided
if not USER_POOL_ID or not CLIENT_ID:
    raise ValueError("Missing required environment variables: USER_POOL_ID, CLIENT_ID")

# Create Cognito client
client = boto3.client(service_name="cognito-idp", region_name=AWS_REGION)


try:
    logger.info("Updating User Pool Client configuration...")
    response = client.update_user_pool_client(
        UserPoolId=USER_POOL_ID,
        ClientId=CLIENT_ID,
        SupportedIdentityProviders=["COGNITO", "Google"],
        CallbackURLs=["http://localhost:8507"],
        LogoutURLs=["http://localhost:8507/logout"],
        AllowedOAuthFlows=["code"],
        AllowedOAuthScopes=["email", "openid", "profile"],
        AllowedOAuthFlowsUserPoolClient=True,
    )

    # Verify the update was successful
    if "UserPoolClient" in response:
        logger.success("Successfully updated User Pool Client configuration")
        logger.info(f"Client ID: {response['UserPoolClient']['ClientId']}")
        logger.info(f"Supported Identity Providers: {response['UserPoolClient']['SupportedIdentityProviders']}")
    else:
        logger.warning("Update successful but response format unexpected")

except ClientError as e:
    error_code = e.response["Error"]["Code"]
    error_message = e.response["Error"]["Message"]
    logger.error(f"Failed to update User Pool Client. Error {error_code}: {error_message}")
    raise

except Exception as e:
    logger.error(f"Unexpected error occurred: {str(e)}")
    raise
