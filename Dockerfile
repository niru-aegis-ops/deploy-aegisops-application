# Multi-stage build for a smaller final image

# --- Builder Stage ---
FROM python:3.9-slim-buster AS builder

# Create a virtual environment and install dependencies into it
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
# Ensure pip and python commands use the virtual environment
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# Copy requirements and install application dependencies into the venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Production Stage ---
FROM python:3.9-slim-buster

# Create a dedicated non-root user for enhanced security
RUN useradd --no-log-init --create-home appuser

# Set the working directory for the application
WORKDIR /home/appuser/app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
# Add the virtual environment's bin directory to the PATH for the non-root user
ENV PATH="/opt/venv/bin:$PATH"

# Copy the application code into the working directory
COPY . .

# Change ownership of the application directory to the non-root user
RUN chown -R appuser:appuser /home/appuser/app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Use Gunicorn as the production-ready WSGI server
# ENTRYPOINT sets the primary command, CMD provides default arguments
# This allows for easy overriding of Gunicorn arguments while keeping gunicorn as the entrypoint.
# Assuming your Flask/Django app instance is named 'app' in 'app.py'
ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:5000", "app:app"]