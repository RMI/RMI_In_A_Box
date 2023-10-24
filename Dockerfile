# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install azure-storage-blob

# Copy the current directory content into the container
COPY . .

# Set the environment variables with default/empty values
ENV AZURE_STORAGE_CONNECTION_STRING=""
ENV OPENAI_API_KEY=""

# Make port 5000 available
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=qa_api.py

# Run the application when the container launches
CMD ["./start.sh"]