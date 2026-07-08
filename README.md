# Courses MCP Server

An MCP (Model Context Protocol) server designed for the Faculty of Information Technology, Czech Technical University (FIT CTU) course materials site: courses.fit.cvut.cz.

It enables LLMs (such as Claude, AGY, or Open WebUI) to list subjects, navigate their subpages (lectures, labs, exams), read materials converted to clean Markdown, and perform quick keyword searches across subjects.

---

## Features

- **Dual Authentication:** Supports logging in using pre-fetched browser session cookies or CTU credentials (username and password) with fully automatic cookie status detection, renewal, and persistence.
- **Enrolled Semester Courses:** Detects and lists subjects currently enrolled by the student.
- **Static Site Navigation:** Crawls and resolves the navigation sidebar (PagesFIT/MkDocs) of any course.
- **Clean Markdown:** Isolates primary content sections (e.g. `<main>`, `<article>`) and converts them to readable, clean Markdown.
- **Indexed Keyword Search:** Iterates through course pages and searches for keywords, with local caching to speed up consecutive searches.

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
COURSES_COOKIES="oauth_access_token=YOUR_ACCESS_TOKEN; oauth_refresh_token=YOUR_REFRESH_TOKEN; oauth_username=YOUR_USERNAME"

# OPTION 2: Set credentials for automatic OAuth login handshake
COURSES_USERNAME="YOUR_CTU_USERNAME"
COURSES_PASSWORD="YOUR_CTU_PASSWORD"
```

---

## MCP Server Setup

The MCP server exposes Fit-Courses tools to LLM clients. It runs via stdio or streamable-http.

### Client Configuration

Add the following to your client's MCP configuration file. Cookies are loaded from the `.env` file (see [`.env.example`](.env.example)).

```json
{
  "mcpServers": {
    "courses": {
      "command": "/path/to/courses/venv/bin/python",
      "args": ["/path/to/courses/mcp_server.py"]
    }
  }
}
```

### Config File Locations

| Client | Path |
|---|---|
| Claude Desktop | `~/.config/Claude/claude_desktop_config.json` |
| AGY (CLI) | `~/.gemini/antigravity-cli/mcp_config.json` |
| AGY (IDE / 2.0) | `~/.gemini/config/mcp_config.json` |
| OpenCode | `.opencode.json` in the workspace root |

Restart the client after saving.

### Transports

- **stdio** (default) – the client spawns the server as a subprocess. Use for Claude Desktop, AGY, OpenCode.
- **streamable-http** – for Docker or remote setups. Set `MCP_TRANSPORT=streamable-http` and point the client to `http://host:8000/mcp`.

---

## Exposed MCP Tools

- `login` – Performs CTU login using credentials from the local `.env` file, and writes the retrieved cookies to the `.env` file for automatic persistent logins (parameterless).
- `list_courses` – Lists subjects taught at FIT. If authenticated, separates your current semester courses from all other catalog subjects.
- `get_course_index` – Retrieves all available subpages (paths and titles) from the sidebar menu of a course.
- `get_page_content` – Fetches a specific course subpage and returns its main section in Markdown format.
- `search_course_content` – Scrapes (or reads from cache) all pages of a course and returns matching search snippets.
- `download_course_file` – Downloads any linked slide (PDF), code, or file from the course portal.

*Note: None of the tools require passing session cookies manually; authentication status is detected on the fly and expired cookies are automatically renewed and persisted to the `.env` file.*

---

## Exposed MCP Resources

The server exposes the following read-only resources:

- `courses://list` – Returns the list of subjects/courses.
- `courses://{course_code}/index` – Returns the navigation index sidebar of a subject.
- `courses://{course_code}/pages/{page_path}` – Returns the content of a specific course subpage in Markdown. *(Note: For nested paths, URL-encode the slashes as `%2F`, e.g., `lectures%2Findex.html`)*
