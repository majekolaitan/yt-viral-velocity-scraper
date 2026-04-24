import logging
import re
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
        try:
            logging.info("  ∟ Waiting for page to hydrate...")
            # Wait for at least one video to load so we know the UI is fully ready
            page.wait_for_selector('ytd-rich-item-renderer', state='visible', timeout=15000)
            
            logging.info("  ∟ Switching to 'Popular' tab...")
            
            # Scroll to the absolute top to ensure tabs aren't hidden under the sticky search header
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)
            
            # The :visible flag prevents grabbing the hidden mobile sidebar tab
            popular_tab = page.locator('button[aria-label="Popular"]:visible, yt-chip-cloud-chip-renderer:has-text("Popular"):visible').first
            popular_tab.wait_for(state="visible", timeout=5000)
            
            # USE JAVASCRIPT CLICK: Bypasses Playwright's strict viewport and overlap checks
            popular_tab.evaluate("node => node.click()")
            
            # Wait 3 seconds for the grid to refresh with the new sorted videos
            page.wait_for_timeout(3000)
            
        except Exception as e:
            logging.warning(f"  ⚠️ Could not click 'Popular' tab (using default sort). Error: {e}")

    def _scroll_to_load(self, page: Page, max_scrolls: int):
        selector = 'ytd-rich-item-renderer a#video-title-link'
        last_count = 0
        retries = 0
        
        for i in range(max_scrolls):
            # --- JAVASCRIPT SCROLL UPDATE ---
            # Bypasses Playwright's need to click the <body> to focus the keyboard
            page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
            page.wait_for_timeout(2500)
            
            current_count = page.locator(selector).count()
            logging.info(f"  ∟ Scroll {i+1}/{max_scrolls} - Videos loaded: {current_count}")
            
            if current_count == last_count:
                retries += 1
                if retries >= 3:
                    logging.info("  ∟ End of list reached after 3 consecutive scrolls with no new videos.")
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
            
            raw_data = page.evaluate("""
                () => [...document.querySelectorAll('ytd-rich-item-renderer')].map(vid => {
                    const titleElem = vid.querySelector('a#video-title-link');
                    if (!titleElem) return null;

                    const meta = vid.querySelectorAll('#metadata-line > span.inline-metadata-item');
                    
                    const durationElem = vid.querySelector('ytd-thumbnail-overlay-time-status-renderer .ytBadgeShapeText, ytd-thumbnail-overlay-time-status-renderer #text');
                    const duration = durationElem ? durationElem.innerText.trim() : 'Unknown';
                    
                    return {
                        title: titleElem.getAttribute('title'),
                        href: titleElem.getAttribute('href'),
                        duration: duration,
                        views: meta.length > 0 ? meta[0].innerText : '0 views',
                        date: meta.length > 1 ? meta[1].innerText : 'Unknown'
                    };
                }).filter(v => v !== null && v.title)
            """)

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

            # --- NEW DURATION LOGIC ---
            duration_seconds = DataConverter.parse_duration_to_seconds(item['duration'])
            duration_formatted = DataConverter.format_seconds_to_hhmmss(duration_seconds)

            views_per_day = 0
            if days_int > 0 and item['date'] != 'Unknown':
                views_per_day = round(views_int / days_int)

            processed.append({
                'Title': item['title'],
                'URL': url,
                'Duration (HH:MM:SS)': duration_formatted,
                'Duration (seconds)': duration_seconds,
                'Duration': item['duration'],
                'View Count': item['views'],
                'Date/Year': item['date'],
                'Views (int)': views_int,
                'Age (days)': days_int if item['date'] != 'Unknown' else 'N/A', 
                'Views Per Day (Avg)': views_per_day
            })
        return processed