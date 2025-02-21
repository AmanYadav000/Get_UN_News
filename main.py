import feedparser
import json
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
import requests
import uvicorn

app = FastAPI()
bills_router = APIRouter()

RSS_URL = "https://news.un.org/feed/subscribe/en/news/all/rss.xml"

@bills_router.get("/get_un_news")
async def get_un_news():
    """Fetch UN news articles from RSS feed."""
    try:
        feed = feedparser.parse(RSS_URL)
        news_entries = [{"Title": entry.title, "Link": entry.link, "Published": entry.published, "Summary": entry.summary} for entry in feed.entries]
        return JSONResponse(content={"news_entries": news_entries})
    except Exception as e:
        return JSONResponse(content={"error": f"Failed to fetch UN news: {str(e)}"}, status_code=500)


def extract_content(url):
    """Extracts article summary from a webpage."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            body_content_div = soup.find('div', class_='body_content')
            if body_content_div:
                content = body_content_div.get_text(strip=True)
                word_limit_summary = " ".join(content.split()[:50]) + "..."
                return word_limit_summary
            return "Content not found."
        return f"Failed to retrieve page. Status code: {response.status_code}"
    except Exception as e:
        return f"Error fetching content: {str(e)}"


@bills_router.get("/get_bills")
async def get_bills():
    """Fetches latest bills from PRS India website."""
    try:
        response = requests.get("https://prsindia.org/billtrack", timeout=10)
        if response.status_code != 200:
            return JSONResponse(content={"error": f"Failed to fetch bills. Status code: {response.status_code}"}, status_code=500)

        soup = BeautifulSoup(response.text, 'html.parser')
        bill_rows = soup.find_all('div', class_='views-row')
        bills = []

        for index, row in enumerate(bill_rows[:50], start=1):
            title_div = row.find('div', class_='views-field-title-field')
            status_div = row.find('div', class_='views-field-field-bill-status')

            if not title_div:
                continue

            title = title_div.find('h3').get_text(strip=True) if title_div.find('h3') else "N/A"
            link = title_div.find('a')['href'] if title_div.find('a') else None
            full_link = f"https://prsindia.org{link}" if link else "N/A"
            status = status_div.get_text(strip=True) if status_div else "N/A"
            content = extract_content(full_link) if full_link != "N/A" else "N/A"

            bills.append({
                "index": index,
                "title": title,
                "link": full_link,
                "status": status,
                "summary": content
            })

        return JSONResponse(content={"bills": bills})

    except Exception as e:
        return JSONResponse(content={"error": f"An error occurred: {str(e)}"}, status_code=500)


app.include_router(bills_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
