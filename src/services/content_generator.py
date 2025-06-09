import google.generativeai as genai
import os
from typing import Dict, List
import requests
import logging
import json
from pathlib import Path
from src.database.mongodb import MongoDB
import cloudinary
import cloudinary.uploader
from datetime import datetime
import time  # Added missing import

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.db = MongoDB()
        # Initialize Cloudinary - moved inside the constructor
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET")
        )
        logger.info("ContentGenerator initialized with MongoDB and Cloudinary")
        self.cache_ttl = 3600  # 1 hour cache
        self.cache = {}
        
    async def get_cached_posts(self):
        cache_key = 'all_posts'
        if cache_key in self.cache:
            if time.time() - self.cache[cache_key]['timestamp'] < self.cache_ttl:
                return self.cache[cache_key]['data']
        
        posts = await self.db.get_all_posts()
        self.cache[cache_key] = {
            'data': posts,
            'timestamp': time.time()
        }
        return posts

    async def update_cached_posts(self, posts: List[Dict]):
        for post in posts:
            await self.db.save_post(post)
        # Clear the cache after saving new posts
        self.cache = {}  # Clear entire cache
        logger.info(f"Saved {len(posts)} posts to MongoDB and cleared cache")

    async def get_posts_by_category(self, category: str):
        try:
            logger.info(f"Fetching posts for category: {category}")
            posts = await self.db.get_posts_by_category(category)
            if not posts:
                logger.warning(f"No posts found for category: {category}")
            return posts
        except Exception as e:
            logger.error(f"Error getting posts by category: {e}")
            return []

    async def get_post_by_id(self, post_id: str):
        return await self.db.get_post_by_id(post_id)

    # Update the generate_blog_post method
    async def generate_blog_post(self, article: Dict) -> Dict:
        start_time = time.time()  # Add this line at the start of the method
        try:
            # Single source of truth for niche mapping with slugs
            niche_context = {
                'ai-news': {
                    'name': 'AI News',
                    'context': 'Focus on artificial intelligence, machine learning, and AI innovations.',
                    'slug': 'ai-news'
                },
                'startup-ecosystem': {
                    'name': 'Startup Ecosystem',
                    'context': 'Focus on startup companies, entrepreneurship, and business innovation.',
                    'slug': 'startup-ecosystem'
                },
                'productivity-tools': {
                    'name': 'Productivity Tools',
                    'context': 'Focus on tools and techniques for improving efficiency and workflow.',
                    'slug': 'productivity-tools'
                },
                'dev-trends': {
                    'name': 'Dev Trends',
                    'context': 'Focus on software development trends and best practices.',
                    'slug': 'dev-trends'
                },
                'tech-ethics': {
                    'name': 'Tech Ethics',
                    'context': 'Focus on ethical considerations in technology.',
                    'slug': 'tech-ethics'
                },
                'meditation-mindfulness': {
                    'name': 'Meditation & Mindfulness',
                    'context': 'Focus on mindfulness practices and mental wellness.',
                    'slug': 'meditation-mindfulness'
                },
                'vedic-philosophy': {
                    'name': 'Vedic Philosophy',
                    'context': 'Focus on ancient wisdom and modern applications.',
                    'slug': 'vedic-philosophy'
                },
                'lucid-dreaming': {
                    'name': 'Lucid Dreaming',
                    'context': 'Focus on dream consciousness and techniques.',
                    'slug': 'lucid-dreaming'
                },
                'habit-science': {
                    'name': 'Habit Science',
                    'context': 'Focus on habit formation and behavior change.',
                    'slug': 'habit-science'
                }
            }
            
            niche = article.get('niche', 'ai-news')
            niche_info = niche_context.get(niche, niche_context['ai-news'])
            category_name = niche_info['name']
            context = niche_info['context']
            
            # Update prompt with exact category name
            prompt = f"""
            Create an engaging blog post based on this news article:
            Title: {article['title']}
            Content: {article['description']}
            Category: {category_name}
            Context: {context}
            
            Format your response exactly as follows:
            1. Title: [Your engaging title]
            2. Meta: [Your meta description in 160 characters]
            3. Content: [Your article content in markdown]
            4. Tags: [Must include exactly "{category_name}" as first tag, then 4 more relevant hashtags]
            """
            
            logger.info("Sending request to Gemini AI...")
            response = self.model.generate_content(prompt)
            content = response.text
            logger.info("Content received from Gemini AI")
    
            # Extract title
            title = content.split("1. Title:")[1].split("2. Meta:")[0].strip()
            
            # Extract meta description
            meta = content.split("2. Meta:")[1].split("3. Content:")[0].strip()
            
            # Extract content
            article_content = content.split("3. Content:")[1].split("4. Tags:")[0].strip()
            
            # Extract hashtags
            # Update hashtag handling
            tags_section = content.split("4. Tags:")[1].strip()
            raw_tags = [tag.strip() for tag in tags_section.split("#") if tag.strip()]
            
            # Ensure first tag is always the category name
            hashtags = [category_name]  # First tag is always the category name
            additional_tags = [tag for tag in raw_tags if tag.lower() != category_name.lower()][:4]
            hashtags.extend(additional_tags)
            
            post = {
                "title": title,
                "meta_description": meta,
                "content": article_content,
                "hashtags": hashtags,
                "niche": niche_info['slug'],  # Store normalized niche
                "category": niche_info['name']  # Store display name
            }
            
            # Generate and add image
            logger.info("Starting image generation...")
            image_url = await self.generate_blog_image(post)
            if image_url:
                post["image_url"] = image_url
                logger.info("Image generation and upload completed")
            else:
                logger.warning("Image generation failed, using placeholder")
            
            end_time = time.time()
            logger.info(f"Blog post generation completed in {end_time - start_time:.2f} seconds")
            return post
                
        except Exception as e:
            logger.error(f"Error generating blog post: {e}")
            return {
                "title": article['title'],
                "meta_description": article['description'][:160],
                "content": f"# {article['title']}\n\n{article['description']}",
                "hashtags": [niche, "tech", "AI", "blog", "automation"]  # Ensure niche is first tag in error case too
            }

    # Fixed the generate_blog_image method
    async def generate_blog_image(self, post: Dict) -> str:
        start_time = time.time()
        logger.info(f"Starting image generation for post: {post['title'][:50]}...")
        
        try:
            # Generate image from AI Art API
            logger.info("Sending request to AI Art API...")
            prompt = f"Create an image for blog post: {post['title']}. Context: {post['meta_description'][:100]}"
            payload = {
                "video_description": prompt,
                "test_mode": False
            }
            response = requests.post(
                url="https://aiart-zroo.onrender.com/api/generate",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                data = response.json()
                image_url = data.get('image_url') or data.get('url')
                
                if image_url:
                    logger.info("Image generated successfully, starting Cloudinary upload...")
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_title = ''.join(c for c in post['title'][:30] if c.isalnum() or c.isspace())
                    public_id = f"blog/{safe_title}_{timestamp}"
                    
                    upload_result = cloudinary.uploader.upload(
                        image_url,
                        public_id=public_id,
                        folder="blog_images",
                        overwrite=True
                    )
                    
                    end_time = time.time()
                    logger.info(f"Image uploaded to Cloudinary in {end_time - start_time:.2f} seconds: {upload_result['secure_url']}")
                    return upload_result['secure_url']
            
            logger.warning("AI Art API failed, using placeholder image")
            return self._generate_placeholder(post)
            
        except Exception as e:
            logger.error(f"Error in image generation: {e}")
            return self._generate_placeholder(post)

    def _generate_placeholder(self, post: Dict) -> str:
        category = post.get('niche', 'general').lower()
        color_map = {
            'tech': 'e2e8f0/1a237e',
            'ai': 'e0f2fe/0369a1',
            'startup': 'f0fdf4/166534',
            'meditation': 'fdf2f8/831843',
            'general': 'f3f4f6/1f2937'
        }
        colors = color_map.get(category, color_map['general'])
        safe_title = ''.join(c for c in post['title'][:30] if c.isalnum() or c.isspace())
        return f"https://placehold.co/800x400/{colors}?text={safe_title}..."

    async def search_posts(self, query: str) -> List[Dict]:
        try:
            # Search in existing posts only using MongoDB text search
            posts = await self.db.search_posts(query)
            if not posts:
                logger.info(f"No posts found for query: {query}")
                return []
                
            logger.info(f"Found {len(posts)} posts matching query: {query}")
            return posts
        except Exception as e:
            logger.error(f"Error searching posts: {e}")
            return []

    # Add this method to ContentGenerator class
    async def get_posts_by_hashtag(self, tag: str):
        logger.info(f"ContentGenerator: Getting posts for tag {tag}")
        return await self.db.get_posts_by_hashtag(tag)

    async def clear_all_caches(self):
        """Clear all caches after post deletion"""
        self.cache = {}  # Clear the local cache
        logger.info("All caches cleared")
            