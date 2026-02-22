import os
import logging
import sys
from flask import Flask, jsonify, request
from pythonjsonlogger import jsonlogger

# --- Configuration Management ---
# Use environment variables for sensitive or environment-specific settings.
# Default to development values if environment variables are not set.
# For production, these should be explicitly set in the environment
# (e.g., via Docker environment variables, Kubernetes secrets, or systemd).
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
DEBUG = FLASK_ENV == 'development'
HOST = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
PORT = int(os.environ.get('FLASK_RUN_PORT', 5000))

app = Flask(__name__)
app.config['DEBUG'] = DEBUG
app.config['FLASK_ENV'] = FLASK_ENV

# --- Structured Logging ---
# Configure a structured JSON logger for better observability in production.
# This allows logs to be easily parsed and analyzed by log management systems.
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = record.asctime
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname.upper()
        
        # Add request-specific details if an active request context exists
        if request:
            log_record['method'] = request.method
            log_record['path'] = request.path
            log_record['ip_address'] = request.remote_addr
            log_record['user_agent'] = request.headers.get('User-Agent')


# Set up root logger for all messages
handler = logging.StreamHandler(sys.stdout)
formatter = CustomJsonFormatter(
    # Specify the format string for the JSON logger.
    # These fields will be at the top level of the JSON object.
    '%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d'
)
handler.setFormatter(formatter)

# Clear existing handlers to prevent duplicate logs from Flask's default setup
# and ensure our custom formatter is the only one used.
if app.logger.handlers:
    for h in app.logger.handlers:
        app.logger.removeHandler(h)
if logging.getLogger().handlers:
    for h in logging.getLogger().handlers:
        logging.getLogger().removeHandler(h)

app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO if not DEBUG else logging.DEBUG) # Catch all logs

# Suppress default Werkzeug (Flask's underlying WSGI server) log messages
# to avoid duplicates, as we're handling with our root logger.
logging.getLogger('werkzeug').setLevel(logging.WARNING)

@app.route('/')
def home():
    app.logger.info("Home page accessed.")
    return "AegisOps Application is running!"

@app.route('/health')
def health_check():
    # Example of structured logging with extra key-value pairs
    app.logger.info("Health check performed.", extra={'service_status': 'ok', 'component': 'web'})
    return jsonify(status="healthy"), 200

# --- Error Handling ---
# Implement custom error handlers to provide more informative and user-friendly
# responses, and to prevent exposing sensitive debug information in production.
@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f"404 Not Found: {request.path}", extra={'error_message': str(error)})
    return jsonify(error="Not Found", message="The requested URL was not found on the server."), 404

@app.errorhandler(500)
def internal_error(error):
    # Log the full traceback for 500 errors.
    # Differentiate response based on debug mode to avoid exposing internal errors.
    if app.config['DEBUG']:
        app.logger.exception("500 Internal Server Error during development.", extra={'error_message': str(error)})
        return jsonify(error="Internal Server Error", message=str(error)), 500
    else:
        app.logger.exception("500 Internal Server Error in production.")
        return jsonify(error="Internal Server Error", message="An unexpected error occurred. Please try again later."), 500

# --- Production WSGI Server & Local Development ---
if __name__ == '__main__':
    # This block is for local development only.
    # It uses Flask's built-in development server, which is NOT suitable for production.
    #
    # For production deployments, a robust WSGI server like Gunicorn or uWSGI must be used.
    # Example Gunicorn command for production:
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
    # Where:
    #   -w 4: Specifies 4 worker processes (adjust based on CPU cores).
    #   -b 0.0.0.0:5000: Binds the server to all network interfaces on port 5000.
    #   app:app: Refers to the 'app' variable (our Flask application instance)
    #             within the 'app.py' module.
    app.logger.info(f"Starting AegisOps Application in {FLASK_ENV} mode on http://{HOST}:{PORT}...")
    app.run(host=HOST, port=PORT)