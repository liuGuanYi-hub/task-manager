"""路由包"""
from routes.stats_routes import stats_bp
from routes.tags_routes import tags_bp
from routes.weekly_routes import weekly_bp
from routes.calendar_routes import calendar_bp
from routes.projects_routes import projects_bp
from routes.settings_routes import settings_bp

__all__ = [
    'stats_bp',
    'tags_bp',
    'weekly_bp',
    'calendar_bp',
    'projects_bp',
    'settings_bp'
]
