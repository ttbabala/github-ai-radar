from __future__ import annotations
import base64
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GitHubClient:
    API = "https://api.github.com"
    def __init__(self, token=None):
        self.token = token if token is not None else os.getenv("GITHUB_TOKEN")
    def request(self, url):
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "github-ai-radar"}
        if self.token: headers["Authorization"] = f"Bearer {self.token}"
        req = Request(url, headers=headers)
        for attempt in range(4):
            try:
                with urlopen(req, timeout=30) as response:
                    import json
                    return json.loads(response.read())
            except HTTPError as e:
                if e.code in (403, 429) and attempt < 3:
                    time.sleep(min(60, int(e.headers.get("Retry-After", 2 ** (attempt + 1))))); continue
                raise RuntimeError(f"GitHub API returned HTTP {e.code}: {e.reason}") from e
            except URLError as e:
                # DNS failures are environmental and retrying each query only delays a clear failure.
                if "nodename nor servname" in str(e.reason) or "Name or service not known" in str(e.reason):
                    raise RuntimeError(f"Unable to reach GitHub API: {e.reason}") from e
                if attempt < 3: time.sleep(2 ** attempt); continue
                raise RuntimeError(f"Unable to reach GitHub API: {e.reason}") from e
    def search(self, query, limit=30):
        data = self.request(self.API + "/search/repositories?" + urlencode({"q": query + " pushed:>" + __import__("datetime").date.today().isoformat(), "sort": "stars", "order": "desc", "per_page": min(100, limit)}))
        return data.get("items", [])
    def repo(self, full_name): return self.request(self.API + "/repos/" + full_name)
    def latest_release(self, full_name):
        try:
            data = self.request(self.API + "/repos/" + full_name + "/releases/latest")
            return {"tag_name": data.get("tag_name"), "published_at": data.get("published_at"), "html_url": data.get("html_url")}
        except Exception:
            return None
    def readme(self, full_name):
        try:
            data = self.request(self.API + "/repos/" + full_name + "/readme")
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")[:12000]
        except Exception:
            return None
    def trending(self):
        # GitHub Trending has no official API; parse only repository links from its public page.
        from urllib.request import Request, urlopen
        req = Request("https://github.com/trending?since=weekly", headers={"User-Agent": "Mozilla/5.0 github-ai-radar"})
        try:
            html = urlopen(req, timeout=20).read().decode("utf-8", "replace")
        except Exception:
            return []
        import re
        names = list(dict.fromkeys(re.findall(r'href="/([\w.-]+/[\w.-]+)"', html)))
        result = []
        for name in names[:50]:
            if name not in ("features/", "topics/", "collections/"):
                try: result.append(self.repo(name))
                except Exception: pass
        return result
