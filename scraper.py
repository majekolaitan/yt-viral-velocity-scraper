import logging
from typing import List, Dict
from playwright.sync_api import sync_playwright, Page
from utils import DataConverter

class YouTubeScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    def _handle_consent(self, page: Page):
        try:
            accept_btn = page.locator('button[aria-label="Accept all"]')
            if accept_btn.count() > 0:
                accept_btn.first.click(force=True)
                page.wait_for_timeout(1000)
        except Exception: pass

    def _click_popular_tab(self, page: Page):
        popular_tab = page.get_by_role("tab", name="Popular").first
        popular_tab.wait_for(state="visible", timeout=10000)
        popular_tab.click(force=True)
        page.get_by_role("tab", name="Popular", selected=True).wait_for(timeout=5000)
        page.wait_for_timeout(2000)

    def _scroll_to_load(self, page: Page, max_scrolls: int):
        selector = 'ytd-rich-item-renderer a#video-title-link'
        last_count = 0
        retries = 0
        
        for i in range(max_scrolls):
            page.keyboard.press("End")
            page.wait_for_timeout(2500)
            
            current_count = page.locator(selector).count()
            logging.info(f"  ∟ Scroll {i+1}/{max_scrolls} - Videos loaded: {current_count}")
            
            if current_count == last_count:
                retries += 1
                if retries >= 3:
                    logging.info("End of list reached after 3 consecutive scrolls with no new videos.")
                    break
            else:
                retries = 0
            
            last_count = current_count
            
    def scrape_channel(self, url: str, max_scrolls: int) -> List[Dict]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            
            self._handle_consent(page)
            self._click_popular_tab(page)
            self._scroll_to_load(page, max_scrolls)
            
            # --- JAVASCRIPT LOGIC UPDATED HERE ---
            raw_data = page.evaluate("""
                () => [...document.querySelectorAll('ytd-rich-item-renderer')].map(vid => {
                    const titleElem = vid.querySelector('a#video-title-link');
                    if (!titleElem) return null; // Skip if it's not a real video card

                    const meta = vid.querySelectorAll('#metadata-line > span.inline-metadata-item');
                    
                    return {
                        title: titleElem.getAttribute('title'),
                        href: titleElem.getAttribute('href'),
                        // Check if meta elements exist before accessing them
                        views: meta.length > 0 ? meta[0].innerText : '0 views',
                        date: meta.length > 1 ? meta[1].innerText : 'Unknown' // FIX: Return 'Unknown' instead of a fake date
                    };
                }).filter(v => v !== null && v.title) // Filter out nulls and empty titles
            """)
            # --- END OF JAVASCRIPT UPDATE ---

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
            
            # If the date is 'Unknown', parse_age_to_days will default to 1,
            # but we can also set the velocity to 0 to push it to the bottom.
            days_int = DataConverter.parse_age_to_days(item['date'])
            views_per_day = 0
            if days_int > 0 and item['date'] != 'Unknown':
                views_per_day = round(views_int / days_int)

            processed.append({
                'Title': item['title'],
                'URL': url,
                'View Count': item['views'],
                'Date/Year': item['date'],
                'Views (int)': views_int,
                'Age (days)': days_int if item['date'] != 'Unknown' else 'N/A', # Show N/A for unknown dates
                'Views Per Day (Avg)': views_per_day
            })
        return processed