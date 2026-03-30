from flask import Flask
from flask_cors import CORS

from common.config import Config
from common.models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)

    # Register blueprints
    from admin.routes import admin_bp
    from student.routes import student_bp
    from student.assistant import assistant_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(assistant_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
