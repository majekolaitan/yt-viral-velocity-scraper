import logging
import sys
from scraper import YouTubeScraper
import csv

# Configure logging to look clean in the terminal
logging.basicConfig(level=logging.INFO, format='%(message)s')

def save_to_csv(data, filename):
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
    
    # 1. Get Channel URL
    channel_url = input("Enter YouTube Channel Videos URL (e.g., https://www.youtube.com/@Name/videos): ").strip()
    if not channel_url or "youtube.com" not in channel_url:
        print("❌ Error: Please enter a valid YouTube URL.")
        sys.exit(1)

    # 2. Get Max Scrolls
    scroll_input = input("Enter max scrolls (higher = more videos, default 10): ").strip()
    try:
        max_scrolls = int(scroll_input) if scroll_input else 10
    except ValueError:
        print("⚠️ Invalid number for scrolls. Using default: 10")
        max_scrolls = 10

    # 3. Choose Mode
    mode_input = input("Run in background? (y/n, default y): ").strip().lower()
    is_headless = False if mode_input == 'n' else True

    # Initialize and Run Scraper
    scraper = YouTubeScraper(headless=is_headless)
    
    try:
        logging.info(f"\n🚀 Starting scraper for: {channel_url}")
        videos = scraper.scrape_channel(channel_url, max_scrolls=max_scrolls)
        
        if videos:
            logging.info("📊 Calculating viral metrics and sorting by velocity...")
            videos.sort(key=lambda x: x['Views Per Day (Avg)'], reverse=True)
            
            output_file = "youtube_results.csv"
            save_to_csv(videos, output_file)
        else:
            logging.error("❌ No videos found. Ensure the URL is correct and points to the /videos tab.")

    except KeyboardInterrupt:
        print("\nStopping process...")
    except Exception as e:
        logging.error(f"\n❌ Application error: {e}")

if __name__ == "__main__":
    main()