import json
import os

import boto3
import dotenv
from loguru import logger

# Load environment variables from .env file
dotenv.load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
POOL_NAME = os.getenv("POOL_NAME", "StreamlitAppUserPool")
CLIENT_NAME = os.getenv("CLIENT_NAME", "StreamlitAppClient")

# Set up loguru
logger.info("Starting Cognito setup script...")

# Create Cognito client
client = boto3.client(service_name="cognito-idp", region_name=AWS_REGION)

# Step 1: Check if User Pool exists and create if it doesn't
logger.info(f"Checking if user pool '{POOL_NAME}' already exists...")
existing_pool_id = None

paginator = client.get_paginator("list_user_pools")
for page in paginator.paginate(MaxResults=60, PaginationConfig={"MaxItems": 10}):  # type: ignore
    for pool in page["UserPools"]:
        if pool["Name"] == POOL_NAME:
            existing_pool_id = pool["Id"]
            logger.info(f"User pool '{POOL_NAME}' already exists with ID: {existing_pool_id}")
            break
    if existing_pool_id:
        break

if existing_pool_id:
    user_pool_id = existing_pool_id
else:
    logger.info(f"Creating new user pool '{POOL_NAME}'...")
    response_pool = client.create_user_pool(
        PoolName=POOL_NAME,
        Policies={
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": True,
                "RequireLowercase": True,
                "RequireNumbers": True,
                "RequireSymbols": False,
            }
        },
        AutoVerifiedAttributes=["email"],
        UsernameAttributes=["email"],
        MfaConfiguration="OFF",
    )
    user_pool_id = response_pool["UserPool"]["Id"]
    logger.success(f"User Pool created with ID: {user_pool_id}")

# Step 2: Check if App Client exists and create if it doesn't
logger.info(f"Checking if app client '{CLIENT_NAME}' already exists...")
existing_client_id = None

response_clients = client.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=60)

for client_info in response_clients["UserPoolClients"]:
    if client_info["ClientName"] == CLIENT_NAME:
        existing_client_id = client_info["ClientId"]
        logger.info(f"App Client '{CLIENT_NAME}' already exists with ID: {existing_client_id}")
        break

if existing_client_id:
    app_client_id = existing_client_id
else:
    logger.info("Creating new App Client...")
    response_client = client.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=CLIENT_NAME,
        GenerateSecret=False,
        ExplicitAuthFlows=[
            "ALLOW_USER_PASSWORD_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH",
            "ALLOW_USER_SRP_AUTH",
            "ALLOW_CUSTOM_AUTH",
        ],
        AllowedOAuthFlows=["code"],
        AllowedOAuthScopes=["email", "openid", "profile"],
        AllowedOAuthFlowsUserPoolClient=True,
        CallbackURLs=["http://localhost:8507"],
        LogoutURLs=["http://localhost:8507/logout"],
    )
    app_client_id = response_client["UserPoolClient"]["ClientId"]
    logger.success(f"App Client created with ID: {app_client_id}")

output = {
    "UserPoolId": user_pool_id,
    "AppClientId": app_client_id,
}

logger.info(f"Output: {json.dumps(output, indent=4)}")
