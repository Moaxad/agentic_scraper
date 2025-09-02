# Agentic AI Scraper (Still Experimenting)

This project is an **agentic AI assistant** for scraping data automatically using ScrapeStorm.
It can:

- Check existing ScrapeStorm tasks for your request.
- If no suitable task exists, ask an AI (deepseek + Groq) to suggest URLs and fields.
- Automatically create new tasks via the ScrapeStorm API.
- It automates handling scraping, pagination, deduplication, and saving data to MySQL (or any preferred RDBMS).



---

## Setup

```bash
git clone https://github.com/<your-username>/agentic_scraper.git
cd agentic_scraper

pip install -r requirements.txt

Copy .env.example to .env and fill in your API keys:

cp .env.example .env


