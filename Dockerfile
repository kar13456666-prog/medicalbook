# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend code (app.py, database.py, routes, etc.)
COPY . .

# Expose the port your backend runs on (matches your docker-compose.yml)
EXPOSE 8000

# Command to run your Python app
CMD ["python", "app.py"]
