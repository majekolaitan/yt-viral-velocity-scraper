import csv
import logging
import sys
import re
from scraper import YouTubeScraper

# Configure logging for clean terminal output
logging.basicConfig(level=logging.INFO, format='%(message)s')

def get_channel_name_from_url(url: str) -> str:
    """Extracts the channel name from a YouTube URL to use in the filename."""
    # Regex to find the @username part of the URL
    match = re.search(r'@([^/]+)', url)
    if match:
        return match.group(1)
    # Fallback for older /channel/ or /user/ URLs or if regex fails
    return "youtube_channel"

def save_to_csv(data: list, filename: str):
    """Saves the given list of dictionaries to a CSV file."""
    if not data:
        logging.warning("⚠️ No data extracted to save.")
        return
        
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    logging.info(f"\n✅ Success! Saved {len(data)} videos to '{filename}'")

def main():
    print("--- YouTube Viral Video Scraper ---")
    
    channel_url = input("Enter YouTube Channel Videos URL (e.g., https://www.youtube.com/@Name/videos): ").strip()
    if not channel_url or "youtube.com" not in channel_url:
        print("❌ Error: Please enter a valid YouTube URL.")
        sys.exit(1)

    scroll_input = input("Enter max scrolls (higher = more videos, default 10): ").strip()
    try:
        max_scrolls = int(scroll_input) if scroll_input else 10
    except ValueError:
        logging.warning("⚠️ Invalid number for scrolls. Using default: 10")
        max_scrolls = 10

    mode_input = input("Run in background? (y/n, default y): ").strip().lower()
    is_headless = mode_input != 'n'

    # --- NEW: Dynamic Filename Generation ---
    channel_name = get_channel_name_from_url(channel_url)
    output_file = f"{channel_name}_viral_videos.csv"
    
    scraper = YouTubeScraper(headless=is_headless)
    
    try:
        logging.info(f"\n🚀 Starting scraper for: {channel_url}")
        videos = scraper.scrape_channel(channel_url, max_scrolls=max_scrolls)
        
        if videos:
            logging.info("📊 Calculating viral metrics and sorting by velocity...")
            videos.sort(key=lambda x: x['Views Per Day (Avg)'], reverse=True)
            save_to_csv(videos, output_file)
        else:
            logging.error("❌ No videos found. Ensure the URL is correct and points to the /videos tab.")

    except KeyboardInterrupt:
        print("\nStopping process...")
    except Exception as e:
        logging.error(f"\n❌ Application error: {e}")

if __name__ == "__main__":
    main()