import logging
from typing import List, Dict
from playwright.sync_api import sync_playwright, Page
from utils import DataConverter

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class YouTubeScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.results = []

    def _handle_consent(self, page: Page):
        """Clicks 'Accept all' if the Google consent dialog appears."""
        try:
            accept_btn = page.locator('button[aria-label="Accept all"]')
            if accept_btn.count() > 0:
                accept_btn.first.click(force=True)
                page.wait_for_timeout(1000)
        except Exception:
            pass

    def _click_popular_tab(self, page: Page):
        """Navigates to the Popular videos tab."""
        popular_tab = page.get_by_role("tab", name="Popular").first
        popular_tab.wait_for(state="visible", timeout=10000)
        popular_tab.click(force=True)
        # Wait for the selection to be visually confirmed and cards to load
        page.get_by_role("tab", name="Popular", selected=True).wait_for(timeout=5000)
        page.wait_for_timeout(2000)

    def _scroll_to_load(self, page: Page, max_scrolls: int):
        """Scrolls the page to trigger infinite load."""
        retries = 0
        for i in range(max_scrolls):
            # We count actual video titles to avoid counting empty 'ghost' boxes
            selector = 'ytd-rich-item-renderer a#video-title-link'
            last_count = page.locator(selector).count()
            page.keyboard.press("End")
            
            try:
                page.wait_for_function(f"document.querySelectorAll('{selector}').length > {last_count}", timeout=4000)
                logging.info(f"Scroll {i+1}/{max_scrolls} - Videos loaded: {page.locator(selector).count()}")
                retries = 0
            except Exception:
                retries += 1
                if retries >= 2:
                    logging.info("End of list or slow connection reached.")
                    break

    def _extract_data_js(self, page: Page) -> List[Dict]:
        """Injects JS to grab all data in one trip across the bridge."""
        return page.evaluate("""
            () => [...document.querySelectorAll('ytd-rich-item-renderer')].map(vid => {
                const titleElem = vid.querySelector('a#video-title-link');
                const meta = vid.querySelectorAll('.inline-metadata-item');
                return {
                    title: titleElem?.getAttribute('title') || '',
                    href: titleElem?.getAttribute('href') || '',
                    views: meta[0]?.innerText || '0 views',
                    date: meta[1]?.innerText || '1 day ago'
                };
            }).filter(v => v.title !== '')
        """)

    def scrape_channel(self, url: str, max_scrolls: int = 10) -> List[Dict]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            logging.info(f"Opening: {url}")
            page.goto(url, wait_until="domcontentloaded")
            
            self._handle_consent(page)
            self._click_popular_tab(page)
            self._scroll_to_load(page, max_scrolls)
            
            raw_data = self._extract_data_js(page)
            browser.close()
            
            return self._process_raw_data(raw_data)

    def _process_raw_data(self, raw_data: List[Dict]) -> List[Dict]:
        processed = []
        seen_urls = set()
        
        for item in raw_data:
            url = f"https://www.youtube.com{item['href']}" if not item['href'].startswith('http') else item['href']
            if url in seen_urls: continue
            seen_urls.add(url)

            views_int = DataConverter.parse_view_count(item['views'])
            days_int = DataConverter.parse_age_to_days(item['date'])
            
            processed.append({
                'Title': item['title'],
                'URL': url,
                'View Count': item['views'],
                'Date/Year': item['date'],
                'Views Per Day (Avg)': round(views_int / days_int)
            })
        return processed