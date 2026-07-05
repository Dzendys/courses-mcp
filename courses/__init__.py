"""
Courses.FIT.CVUT.cz Scraper & MCP Server package.
Provides interfaces to fetch courses, index subpages, scrape content, and search subject pages.
"""

from .config import CoursesConfig
from .client import CoursesClient

__all__ = ["CoursesConfig", "CoursesClient"]
