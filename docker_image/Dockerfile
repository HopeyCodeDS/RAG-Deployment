FROM public.ecr.aws/lambda/python:3.11

LABEL authors="Opeyemi"

COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install pysqlite3 (required for SQLite3/ChromaDB in Lambda) and project dependencies
RUN pip install pysqlite3-binary && \
    pip install -r requirements.txt --upgrade

# For local testing
EXPOSE 8000

# Setting IS_USING_IMAGE_RUNTIME Environment Variable To True For AWS Lambda
ENV IS_USING_IMAGE_RUNTIME=True

# Copy application code
COPY src/ ${LAMBDA_TASK_ROOT}/

# Generate ChromaDB embeddings at build time (requires AWS credentials as build args)
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION=us-east-1
COPY populate_database.py ${LAMBDA_TASK_ROOT}/
RUN if [ -n "$AWS_ACCESS_KEY_ID" ]; then \
      AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
      AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
      AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} \
      python populate_database.py --reset; \
    else \
      echo "Skipping DB population (no AWS credentials)"; \
    fi && \
    rm populate_database.py

# Lambda entry point to run the FastAPI server
CMD ["app_api_handler.handler"]
