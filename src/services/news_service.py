import os
import requests
from typing import List, Dict
import logging
import time  # Add this import

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        if not self.api_key:
            logger.error("NEWS_API_KEY not found in environment variables")
        self.base_url = "https://newsapi.org/v2/everything"
        logger.info("NewsService initialized")

    async def fetch_tech_news(self) -> List[Dict]:
        logger.info("Fetching tech news")
        return await self.fetch_news_by_niche("tech")

    # Update the fetch_news_by_niche method
    async def fetch_news_by_niche(self, niche: str) -> List[Dict]:
        start_time = time.time()
        logger.info(f"Fetching news for niche: {niche}")
        
        try:
            if not self.api_key:
                raise ValueError("NEWS_API_KEY not configured")
                
            niche_queries = {
                'ai-news': '(artificial intelligence breakthrough OR AI research papers OR machine learning industry)',
                'startup-ecosystem': '(startup funding OR company launch OR innovative business)',
                'productivity-tools': '(productivity apps OR workflow tools OR time management)',
                'dev-trends': '(programming trends OR framework updates OR developer tools)',
                'tech-ethics': '(AI ethics OR technology policy OR digital rights)',
                'meditation-mindfulness': '(meditation techniques OR mindfulness practice OR mental wellness)',
                'vedic-philosophy': '(upanishads OR bhagavad gita OR vedic wisdom)',
                'lucid-dreaming': '(lucid dreams OR dream research OR consciousness exploration)',
                'habit-science': '(habit formation OR behavioral psychology OR dopamine)'
            }
            
            query = niche_queries.get(niche, niche_queries["ai-news"])  # Changed default
            logger.info(f"Using query: {query}")
            
            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 10,
                "apiKey": self.api_key
            }
            
            logger.info("Sending request to News API...")
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # This will raise an exception for bad status codes
            
            data = response.json()
            if "articles" not in data:
                logger.error(f"Unexpected API response: {data}")
                return []
                
            articles = data["articles"]
            end_time = time.time()
            logger.info(f"Successfully fetched {len(articles)} articles in {end_time - start_time:.2f} seconds")
            return articles
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching news: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            return []