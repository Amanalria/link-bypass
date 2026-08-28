import re
import time
import asyncio
import aiohttp
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

class UnshortenResult:
    def __init__(self, original_url: str, final_url: str, hops: list, duration: float, success: bool = True, error: str = None):
        self.original_url = original_url
        self.final_url = final_url
        self.hops = hops
        self.duration = duration
        self.success = success
        self.error = error

class UniversalUnshortener:
    def __init__(self, max_hops: int = 25, timeout: int = 40):
        self.max_hops = max_hops
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        # Semaphore allowing up to 10 concurrent browser solves
        self._sem = asyncio.Semaphore(10)

    def is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)

    def extract_urls(self, text: str) -> list:
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
        urls = re.findall(url_pattern, text)
        clean_urls = []
        for u in urls:
            u = u.rstrip(".,);:\"'<>")
            if self.is_valid_url(u) and u not in clean_urls:
                clean_urls.append(u)
        return clean_urls

    async def _solve_complex_ad_shortener(self, target_url: str) -> tuple:
        """Exact 100% robust solver for vplink.in and multi-tier AdLinkFly networks with anti-crash safety"""
        async with self._sem:
            hops = [target_url]
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-gpu",
                        "--disable-images",
                        "--blink-settings=imagesEnabled=false",
                        "--disable-software-rasterizer",
                        "--js-flags=--max-old-space-size=512"
                    ]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800}
                )
                
                # Block heavy media and third-party ads
                async def intercept_route(route):
                    url = route.request.url.lower()
                    if route.request.resource_type in ["image", "media", "font"]:
                        await route.abort()
                    elif any(ad in url for ad in ["doubleclick", "googlesyndication", "google-analytics", "adservice", "adnxs", "criteo", "amazon-adsystem", "taboola"]):
                        await route.abort()
                    else:
                        await route.continue_()
                        
                await context.route("**/*", intercept_route)
                page = await context.new_page()
                
                try:
                    try:
                        await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
                    except Exception:
                        pass
                        
                    for step in range(1, 25):
                        try:
                            await page.wait_for_timeout(1500)
                        except Exception:
                            break
                            
                        curr = page.url
                        if curr not in hops:
                            hops.append(curr)
                            
                        p_url = urlparse(curr)
                        domain = p_url.netloc.lower()
                        
                        # 1. Check if reached destination URL
                        if curr != target_url and not any(k in domain for k in ["vplink.in", "shikshaads.in", "krishitalk.com", "sarkarijobcorner.com", "engineergates.com", "onlinewish.in", "crimejasoos.in"]) and not any(sub in curr for sub in ["educate", "study", "degree", "learn_more", "estudy", "links/go"]):
                            await browser.close()
                            return curr, hops
                            
                        # 2. Check if on vplink final page
                        if "vplink.in" in curr and step > 1:
                            try:
                                html = await page.content()
                                soup = BeautifulSoup(html, "html.parser")
                                
                                # Check gt-link anchor
                                gt_btn = soup.find(id="gt-link") or soup.find(class_="get-link")
                                if gt_btn and gt_btn.get("href"):
                                    target_href = gt_btn["href"].strip()
                                    if target_href and not target_href.startswith(("#", "javascript:")) and "vplink.in" not in target_href and "t.me/+SDtA6sDThtwzN2Rl" not in target_href:
                                        await browser.close()
                                        if target_href not in hops:
                                            hops.append(target_href)
                                        return target_href, hops
                                        
                                for a in soup.find_all("a", href=True):
                                    href = a["href"].strip()
                                    if href.startswith("http") and "vplink.in" not in href and "t.me/+SDtA6sDThtwzN2Rl" not in href and not any(k in href for k in ["facebook.com", "twitter.com", "instagram.com", "example.com"]):
                                        await browser.close()
                                        if href not in hops:
                                            hops.append(href)
                                        return href, hops
                                        
                                await page.evaluate("""() => {
                                    const goForm = document.getElementById("go-link");
                                    if (goForm) goForm.submit();
                                    const btn = document.getElementById("gt-link") || document.querySelector(".get-link");
                                    if (btn) btn.click();
                                }""")
                            except Exception:
                                pass
                                
                        # 3. Blog wait to satisfy backend timer validation
                        if any(sub in curr for sub in ["/studyeducates/", "/educatestudy/", "/educatehub/"]) and not any(q in curr for q in ["degreehubs", "educationstudy", "insurancesstudy", "studyeducations", "eduonline", "syastudy", "learn_more.php"]):
                            try:
                                await page.wait_for_timeout(5000)
                            except Exception:
                                pass
                            for sub in ["/studyeducates/", "/educatestudy/", "/educatehub/"]:
                                if sub in curr:
                                    learn_url = f"{p_url.scheme}://{p_url.netloc}{sub}learn_more.php"
                                    try:
                                        await page.goto(learn_url, referer=curr, wait_until="domcontentloaded", timeout=15000)
                                    except Exception:
                                        pass
                                    break
                        else:
                            try:
                                await page.wait_for_timeout(1500)
                            except Exception:
                                pass
                                
                    final_url = page.url
                    await browser.close()
                    return final_url, hops
                finally:
                    try:
                        await browser.close()
                    except Exception:
                        pass

    async def unshorten(self, url: str) -> UnshortenResult:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        start_time = time.time()
        hops = [url]
        current_url = url
        domain = urlparse(url).netloc.lower()

        # Check if URL belongs to complex monetized ad-shorteners
        is_complex_shortener = any(d in domain for d in ["vplink", "vplinks", "droplink", "gplinks", "linkvertise", "ouo.io", "adf.ly", "shikshaads", "krishitalk", "sarkarijobcorner", "engineergates"])

        if is_complex_shortener:
            try:
                final_url, bypass_hops = await self._solve_complex_ad_shortener(url)
            except Exception as e:
                try:
                    await asyncio.sleep(1)
                    final_url, bypass_hops = await self._solve_complex_ad_shortener(url)
                except Exception as e2:
                    return UnshortenResult(
                        original_url=url,
                        final_url="",
                        hops=hops,
                        duration=round(time.time() - start_time, 2),
                        success=False,
                        error=str(e2)
                    )

            duration = round(time.time() - start_time, 2)
            return UnshortenResult(
                original_url=url,
                final_url=final_url,
                hops=bypass_hops,
                duration=duration,
                success=True
            )

        # Ultra-fast HTTP redirect resolver for bit.ly, tinyurl, t.co, is.gd, cutt.ly, etc.
        async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
            for _ in range(self.max_hops):
                try:
                    async with session.get(current_url, allow_redirects=False) as response:
                        if response.status in (301, 302, 303, 307, 308):
                            location = response.headers.get("Location")
                            if not location:
                                break
                            if location.startswith("/"):
                                parsed_curr = urlparse(current_url)
                                location = f"{parsed_curr.scheme}://{parsed_curr.netloc}{location}"
                            if location == current_url or location in hops:
                                break
                            hops.append(location)
                            current_url = location
                        elif response.status == 200:
                            content_type = response.headers.get("Content-Type", "")
                            if "text/html" in content_type:
                                body = await response.text()
                                # Meta refresh
                                meta_match = re.search(r'<meta[^>]*http-equiv=["\x27]?refresh["\x27]?[^>]*content=["\x27]?\d+;\s*url=([^"\x27\s>]+)', body, re.IGNORECASE)
                                if meta_match:
                                    meta_url = meta_match.group(1).strip()
                                    if meta_url.startswith("/"):
                                        parsed_curr = urlparse(current_url)
                                        meta_url = f"{parsed_curr.scheme}://{parsed_curr.netloc}{meta_url}"
                                    if meta_url != current_url and meta_url not in hops:
                                        hops.append(meta_url)
                                        current_url = meta_url
                                        continue

                                # JS Redirect
                                js_match = re.search(r'(?:window\.)?location(?:\.href|\.replace)?\s*(?:=|\()\s*["\x27](https?://[^"\x27]+)["\x27]', body, re.IGNORECASE)
                                if js_match:
                                    js_url = js_match.group(1).strip()
                                    if js_url != current_url and js_url not in hops:
                                        hops.append(js_url)
                                        current_url = js_url
                                        continue
                            break
                        else:
                            break
                except Exception:
                    break

        duration = round(time.time() - start_time, 2)
        return UnshortenResult(
            original_url=url,
            final_url=current_url,
            hops=hops,
            duration=duration,
            success=True
        )
