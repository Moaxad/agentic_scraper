# Agentic AI Scraper (Still Experimenting)

This project is an **agentic AI assistant** for scraping data automatically using ScrapeStorm.
It can:

- Check existing ScrapeStorm tasks for your request.
- If no suitable task exists, ask an AI (DeepSeek + Groq) to suggest URLs and fields.
- Automatically create new tasks via the ScrapeStorm API.
- Handles scraping, pagination, deduplication, and saving data to MySQL (or any preferred RDBMS).
- The final goal: take a user prompt ("What data do you want?") and handle the full pipeline from source determination to scraping the data, and pushing data to the preferred data sink.


---

## Setup

```bash
git clone https://github.com/<your-username>/agentic_scraper.git
cd agentic_scraper

pip install -r requirements.txt

Copy .env.example to .env and fill in your API keys:

cp .env.example .env



