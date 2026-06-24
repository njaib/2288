import telebot
import feedparser
import time
import requests
from deep_translator import GoogleTranslator
import os
import re
import pycountry
import flag

# --- Configuration ---
BOT_TOKEN = "8805157616:AAHhD_bRckdy3CH_KkmGX8lXbLVg08OE83M"
CHANNEL_ID = "@AFGaziz"

# Expanded RSS feeds from major international networks
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "http://feeds.reuters.com/reuters/topNews",
    "http://feeds.foxnews.com/foxnews/latest",
    "https://www.france24.com/en/rss",
    "https://rss.dw.com/xml/rss-en-all",
    "http://rss.cnn.com/rss/edition_world.rss",
    "https://www.theguardian.com/world/rss",
    "https://www.rt.com/rss/news/"
]

bot = telebot.TeleBot(BOT_TOKEN)
translator = GoogleTranslator(source='auto', target='fa')

# To avoid duplicates
sent_news = set()

def get_country_flag(text):
    """Detect country in text and return its flag emoji."""
    for country in pycountry.countries:
        if country.name in text:
            return flag.flag(country.alpha_2)
    return "🌍" # Default globe if no country detected

def get_image_url(entry):
    """Extract image URL from RSS entry."""
    if 'media_content' in entry:
        return entry.media_content[0]['url']
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''):
                return link.get('href')
    if 'description' in entry:
        img_match = re.search(r'<img src="([^"]+)"', entry.description)
        if img_match:
            return img_match.group(1)
    return None

def process_news():
    for url in RSS_FEEDS:
        print(f"Checking feed: {url}")
        feed = feedparser.parse(url)
        for entry in feed.entries:
            news_id = entry.get('id', entry.link)
            if news_id in sent_news:
                continue
            
            try:
                title = entry.title
                summary = entry.get('summary', '')
                # Remove HTML tags
                summary = re.sub('<[^<]+?>', '', summary)
                
                # Detect flag
                country_flag = get_country_flag(title + " " + summary)
                
                # Translate with more length
                translated_title = translator.translate(title)
                # Translate more of the summary (up to 1000 chars)
                translated_summary = translator.translate(summary[:1000])
                
                img_url = get_image_url(entry)
                
                # Format the message
                caption = (
                    f"{country_flag} <b>{translated_title}</b>\n\n"
                    f"{translated_summary}\n\n"
                    f"🔗 <a href='{entry.link}'>مشاهده منبع خبر</a>\n"
                    f"🆔 {CHANNEL_ID}"
                )
                
                if img_url:
                    bot.send_photo(CHANNEL_ID, img_url, caption=caption, parse_mode='HTML')
                else:
                    bot.send_message(CHANNEL_ID, caption, parse_mode='HTML')
                
                print(f"Sent: {title}")
                sent_news.add(news_id)
                
                # User requested: 1 news per minute, change every 20s (interpreted as sending one, waiting 60s)
                # But also mentioned "every 20s change it every 1 minute". 
                # I will stick to 1 news per minute (60s) to keep it steady as requested.
                time.sleep(60)
                
            except Exception as e:
                print(f"Error processing entry: {e}")
                continue

if __name__ == "__main__":
    print("Enhanced News Bot started...")
    # Clean start: optionally clear sent_news if you want to resend latest
    while True:
        try:
            process_news()
        except Exception as e:
            print(f"Global error: {e}")print("Cycle complete. Waiting for new updates...")
        time.sleep(30)