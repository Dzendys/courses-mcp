import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
import markdownify

class CoursesClient:
    def __init__(self, cookies_str=None, username=None, password=None, cache_dir="cache"):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        self.username = username
        self.password = password
        self.cache_dir = cache_dir
        
        if cookies_str:
            self.set_cookies(cookies_str)
            
    def set_cookies(self, cookies_str):
        """Parses a cookie string and sets it in the requests session."""
        for cookie_item in cookies_str.split(";"):
            cookie_item = cookie_item.strip()
            if "=" in cookie_item:
                k, v = cookie_item.split("=", 1)
                self.session.cookies.set(k, v, domain="courses.fit.cvut.cz")
                
        # Also set Bearer token if oauth_access_token cookie is present
        token = self.session.cookies.get("oauth_access_token", domain="courses.fit.cvut.cz")
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def login(self):
        """Performs programmatic OAuth login using CTU credentials."""
        if not self.username or not self.password:
            return False, "Username or password not provided."
            
        try:
            # 1. Initialize the OAuth flow by requesting a course page
            init_url = "https://courses.fit.cvut.cz/BI-OSY/index.html"
            r1 = self.session.get(init_url, allow_redirects=True)
            
            # 2. Check if we are already logged in
            if "oauth_access_token" in self.session.cookies.get_dict(domain="courses.fit.cvut.cz"):
                token = self.session.cookies.get("oauth_access_token", domain="courses.fit.cvut.cz")
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                return True, "Already authenticated."
                
            # 3. Post credentials to auth.fit.cvut.cz
            login_url = "https://auth.fit.cvut.cz/login.do"
            payload = {
                "j_username": self.username,
                "j_password": self.password
            }
            
            # Follow redirects to complete the handshake
            r2 = self.session.post(login_url, data=payload, allow_redirects=True)
            
            # 4. Check if authentication cookies are now set
            cookies = self.session.cookies.get_dict(domain="courses.fit.cvut.cz")
            if "oauth_access_token" in cookies:
                token = cookies["oauth_access_token"]
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                return True, "Successfully logged in."
            else:
                # Let's inspect final URL or response to provide a diagnostic message
                if "login.html" in r2.url or "login.do" in r2.url:
                    return False, "Authentication failed: invalid username or password."
                return False, f"Login failed. Ended up at {r2.url}. Session cookies: {list(cookies.keys())}"
                
        except Exception as e:
            return False, f"Exception during login: {str(e)}"

    def get_user_info(self):
        """Fetches information about the currently logged in user."""
        try:
            r = self.session.get("https://courses.fit.cvut.cz/api/v2/users/me")
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return None

    def list_courses(self):
        """
        Lists all courses. If authenticated, highlights courses the user is studying or teaching.
        """
        # Fetch all courses from global catalog
        courses_map = {}
        try:
            r_all = self.session.get("https://courses.fit.cvut.cz/data/courses-all.json")
            if r_all.status_code == 200:
                courses_map = r_all.json().get("courses", {})
        except Exception as e:
            print("Failed to fetch global courses:", e)

        # Fetch user-specific courses if logged in
        user_courses = {"studying": [], "teaching": []}
        is_authenticated = False
        try:
            r_me = self.session.get("https://courses.fit.cvut.cz/api/v2/users/me/courses")
            if r_me.status_code == 200:
                user_courses = r_me.json()
                is_authenticated = True
        except:
            pass

        # Build output structure
        enrolled_studying = []
        enrolled_teaching = []
        all_other_courses = []

        # Parse enrolled studying
        for code_with_suffix in user_courses.get("studying", []):
            code = code_with_suffix.split(".")[0].upper()
            info = courses_map.get(code, {})
            enrolled_studying.append({
                "code": code,
                "title": info.get("nameCs", code),
                "url": f"https://courses.fit.cvut.cz/{code}/",
                "enrolled_code": code_with_suffix
            })

        # Parse enrolled teaching
        for code_with_suffix in user_courses.get("teaching", []):
            code = code_with_suffix.split(".")[0].upper()
            info = courses_map.get(code, {})
            enrolled_teaching.append({
                "code": code,
                "title": info.get("nameCs", code),
                "url": f"https://courses.fit.cvut.cz/{code}/",
                "enrolled_code": code_with_suffix
            })

        # Parse all other courses
        enrolled_codes = set(c["code"] for c in enrolled_studying + enrolled_teaching)
        for code, info in courses_map.items():
            if code not in enrolled_codes:
                all_other_courses.append({
                    "code": code,
                    "title": info.get("nameCs", code),
                    "url": f"https://courses.fit.cvut.cz/{code}/"
                })

        return {
            "authenticated": is_authenticated,
            "studying": enrolled_studying,
            "teaching": enrolled_teaching,
            "all_courses": all_other_courses
        }

    def get_course_index(self, course_code):
        """
        Fetches the course home page and parses the navigation hierarchy (sidebar menu).
        """
        course_code = course_code.strip().upper()
        # Clean suffix if provided (e.g. BI-OSY.21 -> BI-OSY)
        course_code = course_code.split(".")[0]
        
        base_url = f"https://courses.fit.cvut.cz/{course_code}/"
        index_url = base_url + "index.html"
        
        r = self.session.get(index_url, allow_redirects=True)
        r.encoding = "utf-8"
        
        if r.status_code != 200:
            # Try without index.html
            index_url = base_url
            r = self.session.get(index_url, allow_redirects=True)
            r.encoding = "utf-8"
            
        if r.status_code != 200:
            raise Exception(f"Course {course_code} not found or inaccessible (HTTP {r.status_code})")
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Look for the site navigation element (<nav id="nav"> or similar)
        nav_tag = soup.find("nav", id="nav") or soup.find("nav", class_="site-nav")
        if not nav_tag:
            # Fallback to any nav or sidebar
            nav_tag = soup.find("nav") or soup.find("div", class_="sidebar") or soup.find("div", id="sidebar")
            
        pages = []
        if nav_tag:
            links = nav_tag.find_all("a", href=True)
            for link in links:
                href = link["href"]
                # Skip anchors or external links
                if href.startswith("#") or href.startswith("http"):
                    continue
                title = link.text.strip()
                # Normalize relative URL
                full_url = urllib.parse.urljoin(base_url, href)
                relative_path = urllib.parse.urlparse(full_url).path.replace(f"/{course_code}/", "")
                
                # Deduplicate pages
                if not any(p["path"] == relative_path for p in pages):
                    pages.append({
                        "title": title,
                        "path": relative_path,
                        "url": full_url
                    })
        else:
            # Fallback: find all links inside the main page that start with course_code
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if not href.startswith("http") and not href.startswith("#"):
                    full_url = urllib.parse.urljoin(base_url, href)
                    if f"/{course_code}/" in full_url:
                        relative_path = urllib.parse.urlparse(full_url).path.replace(f"/{course_code}/", "")
                        title = link.text.strip() or relative_path
                        if not any(p["path"] == relative_path for p in pages):
                            pages.append({
                                "title": title,
                                "path": relative_path,
                                "url": full_url
                            })
                            
        return pages

    def get_page_content(self, course_code, page_path):
        """
        Fetches a subpage of a course and returns the parsed markdown content of the main section.
        """
        course_code = course_code.strip().upper().split(".")[0]
        page_path = page_path.strip().lstrip("/")
        
        url = f"https://courses.fit.cvut.cz/{course_code}/{page_path}"
        r = self.session.get(url, allow_redirects=True)
        r.encoding = "utf-8"
        
        if r.status_code != 200:
            raise Exception(f"Failed to fetch page {page_path} for course {course_code} (HTTP {r.status_code})")
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Look for primary content area
        content_tag = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
        if not content_tag:
            content_tag = soup.find("div", id="content") or soup.find("div", class_="main-content")
            
        # Fallback to body
        if not content_tag:
            content_tag = soup.body
            
        if not content_tag:
            return "No content found on page."
            
        # Strip navigation/header elements if we fell back to body
        if content_tag == soup.body:
            for n in content_tag.find_all(["nav", "header", "footer"]):
                n.decompose()
                
        # Convert HTML to clean markdown
        md = markdownify.markdownify(str(content_tag), heading_style="ATX")
        
        # Clean up double backslashes and redundant newlines
        md = re.sub(r'\n\s*\n\s*\n+', '\n\n', md)
        return md.strip()

    def search_course_content(self, course_code, query):
        """
        Scrapes (or reads from cache) all pages of a course and searches for the query.
        """
        course_code = course_code.strip().upper().split(".")[0]
        query = query.strip().lower()
        
        pages = self.get_course_index(course_code)
        matches = []
        
        # Setup course cache dir
        course_cache = os.path.join(self.cache_dir, course_code)
        os.makedirs(course_cache, exist_ok=True)
        
        for page in pages:
            path_slug = page["path"].replace("/", "_").replace(".html", "")
            if not path_slug or path_slug == "_":
                path_slug = "index"
                
            cache_file = os.path.join(course_cache, f"{path_slug}.md")
            
            # Read from cache if it exists, otherwise fetch and cache
            content = None
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        content = f.read()
                except:
                    pass
                    
            if not content:
                try:
                    content = self.get_page_content(course_code, page["path"])
                    # Save to cache
                    with open(cache_file, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    print(f"Skipping {page['path']} due to error: {e}")
                    continue
            
            # Search in content
            if query in content.lower():
                # Find a snippet around the match
                idx = content.lower().find(query)
                start = max(0, idx - 100)
                end = min(len(content), idx + len(query) + 150)
                snippet = content[start:end].replace("\n", " ")
                
                matches.append({
                    "title": page["title"],
                    "path": page["path"],
                    "url": page["url"],
                    "snippet": f"...{snippet}..."
                })
                
        return matches
