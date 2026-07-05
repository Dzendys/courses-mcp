import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CoursesConfig:
    """
    Configuration for the Courses.FIT.CVUT.cz Client and MCP Server.
    """
    def __init__(
        self,
        cookies_str: str = "",
        username: str = "",
        password: str = "",
        base_url: str = "https://courses.fit.cvut.cz",
        cache_dir: str = "cache"
    ):
        self.cookies_str = cookies_str
        self.username = username
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.cache_dir = cache_dir
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @classmethod
    def from_env(cls) -> 'CoursesConfig':
        """
        Loads configuration from environment variables (.env).
        """
        cookies_str = os.getenv("COURSES_COOKIES", "")
        username = os.getenv("COURSES_USERNAME", "")
        password = os.getenv("COURSES_PASSWORD", "")
        base_url = os.getenv("COURSES_BASE_URL", "https://courses.fit.cvut.cz")
        cache_dir = os.getenv("COURSES_CACHE_DIR", "cache")
        
        return cls(
            cookies_str=cookies_str,
            username=username,
            password=password,
            base_url=base_url,
            cache_dir=cache_dir
        )
