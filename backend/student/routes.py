from flask import Blueprint

student_bp = Blueprint('student', __name__, url_prefix='/api/student')

# TODO: Routes for student
# - /auth/login - Student login (student ID + password)
# - /rooms - List available study rooms
# - /seats - Seat search and filtering
# - /reservations - Reservation (create, cancel, view history)
# - /checkin - Check-in with dynamic code/QR
# - /notifications - Notification preferences
# - /assistant - Smart assistant (natural language)
