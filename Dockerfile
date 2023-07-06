# Use python 3.9 slim edition as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy source code into the container
COPY . /app

# Setup the environment variable for the connection string
ARG CONNECTION_STRING
ENV CONNECTION_STRING=$CONNECTION_STRING

# Install requirements
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8080

# Entrypoint command for api.py server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]