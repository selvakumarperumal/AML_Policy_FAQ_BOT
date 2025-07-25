# Base image for the Dockerfile
# Using a slim version of Python 3.14 for a lightweight container
FROM python:3.14-slim

# Set the working directory in the container
WORKDIR aml_policy_faq_bot

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]