import json
import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, Status, StatusCode
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace import SpanKind
from logging.handlers import RotatingFileHandler # For rotating logs

# Flask App Initialization
app = Flask(__name__)
app.secret_key = 'secret'
COURSE_FILE = 'course_catalog.json'  # For fetching course names and details
LOG_FILE = 'app_log_rotating.json'  # For logging

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

# Logger setup
log_formatter = logging.Formatter('%(message)s')
rotating_file_handler = RotatingFileHandler(    # For saving logs to a rotating logs file
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5  # Max Size: 5MB, Backup Count: 5
)
rotating_file_handler.setFormatter(log_formatter)

# Stream handler (console)
stream_handler = logging.StreamHandler()  # For getting logs on terminal
stream_handler.setFormatter(log_formatter) 

# Get the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(rotating_file_handler)
logger.addHandler(stream_handler)

def log_request(level, event, message):     # Function to log requests based on level, event and message
    if (level=="info"):   
        logger.info(json.dumps({
            "level:": "INFO",
            "event": event,
            "http.method": request.method,
            "http.url": request.url,
            "user.ip": request.remote_addr,
            "message": message
            }, indent=4))
    elif (level=="error"):
        logger.error(json.dumps({
            "level:": "ERROR",
            "event": event,
            "http.method": request.method,
            "http.url": request.url,
            "user.ip": request.remote_addr,
            "message": message
            }, indent=4))
    elif (level=="warning"):
        logger.warning(json.dumps({
            "level:": "WARNING",
            "event": event,
            "http.method": request.method,
            "http.url": request.url,
            "user.ip": request.remote_addr,
            "message": message
            }, indent=4))

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
    error_fields = ['code', 'name', 'instructor']   # High Priority Fields without which course cannot be added
    warning_fields = [] 
    for filed in error_fields:
        if not data[filed].strip():
            flash(f"Error: '{filed}' field is required!", "error")
            return False
    for field in list(data.keys()):     # Low Priority Fields which are optional and can be added later.
        if (not data[field].strip()):
            warning_fields.append(field)
    if warning_fields:
        warning_fields_str = ', '.join(warning_fields)
        flash(f"Warning: '{warning_fields_str}' field is empty", "warning")
        return "warning"
    return True

def add_trace_context(span_name, load_courses_ = False, course_code = None, error_message = None, warning_message = None):    
    """
    Function to add tracers
    compulsory parameters:
        span_name: Name of the span

    Non-compulsory parameters:
        load_courses_: If the course count is to be logged  (For traces related to course catalog like rendering course catalog page)
        course_code: Course code to be logged (For traces related to a specific course like adding, deleting, viewing course details)
        error_message: Error message to be logged  (For traces where an error occurs)
        warning_message: Warning message to be logged (For traces where a warning occurs)
    """
    with tracer.start_as_current_span(span_name, kind=SpanKind.SERVER) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        span.set_attribute("user.ip", request.remote_addr)
        if load_courses_:
            courses = load_courses()
            span.set_attribute("courses.count", len(courses))
        if course_code:
            span.set_attribute("course.code", course_code)
        if error_message:
            span.set_attribute("error.message", error_message)
            span.set_status(Status(StatusCode.ERROR, error_message))   # Set status to error
        if warning_message:
            span.set_attribute("warning.message", warning_message)
            span.add_event("Potential issue detected", {
                "severity": "warning",
                "details": "This is a potential issue, but the operation succeeded."
            })

# Routes
@app.route('/')
def index():
    log_request("info", "render-index", "Home page rendered successfully")   # Calling the function to log requests
    add_trace_context("render-index")   # Calling the function to add tracers
    return render_template('index.html')

@app.route('/catalog', methods=['GET', 'POST'])
def course_catalog():
    courses = load_courses()
    add_trace_context("render-course-catalog", load_courses_=True)
    log_request("info", "render-course-catalog", "Course catalog page rendered successfully")
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
            }
            validation = validate_course(course)   # Get the validation of course data: True, False or "warning"
            if (validation == False):
                log_request("error", "course-add-error", "Required fields are empty")
                add_trace_context("add-course", course_code=course['code'], error_message="Required fields are empty")
                return redirect(url_for('course_catalog'))
            elif (validation == "warning"):
                log_request("warning", "course-add-warning", "Some fields are empty")
                add_trace_context("add-course", course_code=course['code'], warning_message="Some fields are empty")
                save_courses(course)
            else:
                add_trace_context("add-course", course_code=course['code'])
                save_courses(course)
            log_request("info", "course-added", f"Course '{course['code']}' '{course['name']}' added successfully")
            flash(f"Course '{course['name']}' added successfully!", "success")
            return redirect(url_for('course_catalog'))
        else:
            log_request("info", "render-add-course", "Add course page rendered successfully")
            add_trace_context("render-add-course")
            return render_template('add_course.html')
            
@app.route('/delete_course/<code>')   # Extra: Function to delete a course
def delete_course(code):
    # print(code)
    courses = load_courses()
    courses = [course for course in courses if course['code'] != code]
    with open(COURSE_FILE, 'w') as file:
        json.dump(courses, file, indent=4)
    log_request("info", "course-deleted", f"Course with code '{code}' deleted successfully")
    add_trace_context("delete-course", course_code=code)
    flash(f"Course with code '{code}' deleted successfully!", "success")
    return redirect(url_for('course_catalog'))

@app.route('/course/<code>')
def course_details(code):
    courses = load_courses()
    course = next((course for course in courses if course['code'] == code), None)
    if not course:
        flash(f"No course found with code '{code}'.", "error")
        log_request("error", "view-course-details-error", f"No course found with code '{code}'.")
        add_trace_context("view-course-details", course_code=code, error_message=f"No course found with code '{code}'.")
        return redirect(url_for('course_catalog'))
    log_request("info", "view-course-details", f"Course with code '{code}' viewed successfully")
    add_trace_context("view-course-details", course_code=code)
    return render_template('course_details.html', course=course)

@app.route('/contact')
def contact():
    log_request("info", "render-contact", "Contact page rendered successfully")
    add_trace_context("render-contact")
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
