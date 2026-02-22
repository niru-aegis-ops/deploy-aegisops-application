# Multi-stage Dockerfile for Aegisops application

# --- Builder Stage ---
# Pin to a specific patch version for enhanced reproducibility
FROM python:3.9.18-slim-buster as builder

WORKDIR /app

# Install dependencies into a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv
# Activate the virtual environment for subsequent commands in this stage
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# --- Runner Stage ---
# Use the same slim-buster base image. The key benefit of multi-stage here is
# pre-installing dependencies into a venv and copying only that, avoiding reinstall.
FROM python:3.9.18-slim-buster

# Set working directory
WORKDIR /app

# Copy the installed virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Activate the virtual environment for the runner stage
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code. Ensure a .dockerignore file is present to exclude unnecessary files.
COPY . .

# Create a dedicated non-root user for improved security
RUN adduser --system --no-create-home appuser
# Grant ownership of the application directory to the non-root user
RUN chown -R appuser:appuser /app
# Switch to the non-root user
USER appuser

# Expose the application port
EXPOSE 5000

# Set environment variable for the port
ENV PORT=5000

# Command to run the application using Gunicorn for production robustness.
# This assumes 'app.py' contains a WSGI callable named 'app'.
# Adjust 'app:app' if your application entry point is different (e.g., 'your_module:create_app()').
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]