from flask import Flask, redirect, url_for, session, render_template, request, g
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

    @app.after_request
    def preserve_post_queries(response):
        """Preserve SQL queries from POST/mutation requests across redirects."""
        if request.method in ('POST', 'PUT', 'DELETE') and hasattr(g, 'sql_queries') and g.sql_queries:
            session['_last_action_queries'] = {
                'endpoint': request.path,
                'method': request.method,
                'queries': list(g.sql_queries)
            }
        return response

    @app.context_processor
    def inject_global_data():
        """Inject current year, session user details, and SQL queries globally to all templates."""
        recent_action = session.pop('_last_action_queries', None)
        return {
            'current_year': datetime.now().year,
            'logged_in': 'user_id' in session,
            'user_role': session.get('role'),
            'user_name': session.get('full_name') or session.get('username'),
            'user_roll': session.get('roll_number'),
            'page_sql_queries': getattr(g, 'sql_queries', []),
            'recent_action_queries': recent_action
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
