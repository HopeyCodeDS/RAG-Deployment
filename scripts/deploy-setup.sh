#!/bin/bash
# =============================================================================
# One-time AWS infrastructure setup for Serverless RAG API
# Run this once to create ECR repo, Lambda function, and API Gateway.
# Prerequisites: AWS CLI configured with appropriate permissions.
# =============================================================================

set -euo pipefail

# ---- Configuration (edit these) ----
APP_NAME="rag-app"
AWS_REGION="us-east-1"
LAMBDA_MEMORY=1024          # MB
LAMBDA_TIMEOUT=60           # seconds
# ------------------------------------

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_REPO_URI="${ECR_URI}/${APP_NAME}"

echo "=== Serverless RAG API: AWS Infrastructure Setup ==="
echo "Account:  ${ACCOUNT_ID}"
echo "Region:   ${AWS_REGION}"
echo "ECR Repo: ${ECR_REPO_URI}"
echo ""

# --- Step 1: Create ECR Repository ---
echo "[1/5] Creating ECR repository..."
if aws ecr describe-repositories --repository-names "${APP_NAME}" --region "${AWS_REGION}" > /dev/null 2>&1; then
    echo "  ECR repository '${APP_NAME}' already exists. Skipping."
else
    aws ecr create-repository \
        --repository-name "${APP_NAME}" \
        --region "${AWS_REGION}" \
        --image-scanning-configuration scanOnPush=true
    echo "  Created ECR repository '${APP_NAME}'."
fi

# --- Step 2: Create IAM Role for Lambda ---
echo "[2/5] Creating Lambda execution role..."
ROLE_NAME="${APP_NAME}-lambda-role"
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}'

if aws iam get-role --role-name "${ROLE_NAME}" > /dev/null 2>&1; then
    echo "  IAM role '${ROLE_NAME}' already exists. Skipping."
else
    aws iam create-role \
        --role-name "${ROLE_NAME}" \
        --assume-role-policy-document "${TRUST_POLICY}"

    # Attach basic Lambda + Bedrock permissions
    aws iam attach-role-policy \
        --role-name "${ROLE_NAME}" \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    aws iam attach-role-policy \
        --role-name "${ROLE_NAME}" \
        --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

    echo "  Created IAM role '${ROLE_NAME}' with Lambda + Bedrock permissions."
    echo "  Waiting 10s for IAM role propagation..."
    sleep 10
fi

ROLE_ARN=$(aws iam get-role --role-name "${ROLE_NAME}" --query 'Role.Arn' --output text)

# --- Step 3: Build and Push Docker Image ---
echo "[3/5] Building and pushing Docker image..."
aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ECR_URI}"
docker build -t "${APP_NAME}" docker_image/
docker tag "${APP_NAME}:latest" "${ECR_REPO_URI}:latest"
docker push "${ECR_REPO_URI}:latest"
echo "  Pushed image to ${ECR_REPO_URI}:latest"

# --- Step 4: Create Lambda Function ---
echo "[4/5] Creating Lambda function..."
if aws lambda get-function --function-name "${APP_NAME}" --region "${AWS_REGION}" > /dev/null 2>&1; then
    echo "  Lambda function '${APP_NAME}' already exists. Updating image..."
    aws lambda update-function-code \
        --function-name "${APP_NAME}" \
        --image-uri "${ECR_REPO_URI}:latest" \
        --region "${AWS_REGION}"
else
    aws lambda create-function \
        --function-name "${APP_NAME}" \
        --package-type Image \
        --code "ImageUri=${ECR_REPO_URI}:latest" \
        --role "${ROLE_ARN}" \
        --timeout "${LAMBDA_TIMEOUT}" \
        --memory-size "${LAMBDA_MEMORY}" \
        --region "${AWS_REGION}" \
        --environment "Variables={IS_USING_IMAGE_RUNTIME=True}"
    echo "  Created Lambda function '${APP_NAME}'."
fi

# Wait for function to be active
echo "  Waiting for Lambda function to become active..."
aws lambda wait function-active-v2 --function-name "${APP_NAME}" --region "${AWS_REGION}"
echo "  Lambda function is active."

# --- Step 5: Create API Gateway ---
echo "[5/5] Creating HTTP API Gateway..."
EXISTING_API_ID=$(aws apigatewayv2 get-apis --region "${AWS_REGION}" \
    --query "Items[?Name=='${APP_NAME}-api'].ApiId" --output text 2>/dev/null || echo "")

if [ -n "${EXISTING_API_ID}" ] && [ "${EXISTING_API_ID}" != "None" ]; then
    echo "  API Gateway '${APP_NAME}-api' already exists (ID: ${EXISTING_API_ID}). Skipping."
    API_ID="${EXISTING_API_ID}"
else
    LAMBDA_ARN=$(aws lambda get-function --function-name "${APP_NAME}" --region "${AWS_REGION}" \
        --query 'Configuration.FunctionArn' --output text)

    # Create HTTP API with Lambda integration
    API_ID=$(aws apigatewayv2 create-api \
        --name "${APP_NAME}-api" \
        --protocol-type HTTP \
        --target "${LAMBDA_ARN}" \
        --region "${AWS_REGION}" \
        --query 'ApiId' --output text)

    # Grant API Gateway permission to invoke Lambda
    aws lambda add-permission \
        --function-name "${APP_NAME}" \
        --statement-id "apigateway-invoke" \
        --action "lambda:InvokeFunction" \
        --principal "apigateway.amazonaws.com" \
        --source-arn "arn:aws:execute-api:${AWS_REGION}:${ACCOUNT_ID}:${API_ID}/*" \
        --region "${AWS_REGION}"

    echo "  Created API Gateway (ID: ${API_ID})."
fi

API_ENDPOINT=$(aws apigatewayv2 get-api --api-id "${API_ID}" --region "${AWS_REGION}" \
    --query 'ApiEndpoint' --output text)

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Your RAG API is live at:"
echo "  ${API_ENDPOINT}"
echo ""
echo "Test it:"
echo "  curl ${API_ENDPOINT}/"
echo "  curl -X POST ${API_ENDPOINT}/submit_query -H 'Content-Type: application/json' -d '{\"query_text\": \"What services do you offer?\"}'"
echo ""
echo "GitHub Secrets to set (for CI/CD auto-deploy):"
echo "  AWS_ACCESS_KEY_ID       = <your key>"
echo "  AWS_SECRET_ACCESS_KEY   = <your secret>"
echo "  ECR_REPOSITORY_URI      = ${ECR_REPO_URI}"
echo "  LAMBDA_FUNCTION_NAME    = ${APP_NAME}"
echo ""
