FROM public.ecr.aws/lambda/python:3.11

LABEL authors="Opeyemi"

COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Required to make SQLlite3 work for Chroma.
RUN pip install pysqlite3-binary

# Install the specified dependencies
RUN pip install -r requirements.txt --upgrade

# For local testing
EXPOSE 8000

# Setting IS_USING_IMAGE_RUNTIME Environment Variable To True For AWS Lambda
ENV IS_USING_IMAGE_RUNTIME=True

# Copy application code
COPY src/ ${LAMBDA_TASK_ROOT}/

# Lambda entry point to run the FastAPI server
CMD ["app_api_handler.handler"]

