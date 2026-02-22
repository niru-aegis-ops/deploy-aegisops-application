import os
import logging
from flask import Flask, jsonify

# --- Configuration Management & Enhanced Logging ---
# Configure logging for production. Logs to stdout/stderr which is standard for containerized apps.
# Log level can be set via environment variable (e.g., LOG_LEVEL=DEBUG).
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
    format='[%(asctime)s] [%(levelname)s] in %(module)s: %(message)s'
)

app = Flask(__name__)
# Integrate Flask's default logger with our configured logging
app.logger.handlers = logging.getLogger().handlers
app.logger.setLevel(logging.getLogger().level)

# --- Error Handling ---
@app.errorhandler(404)
def not_found_error(error):
    """
    Custom handler for 404 Not Found errors.
    Provides a JSON response and logs the event.
    """
    app.logger.warning(f"404 Not Found: {error.description if hasattr(error, 'description') else 'No description'}")
    return jsonify({
        "error": "Not Found",
        "message": "The requested URL was not found on the server. Please check the endpoint."
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Custom handler for 500 Internal Server Errors.
    Provides a JSON response and logs the error details.
    """
    app.logger.exception("500 Internal Server Error: An unexpected error occurred.")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred on the server. Please try again later."
    }), 500

# --- Application Routes ---
@app.route('/')
def hello_world():
    """
    Root endpoint for the Aegisops application.
    """
    app.logger.info("Serving root endpoint '/'")
    return "Hello from Aegisops Application!"

@app.route('/health')
def health_check():
    """
    Liveness probe: Checks if the application is running.
    Returns a simple healthy status.
    """
    app.logger.debug("Serving liveness check endpoint '/health'")
    return jsonify({"status": "healthy", "application": "Aegisops"}), 200

@app.route('/ready')
def readiness_check():
    """
    Readiness probe: Checks if the application is ready to serve traffic.
    In a real-world scenario, this would include checks for database connections,
    external services, or any other dependencies required for full functionality.
    For this example, it simply confirms the application process is responsive.
    """
    # Example: if you had a database, you might try to connect here
    # try:
    #     db_connection.ping()
    #     db_status = "ok"
    # except Exception as e:
    #     app.logger.error(f"Database readiness check failed: {e}")
    #     db_status = "failed"
    #     return jsonify({"status": "not ready", "application": "Aegisops", "details": {"database": db_status}}), 503

    app.logger.debug("Serving readiness check endpoint '/ready'")
    return jsonify({"status": "ready", "application": "Aegisops", "message": "Application is ready to serve traffic."}), 200

# --- Production WSGI Server Integration & Local Development ---
if __name__ == '__main__':
    # This block is for local development purposes only.
    # In a production environment, a robust WSGI server like Gunicorn
    # will be used to run the application (e.g., `gunicorn -w 4 -b 0.0.0.0:5000 app:app`).
    # The 'PORT' environment variable is used for dynamic port assignment, common in cloud deployments.
    port = int(os.environ.get('PORT', 5000))
    # Enable debug mode for local development for automatic reloader and detailed error messages.
    # This should ALWAYS be False in production for security and performance.
    app.logger.info(f"Starting Flask development server on http://0.0.0.0:{port} (DEBUG mode is ON)")
    app.run(debug=True, host='0.0.0.0', port=port)