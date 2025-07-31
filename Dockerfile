# Use a lightweight base image of Python 3.12 slim version for the container
# This ensures the container is small and efficient, reducing build time and resource usage
FROM python:3.12-slim

# copy temporary files to the container
# This is necessary to ensure that the application code is available in the container
COPY ./app /temp_app
# Set the working directory inside the container
# All subsequent commands will be executed relative to this directory

WORKDIR /aml_policy_faq_bot

# Install required system packages:
# - gcc: compiler for Python packages
# - libpq-dev: PostgreSQL support
# - build-essential: make, etc.
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#     gcc \
#     libpq-dev \
#     build-essential && \
#     rm -rf /var/lib/apt/lists/*


# Copy the requirements file into the container
# This file contains a list of Python dependencies required by the application
COPY requirements.txt .

# Install Python dependencies
# Upgrade pip to the latest version and install packages listed in requirements.txt
# The --no-cache-dir flag prevents caching to reduce image size
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Development does not require copying the source code into the container
# Conditional logic is used to handle source code copying based on the build environment

# Define a build argument to specify the environment (default is 'prod')
# This allows flexibility in building the container for different environments
ARG ENV=prod

# Conditional logic to copy source code only for production builds
# If the environment is not 'dev', the source code is copied into the container
RUN if [ "${ENV}" != "dev" ]; then \
    echo "Copying source code for production"; \
    cp -r /temp_app /aml_policy_faq_bot/app; \
    rm -rf /temp_app; \
    echo "Source code copied successfully"; \
    else \
    rm -rf /temp_app; \ 
    echo "Skipping source code copy for development"; \
    fi

# Set an environment variable inside the container
# This variable can be used by the application to determine the runtime environment
ENV APP_ENV=${ENV}

# Copy the start script into the container
# This script is responsible for starting the application
COPY start.sh /start.sh
COPY start_worker.sh /start_worker.sh

# Grant execute permissions to the start script
# This ensures the script can be executed when the container starts
RUN chmod +x /start.sh
RUN chmod +x /start_worker.sh

# Define the default command to run when the container starts
# The start script will launch the FastAPI application using Uvicorn
# CMD [ "/start.sh" ]
