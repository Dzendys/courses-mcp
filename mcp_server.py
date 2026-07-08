#!/usr/bin/env python3
import os
import sys
from typing import Optional
from dotenv import load_dotenv, set_key

# Ensure standard import path works
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from courses import CoursesClient, CoursesConfig

# Initialize FastMCP server
mcp = FastMCP("courses")

def get_client(cookies: str = "") -> CoursesClient:
    """Helper to initialize CoursesClient from env or parameter cookies."""
    config = CoursesConfig.from_env()
    
    # Priority: 1. Passed parameter, 2. Env variable
    if cookies:
        config.cookies_str = cookies
        
    client = CoursesClient(config)
    return client


@mcp.tool()
def login() -> str:
    """
    Performs CTU OAuth login handshake using credentials from the local .env file.
    Saves the retrieved cookies back to the local .env file so future calls
    will remain authenticated automatically.
    """
    client = get_client()
    success, msg = client.login_and_save()
    
    if success:
        return f"Success! {msg}\nSession cookies retrieved and saved to .env."
    else:
        return f"Login failed: {msg}"

@mcp.tool()
def list_courses() -> str:
    """
    Lists subjects/courses available at FIT CTU.
    If authenticated (via environment variables), highlights the courses
    the user is currently enrolled in (studying or teaching).
    """
    client = get_client()
    try:
        res = client.list_courses()
        
        output = []
        if res["authenticated"]:
            user_info = client.get_user_info() or {}
            fullname = user_info.get("fullName", os.getenv("COURSES_USERNAME", "Student"))
            output.append(f"### Logged in as: {fullname} ({user_info.get('username', '')})")
            
            output.append("\n#### 📚 Enrolled Studying Courses:")
            if res["studying"]:
                for c in res["studying"]:
                    output.append(f"- **[{c['code']}]** {c['title']} - {c['url']}")
            else:
                output.append("- None found")
                
            if res["teaching"]:
                output.append("\n#### 🎓 Enrolled Teaching Courses:")
                for c in res["teaching"]:
                    output.append(f"- **[{c['code']}]** {c['title']} - {c['url']}")
            
            output.append(f"\n#### 📁 Other catalog courses (Total {len(res['all_courses'])}):")
        else:
            output.append("### ℹ️ Unauthenticated (showing full FIT course catalog):")
            output.append(f"Total catalog courses: {len(res['all_courses'])}")
            
        # List first 100 courses from catalog to avoid blowing up context window
        limit = 100
        output.append(f"\nListing first {limit} courses:")
        for c in res["all_courses"][:limit]:
            output.append(f"- **[{c['code']}]** {c['title']} - {c['url']}")
            
        if len(res["all_courses"]) > limit:
            output.append(f"\n... and {len(res['all_courses']) - limit} more courses. Use course codes to inspect specific courses directly.")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error listing courses: {str(e)}"

@mcp.tool()
def get_course_index(course_code: str) -> str:
    """
    Fetches the home page of a subject and parses the navigation hierarchy/sidebar.
    Lists all available subpages (paths and titles) for this course.
    
    Args:
        course_code: Code of the course (e.g. 'BI-OSY', 'BI-PJV').
    """
    client = get_client()
    try:
        pages = client.get_course_index(course_code)
        if not pages:
            return f"No subpages found for course {course_code.upper()}."
            
        output = [f"### Pages for course {course_code.upper()}:\n"]
        for p in pages:
            output.append(f"- {p['title']} (path: `{p['path']}`)")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching index for course {course_code.upper()}: {str(e)}"

@mcp.tool()
def get_page_content(course_code: str, page_path: str) -> str:
    """
    Fetches a specific subpage of a course and returns the main section content
    converted into clean, readable Markdown.
    
    Args:
        course_code: Code of the course (e.g. 'BI-OSY').
        page_path: Relative path of the page (get this from get_course_index, e.g. 'lectures/index.html' or 'classification/index.html').
    """
    client = get_client()
    try:
        content = client.get_page_content(course_code, page_path)
        return content
    except Exception as e:
        return f"Error reading page {page_path} in course {course_code.upper()}: {str(e)}"

@mcp.tool()
def search_course_content(course_code: str, query: str) -> str:
    """
    Searches the content of all pages in a specific course for the keyword query.
    Caches scraped pages locally to speed up subsequent search requests.
    
    Args:
        course_code: Code of the course (e.g. 'BI-OSY').
        query: Keyword or phrase to search for.
    """
    client = get_client()
    try:
        matches = client.search_course_content(course_code, query)
        if not matches:
            return f"No matches found for '{query}' in course {course_code.upper()}."
            
        output = [f"### Search results for '{query}' in course {course_code.upper()} ({len(matches)} matches):\n"]
        for m in matches:
            output.append(f"#### {m['title']} (path: `{m['path']}`)")
            output.append(f"Snippet: {m['snippet']}\n")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error searching course content: {str(e)}"

@mcp.tool()
def download_course_file(course_code: str, file_path: str) -> str:
    """
    Downloads any file (PDF slides, ZIP archives, scripts) linked on the official course pages
    using the current authenticated session, saving it to the local project directory.
    
    Args:
        course_code: Code of the course (e.g. 'BI-OSY').
        file_path: Relative path of the file to download (e.g. 'lectures/01-intro.pdf' or 'labs/01-setup.zip').
    """
    client = get_client()
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(base_dir, "downloads", course_code.upper(), file_path)
        actual_path = client.download_file(course_code, file_path, save_path)
        rel_path = os.path.relpath(actual_path, base_dir)
        return f"Success! File downloaded and saved to: {rel_path} (absolute: {actual_path})"
    except Exception as e:
        return f"Error downloading file: {str(e)}"

@mcp.resource("courses://list")
def list_courses_resource() -> str:
    """Exposes the list of subjects/courses."""
    return list_courses()

@mcp.resource("courses://{course_code}/index")
def get_course_index_resource(course_code: str) -> str:
    """Exposes the navigation menu/sidebar for a subject."""
    return get_course_index(course_code)

@mcp.resource("courses://{course_code}/pages/{page_path}")
def get_page_content_resource(course_code: str, page_path: str) -> str:
    """Exposes the main section of a specific course subpage in Markdown."""
    import urllib.parse
    decoded_path = urllib.parse.unquote(page_path)
    return get_page_content(course_code, decoded_path)

if __name__ == "__main__":
    mcp.run()

