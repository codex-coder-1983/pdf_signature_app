# Use an official lightweight Python image
FROM python:3.11-slim

# Set work directory inside container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose the port Flask/Gunicorn will run on
EXPOSE 5000

# Use Gunicorn as the production server
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
