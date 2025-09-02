# Agentic AI Scraper (Experimental)

This project is an **agentic AI assistant** for scraping data automatically using ScrapeStorm.
It can:

- Check existing ScrapeStorm tasks for your request.
- If no suitable task exists, ask an AI (deepseek + Groq) to suggest URLs and fields.
- Automatically create new tasks via the ScrapeStorm API.
- Let ScrapeStorm handle scraping, pagination, deduplication, and saving data to MySQL.


## Project Structure

agentic_scraper/
│── .env # local secrets (not committed)
│── .env.example # template for environment variables
│── main.py # main entry point
│── config.py # configuration variables
│── scrapestorm_client.py # handles ScrapeStorm API calls
│── ai_agent.py # handles AI suggestions
│── utils.py # helper functions
│── requirements.txt # Python dependencies
│── README.md # this file


---

## Setup

1. Clone the repo:

```bash
git clone https://github.com/<your-username>/agentic_scraper.git
cd agentic_scraper

pip install -r requirements.txt
