#!/bin/bash
# =============================================================================
# Deploy latest code to AWS Lambda
# Use this for manual deployments. CI/CD handles this automatically on push.
# Prerequisites: Run deploy-setup.sh first (one-time).
# =============================================================================

set -euo pipefail

APP_NAME="rag-app"
AWS_REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"

echo "=== Deploying ${APP_NAME} ==="

# Login to ECR
aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Build and push
echo "[1/3] Building Docker image..."
docker build -t "${APP_NAME}" docker_image/
docker tag "${APP_NAME}:latest" "${ECR_REPO_URI}:latest"

echo "[2/3] Pushing to ECR..."
docker push "${ECR_REPO_URI}:latest"

# Update Lambda
echo "[3/3] Updating Lambda function..."
aws lambda update-function-code \
    --function-name "${APP_NAME}" \
    --image-uri "${ECR_REPO_URI}:latest" \
    --region "${AWS_REGION}"

aws lambda wait function-updated-v2 --function-name "${APP_NAME}" --region "${AWS_REGION}"

# Get API endpoint
API_ID=$(aws apigatewayv2 get-apis --region "${AWS_REGION}" \
    --query "Items[?Name=='${APP_NAME}-api'].ApiId" --output text)
API_ENDPOINT=$(aws apigatewayv2 get-api --api-id "${API_ID}" --region "${AWS_REGION}" \
    --query 'ApiEndpoint' --output text)

echo ""
echo "=== Deployed successfully ==="
echo "API: ${API_ENDPOINT}"
echo ""
