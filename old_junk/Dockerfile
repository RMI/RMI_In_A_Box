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

# Make port 8000 available
EXPOSE 8000

# Define environment variable
# Not necessary unless you are using Flask environment variables

# Run the application when the container launches
CMD ["uvicorn", "qa_fastapi:app", "--host", "0.0.0.0", "--port", "8000"]