import json
import os
import logging
import time
from flask import Flask, render_template, request, redirect, url_for, flash
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace import SpanKind

# Flask App Initialization
app = Flask(__name__)
app.secret_key = 'secret'
COURSE_FILE = 'course_catalog.json'
LOG_FILE = 'app_logs.json'

# OpenTelemetry Setup
resource = Resource.create({"service.name": "course-catalog-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
FlaskInstrumentor().instrument_app(app)

# Custom JSON File Handler
class JSONFileHandler(logging.FileHandler):
    def emit(self, record):
        log_entry = self.format(record)
        with open(self.baseFilename, 'a') as log_file:
            log_file.write(log_entry + '\n')

# Logger setup
log_formatter = logging.Formatter('%(message)s')

# JSON file handler
json_file_handler = JSONFileHandler(LOG_FILE)
json_file_handler.setFormatter(log_formatter)

# Stream handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)

# Get the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(json_file_handler)
logger.addHandler(stream_handler)

# Utility Functions
def load_courses():
    """Load courses from the JSON file."""
    if not os.path.exists(COURSE_FILE):
        return []  # Return an empty list if the file doesn't exist
    with open(COURSE_FILE, 'r') as file:
        return json.load(file)


def save_courses(data):
    """Save new course data to the JSON file."""
    courses = load_courses()  # Load existing courses
    courses.append(data)  # Append the new course
    with open(COURSE_FILE, 'w') as file:
        json.dump(courses, file, indent=4)

def validate_course(data):
    """Validate course data to check if the required fields are empty"""
    error_fields = ['code', 'name', 'instructor']
    warning_fields = ['semester', 'schedule', 'classroom', 'prerequisites', 'grading', 'description']
    for filed in error_fields:
        if not data[filed].strip():
            flash(f"Error: '{filed}' field is required!", "error")
            return False
    for filed in warning_fields:
        if data[filed].strip():
            warning_fields.remove(filed)
    if warning_fields:
        warning_fields_str = ', '.join(warning_fields)
        flash(f"Warning: '{warning_fields_str}' field is empty", "warning")
        return "warning"
    return True

# Routes
@app.route('/')
def index():
    logger.info(json.dumps({
        "level:": "INFO",
        "event": "render-index",
        "http.method": request.method,
        "http.url": request.url,
        "user.ip": request.remote_addr
        }, indent=4))
    return render_template('index.html')

@app.route('/catalog')
def course_catalog():
    logger.info(json.dumps({
        "level:": "INFO",
        "event": "render-course-catalog",
        "http.method": request.method,
        "http.url": request.url,
        "user.ip": request.remote_addr
        }, indent=4))
    courses = load_courses()
    return render_template('course_catalog.html', courses=courses)


@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        course = {
            'code': request.form['code'],
            'name': request.form['name'],
            'instructor': request.form['instructor'],
            'semester': request.form['semester'],
            'schedule': request.form['schedule'],
            'classroom': request.form['classroom'],
            'prerequisites': request.form['prerequisites'],
            'grading': request.form['grading'],
            'description': request.form['description']
        }
        validation = validate_course(course)
        if (validation == False):
            logger.error(json.dumps({
                "level:": "ERROR",
                "event": "course-add-error",
                "error.message": "Required fields are empty",
                "http.method": request.method,
                "http.url": request.url,
                "user.ip": request.remote_addr
                }, indent=4))
            return render_template('add_course.html', course=course)
        elif (validation == "warning"):
            logger.warning(json.dumps({
                "level:": "WARNING",
                "event": "course-add-warning",
                "warning.message": "Some fields are empty",
                "http.method": request.method,
                "http.url": request.url,
                "user.ip": request.remote_addr
                }, indent=4))
        save_courses(course)
        flash(f"Course '{course['name']}' added successfully!", "success")
        return redirect(url_for('course_catalog'))
    return render_template('add_course.html')


@app.route('/course/<code>')
def course_details(code):
    courses = load_courses()
    course = next((course for course in courses if course['code'] == code), None)
    if not course:
        flash(f"No course found with code '{code}'.", "error")
        logger.error(json.dumps({
            "level:": "ERROR",
            "event": "view-course-details-error",
            "error.message": f"No course found with code '{code}'.",
            "http.method": request.method,
            "http.url": request.url,
            "user.ip": request.remote_addr
            }, indent=4))
        return redirect(url_for('course_catalog'))
    logger.info(json.dumps({
        "level:": "INFO",
        "event": "view-course-details",
        "http.method": request.method,
        "http.url": request.url,
        "user.ip": request.remote_addr,
        "course.code": course['code'],
        "course.name": course['name']
        }, indent=4))
    return render_template('course_details.html', course=course)

@app.route('/contact')
def contact():
    logger.info(json.dumps({
        "level:": "INFO",
        "event": "render-contact",
        "http.method": request.method,
        "http.url": request.url,
        "user.ip": request.remote_addr
        }, indent=4))
    return render_template('contact.html')

@app.route("/manual-trace")
def manual_trace():
    # Start a span manually for custom tracing
    with tracer.start_as_current_span("manual-span", kind=SpanKind.SERVER) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        span.add_event("Processing request")
        return "Manual trace recorded!", 200


@app.route("/auto-instrumented")
def auto_instrumented():
    # Automatically instrumented via FlaskInstrumentor
    return "This route is auto-instrumented!", 200


if __name__ == '__main__':
    app.run(debug=True)
