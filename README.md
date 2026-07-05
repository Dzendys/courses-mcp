# Courses.FIT.CVUT.cz MCP Server

An MCP (Model Context Protocol) server designed for the Faculty of Information Technology, Czech Technical University (FIT CTU) course materials site: `courses.fit.cvut.cz`. 

It enables LLMs (such as Cline, Cursor, or Open WebUI) to list subjects, navigate their subpages (lectures, labs, exams), read materials converted to clean Markdown, and perform quick keyword searches across subjects.

---

## Features

- 🔑 **Dual Authentication:** Supports logging in using pre-fetched browser session cookies or CTU credentials (username & password) with automatic cookie persistence.
- 🎓 **Enrolled Semester Courses:** Detects and lists subjects currently enrolled by the student.
- 📂 **Static Site Navigation:** Crawls and resolves the navigation sidebar (PagesFIT/MkDocs) of any course.
- 📝 **Clean Markdown:** Isolates primary content sections (e.g. `<main>`, `<article>`) and converts them to readable, clean Markdown.
- 🔍 **Indexed Keyword Search:** Iterates through course pages and searches for keywords, with local caching to speed up consecutive searches.

---

## Installation

1. Clone or copy this repository into your chosen directory.
2. Initialize the Python virtual environment and install the required dependencies:
   ```bash
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ```

---

## Configuration

Duplicate the `.env.example` file to `.env` and set up your preferred authentication method:

```env
# OPTION 1: Set session cookies directly (Recommended if you use MFA)
COURSES_COOKIES="oauth_access_token=...; oauth_refresh_token=...; oauth_username=matejj50"

# OPTION 2: Set credentials for automatic OAuth login handshake
COURSES_USERNAME="matejj50"
COURSES_PASSWORD="your-ctu-password"
```

---

## Registered MCP Tools

The server exposes the following tools:

- `login(username, password)`: Performs CTU login, updates session cookies, and writes the retrieved cookies to the `.env` file for automatic persistent logins.
- `list_courses(cookies)`: Lists subjects taught at FIT. If authenticated, separates your current semester courses from all other catalog subjects.
- `get_course_index(course_code)`: Retrieves all available subpages (paths and titles) from the sidebar menu of a course.
- `get_page_content(course_code, page_path)`: Fetches a specific course subpage and returns its main section in Markdown format.
- `search_course_content(course_code, query)`: Scrapes (or reads from cache) all pages of a course and returns matching search snippets.

---

## Global MCP Integration

Add this configuration to your local MCP client settings (e.g. `mcp_config.json`):

```json
{
  "mcpServers": {
    "courses-mcp": {
      "command": "/home/dzendys_/Downloads/courses-mcp/venv/bin/python",
      "args": ["/home/dzendys_/Downloads/courses-mcp/mcp_server.py"]
    }
  }
}
```

---

## License

Created for educational and utility purposes for students and teachers of FIT ČVUT.
