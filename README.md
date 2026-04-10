# 🚀 YouTube Viral Velocity Scraper

A high-performance, modular web scraper built with **Python** and **Playwright**. Unlike standard scrapers that just sort by total views, this tool calculates the **"Viral Velocity"** (Views Per Day) of videos on any YouTube channel.

It automatically sorts your results so that a video with 100,000 views in 2 days ranks higher than a video with 500,000 views in 5 years.

---

## 🛠 Features

- **Viral Velocity Metric:** Calculates `Views / Days Since Published` to identify true rising stars.
- **Dynamic Content Loading:** Uses Playwright to simulate human scrolling, triggering YouTube's infinite load API.
- **Robust Parsing:** Uses Regex-based parsing to handle different view formats (K, M, B) and relative time strings ("a month ago", "2 days ago").
- **Clean Architecture:** Modular design separating data utilities, browser automation, and the user interface.

---

## 📋 Prerequisites

Ensure you have [Python 3.8+](https://www.python.org/) installed, then set up the environment:

1. **Install dependencies:**
   ```bash
   pip install playwright
   ```
2. **Install browser binaries:**
   ```bash
   playwright install chromium
   ```

---

## 🚀 How to Run

1. **Clone or copy the files** (`main.py`, `scraper.py`, `utils.py`) into your local directory.
2. **Execute the application:**
   ```bash
   python main.py
   ```
3. **Follow the prompts:**
   - **URL:** Paste the channel's `/videos` URL (e.g., `https://www.youtube.com/@ChannelName/videos`).
   - **Max Scrolls:** Enter how many times the scraper should hit "End" to load more content.
   - **Headless Mode:** Choose `y` to run silently in the background, or `n` to watch the browser process the data.

---

## 📁 File Structure

- `main.py`: The entry point. Handles user interaction and saves the final CSV.
- `scraper.py`: Contains the `YouTubeScraper` class, which handles the Playwright browser automation and DOM extraction.
- `utils.py`: Contains the `DataConverter` class, housing the logic for parsing views and dates.

---

## ⚖️ Why "Velocity" over "Popular"?

YouTube's native "Popular" button simply sorts by the highest total view count. This biases your data toward old, legacy content.

- **Example:**
  - _Old Video:_ 1,000,000 views / 1,095 days = **912 views/day**
  - _New Video:_ 200,000 views / 2 days = **100,000 views/day**
- By using our **Views Per Day** metric, the new video is surfaced to the top of your `youtube_results.csv` automatically.

---

## ⚠️ Disclaimer

This tool is for educational purposes and personal data analysis. Please respect [YouTube's Terms of Service](https://www.youtube.com/t/terms) and `robots.txt`. Do not use this tool to perform high-frequency requests that could impact the service's stability.
