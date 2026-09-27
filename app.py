from flask import Flask, redirect, url_for, session, render_template
from config import Config
from blueprints.auth import auth_bp
from blueprints.admin import admin_bp
from blueprints.student import student_bp
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)

    @app.route('/')
    def index():
        """Root dispatcher based on authentication state."""
        if 'user_id' in session:
            if session.get('role') == 'ADMIN':
                return redirect(url_for('admin.dashboard'))
            elif session.get('role') == 'STUDENT':
                return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.login'))

    @app.context_processor
    def inject_global_data():
        """Inject current year and session user details globally to all templates."""
        return {
            'current_year': datetime.now().year,
            'logged_in': 'user_id' in session,
            'user_role': session.get('role'),
            'user_name': session.get('full_name') or session.get('username')
        }

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', not_found=True), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', server_error=True), 500

    return app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  LIBRARY MANAGEMENT SYSTEM - DBMS PROJECT RUNNING")
    print(f"  URL: http://127.0.0.1:5000")
    print("  Admin Credentials: admin / admin123")
    print("  Student Credentials Example: 2417119 / std119")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=Config.DEBUG)
