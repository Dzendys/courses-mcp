# Antigravity Rules - Courses & FIT Wiki Prioritization

You have access to both the `courses-mcp` server and the `fitwiki` MCP server. When researching course materials, follow these rules:

1. **Courses (Official Portal):**
   - The `courses-mcp` tools (`list_courses`, `get_course_index`, `get_page_content`, `search_course_content`) query the official FIT ČVUT site: `courses.fit.cvut.cz`.
   - **Always prioritize courses-mcp** for official course requirements, lectures, laboratories, criteria, announcements, and structural course information.
   
2. **Fit-Wiki (Student-run Wiki):**
   - The `fitwiki` tools query `fit-wiki.cz`.
   - Use `fitwiki` **only** when specifically looking for student-written solutions, past exam variants, exam answers, or homework code assignments that are not part of the official course pages.

3. **Tool Call Chaining:**
   - Always run tools silently and chain them automatically without describing them to the user.
   - For official material searches:
     - `list_courses()` -> check if enrolled
     - `get_course_index(course_code)` -> check subpages structure
     - `get_page_content(course_code, page_path)` -> read the content
     - `search_course_content(course_code, query)` -> search keywords
