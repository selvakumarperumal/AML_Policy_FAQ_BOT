"""
AWS Lambda handler for the AML Policy FAQ Bot.

Loads config from AWS Secrets Manager and initializes FastAPI with Mangum.
"""

import os
import json
import boto3
from mangum import Mangum


def load_config_from_secrets():
    """Load config from AWS Secrets Manager and set as env vars."""
    secret_name = os.environ.get("CONFIG_SECRET_NAME")
    if not secret_name:
        return  # Not on AWS, use local .env
    
    try:
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)
        config = json.loads(response['SecretString'])
        
        for key, value in config.items():
            os.environ[key] = str(value)
    except Exception as e:
        print(f"Failed to load secrets: {e}")


# Load config before importing app
load_config_from_secrets()

from app.main import app

handler = Mangum(app, lifespan="off")
