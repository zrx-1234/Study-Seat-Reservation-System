from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# TODO: Routes for admin
# - /auth/login - Admin login
# - /rooms - Study room management (CRUD)
# - /seats - Seat management (CRUD)
# - /reservations - Reservation management
# - /violations - Violation record management
# - /roles - Role management (RBAC)
# - /permissions - Permission management
# - /users - User management
# - /stats - Statistics and analytics
# - /settings - System parameters
