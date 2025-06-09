from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.services.news_service import NewsService
from src.services.content_generator import ContentGenerator
import markdown2
from fastapi import Form
from fastapi.responses import RedirectResponse
import asyncio
import sys
import logging
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from starlette import status
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from flask import Flask, render_template, request
from datetime import datetime
import os  # Add this import
from fastapi.responses import FileResponse  # Add this import

load_dotenv()

YOUR_EMAIL = os.getenv("YOUR_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

app = FastAPI(title="AI Blog Generator")
news_service = NewsService()
content_generator = ContentGenerator()
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


from datetime import datetime

# Add this after creating the FastAPI app
# Change this line
# Remove this line:
# app.mount("/static", StaticFiles(directory="../static"), name="static")

# Add this instead:

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.middleware("http")
async def add_global_context(request: Request, call_next):
    response = await call_next(request)
    return response

# Add this to your FastAPI app setup
templates.env.globals["current_year"] = lambda: datetime.now().year

@app.get("/")
async def home(request: Request):
    try:
        posts = await content_generator.get_cached_posts()
        
        featured_posts = []
        if posts:
            # Add metadata for trending and popular posts
            for post in posts:
                if post.get('views', 0) > 100:
                    post['is_popular'] = True
                    post['badge'] = 'Popular'
                elif post.get('created_at') and (datetime.now() - post['created_at']).days < 7:
                    post['is_trending'] = True
                    post['badge'] = 'Trending'

            # Sort posts by views and date
            sorted_posts = sorted(
                posts,
                key=lambda x: (x.get('views', 0), x.get('created_at', '')),
                reverse=True
            )
            featured_posts = sorted_posts[:2] if sorted_posts else []
            posts = [p for p in posts if p not in featured_posts]

        return templates.TemplateResponse("home.html", {  # Changed from home.html to index.html
            "request": request, 
            "posts": posts or [],
            "featured_posts": featured_posts,
            "show_empty_state": not posts
        })
        
    except Exception as e:
        logger.error(f"Error in home route: {e}")
        return templates.TemplateResponse("home.html", {  # Changed from home.html to index.html
            "request": request, 
            "posts": [],
            "featured_posts": [],
            "show_empty_state": True
        })

# Add this new route for home.html content
@app.get("/home")
async def home_content(request: Request):
    try:
        posts = await content_generator.get_cached_posts()
        print("Home page accessed")
        # Same post processing as original home route
        featured_posts = []
        if posts:
            for post in posts:
                if post.get('views', 0) > 100:
                    post['is_popular'] = True
                    post['badge'] = 'Popular'
                elif post.get('created_at') and (datetime.now() - post['created_at']).days < 7:
                    post['is_trending'] = True
                    post['badge'] = 'Trending'

            sorted_posts = sorted(
                posts,
                key=lambda x: (x.get('views', 0), x.get('created_at', '')),
                reverse=True
            )
            featured_posts = sorted_posts[:2]
            posts = [p for p in posts if p not in featured_posts]

        return templates.TemplateResponse("home.html", {
            "request": request,
            "posts": posts,
            "featured_posts": featured_posts,
            "show_empty_state": not posts
        })
        
    except Exception as e:
        logger.error(f"Home content error: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request,
            "posts": [],
            "featured_posts": [],
            "show_empty_state": True
        })


@app.get("/about")
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})
    
@app.get("/terms")
async def about_page(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/contact")
async def about_page(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/index")
async def about_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})    
@app.get("/favicon.ico")
async def favicon():
    return FileResponse('static/favicon.ico')
    
@app.get("/index")
async def index_redirect(request: Request):
    return RedirectResponse(url="/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@app.post("/contacts")
async def contacts(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    subject = f"[Echo Mind] New Contact Form Submission from {name}"
    body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

    msg = MIMEMultipart()
    msg["From"] = YOUR_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(YOUR_EMAIL, APP_PASSWORD)
        server.sendmail(YOUR_EMAIL, TO_EMAIL, msg.as_string())
        server.quit()
        return {"success": True, "message": "✅ Email sent successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}



# Update the category route to only accept valid categories
@app.get("/{category}")
async def category_page(request: Request, category: str):
    # Update valid categories to match exact hashtags
    valid_categories = {
        'ai-news': 'AI News',
        'startup-ecosystem': 'Startup Ecosystem',
        'productivity-tools': 'Productivity Tools',
        'dev-trends': 'Dev Trends',
        'tech-ethics': 'Tech Ethics',
        'meditation-mindfulness': 'Meditation & Mindfulness',
        'vedic-philosophy': 'Vedic Philosophy',
        'lucid-dreaming': 'Lucid Dreaming',
        'habit-science': 'Habit Science'
    }
    
    if category not in valid_categories:
        return RedirectResponse(url="/")
    
    try:
        # Use the exact category name for searching
        tag_filter = valid_categories[category]
        logger.info(f"Searching for posts in category: {tag_filter}")
        posts = await content_generator.get_posts_by_hashtag(tag_filter)
        
        # Get featured posts for the category
        featured_posts = []
        if posts:
            sorted_posts = sorted(
                posts,
                key=lambda x: (x.get('views', 0), x.get('created_at', '')),
                reverse=True
            )
            featured_posts = sorted_posts[:2]
            posts = [p for p in posts if p not in featured_posts]
        
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "posts": posts,
            "featured_posts": featured_posts,  # Add this
            "show_empty_state": not posts,
            "category": category,
            "category_title": tag_filter
        })
    except Exception as e:
        logger.error(f"Category error: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "posts": [],
            "featured_posts": [],  # Add this
            "show_empty_state": True,
            "category": category,
            "category_title": valid_categories.get(category, '')
        })




@app.get("/post/{post_id}")
async def post_detail(request: Request, post_id: str):
    try:
        # Get specific post
        post = await content_generator.get_post_by_id(post_id)
        
        if not post:
            return RedirectResponse(url="/")
        
        # Get related posts based on category
        related_posts = []
        if 'category' in post:
            # Get posts with same category, excluding current post
            related_posts = await content_generator.get_posts_by_category(post['category'])
            # Filter out the current post
            related_posts = [p for p in related_posts if str(p['_id']) != post_id][:3]
        
        # Convert content to HTML
        post['content'] = markdown2.markdown(post['content'])
        
        return templates.TemplateResponse("post.html", {
            "request": request,
            "post": post,
            "related_posts": related_posts
        })
    except Exception as e:
        logger.error(f"Error in post_detail: {e}")
        return RedirectResponse(url="/")

# Update the generate_content route
@app.post("/")
async def generate_content(request: Request, niche: str = Form(...)):
    try:
        logger.info(f"Starting content generation for niche: {niche}")
        start_time = time.time()
        
        # Fetch news articles based on selected niche
        logger.info("Fetching news articles...")
        articles = await news_service.fetch_news_by_niche(niche)
        logger.info(f"Fetched {len(articles)} articles")
        
        # Add niche information to articles
        for article in articles:
            article['niche'] = niche
            
        # Generate blog posts for up to 3 articles
        logger.info("Starting blog post generation...")
        tasks = [content_generator.generate_blog_post(article) for article in articles[:3]]
        generated_posts = await asyncio.gather(*tasks)
        
        for post in generated_posts:
            post['content'] = markdown2.markdown(post['content'])
            post['niche'] = niche
        
        # Save to MongoDB
        logger.info("Saving posts to database...")
        await content_generator.update_cached_posts(generated_posts)
        
        end_time = time.time()
        logger.info(f"Content generation completed in {end_time - start_time:.2f} seconds")
        
        return templates.TemplateResponse("preview.html", {
            "request": request,
            "posts": generated_posts
        })
    except Exception as e:
        logger.error(f"Admin generate error: {e}")
        return templates.TemplateResponse("preview.html", {
            "request": request,
            "posts": []
        })


@app.get("/page/{page_number}")
async def paginated_posts(request: Request, page_number: int = 1):
    try:
        result = await content_generator.db.get_paginated_posts(page_number)
        
        for post in result["posts"]:
            post['content'] = markdown2.markdown(post['content'])
        
        return templates.TemplateResponse("home.html", {
            "request": request,
            "posts": result["posts"],
            "pagination": {
                "current": result["page"],
                "total_pages": result["pages"],
                "total_posts": result["total"]
            }
        })
    except Exception as e:
        logger.error(f"Pagination error: {e}")
        return RedirectResponse(url="/")

# First, remove all duplicate category routes and keep only these routes in this order:

# 1. Add the search route BEFORE any catch-all routes
# Remove these imports if they're only used for search
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

# Remove the entire search route
# DELETE this section:
@app.get("/search")
async def search_posts(request: Request, q: str = ""):
    try:
        if not q:
            return templates.TemplateResponse("search.html", {
                "request": request,
                "posts": [],
                "query": "",
                "show_empty_state": True
            })
        
        # Search in MongoDB
        posts = await content_generator.db.search_posts(q)
        
        # Convert markdown content for display
        for post in posts:
            if 'content' in post:
                post['content'] = markdown2.markdown(post['content'])
        
        return templates.TemplateResponse("search.html", {
            "request": request,
            "posts": posts,
            "query": q,
            "total_results": len(posts),
            "show_empty_state": len(posts) == 0
        })
    except Exception as e:
        logger.error(f"Search error: {e}")
        return templates.TemplateResponse("search.html", {
            "request": request,
            "posts": [],
            "query": q,
            "error": "An error occurred while searching"
        })

# 2. Keep all admin routes

# 3. Finally, keep only this version of the category route at the END
@app.get("/{category}")
async def category_page(request: Request, category: str):
    # Define valid categories
    valid_categories = ['tech', 'ai', 'startup', 'meditation']
    
    # Skip processing for favicon.ico and other invalid categories
    if category not in valid_categories:
        return RedirectResponse(url="/")
    
    try:
        # Get category posts from MongoDB
        posts = await content_generator.get_posts_by_category(category)
        
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "posts": posts,
            "category": category
        })
    except Exception as e:
        logger.error(f"Category error: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "posts": [],
            "category": category
        })

security = HTTPBasic()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("ADMIN_USERNAME", "admin")
    correct_password = os.getenv("ADMIN_PASSWORD", "admin")
    is_correct_username = secrets.compare_digest(credentials.username.encode("utf8"), correct_username.encode("utf8"))
    is_correct_password = secrets.compare_digest(credentials.password.encode("utf8"), correct_password.encode("utf8"))
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Move the admin routes before the category route
@app.get("/admin")
async def admin_dashboard(request: Request, username: str = Depends(verify_admin)):
    try:
        # Get statistics and posts for dashboard
        stats = await content_generator.db.get_statistics()
        posts = await content_generator.get_cached_posts()
        
        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "stats": stats,
            "posts": posts,
            "username": username
        })
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Move the category route after all admin routes
@app.get("/{category}")
async def category_page(request: Request, category: str):
    # Update valid categories to match URL slugs
    valid_categories = {
        'ai-news': 'AI News',
        'startup-ecosystem': 'Startup Ecosystem',
        'productivity-tools': 'Productivity Tools',
        'dev-trends': 'Dev Trends',
        'tech-ethics': 'Tech Ethics',
        'meditation-mindfulness': 'Meditation & Mindfulness',
        'vedic-philosophy': 'Vedic Philosophy',
        'lucid-dreaming': 'Lucid Dreaming',
        'habit-science': 'Habit Science'
    }
    
    if category not in valid_categories:
        return RedirectResponse(url="/")
    
    try:
        # Use the URL slug for searching
        logger.info(f"Searching for posts in category: {valid_categories[category]}")
        posts = await content_generator.get_posts_by_hashtag(valid_categories[category])
        
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "posts": posts,
            "show_empty_state": not posts,
            "category": category,
            "category_title": valid_categories[category]
        })
    except Exception as e:
        logger.error(f"Category error: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "posts": [],
            "featured_posts": [],  # Add this
            "show_empty_state": True,
            "category": category,
            "category_title": valid_categories.get(category, '')
        })

@app.get("/post/{post_id}")
async def post_detail(request: Request, post_id: str):
    try:
        # Get specific post from MongoDB
        post = await content_generator.get_post_by_id(post_id)
        
        if not post:
            logger.warning(f"Post not found: {post_id}")
            return RedirectResponse(url="/")
            
        # Get related posts based on the current post's niche/tags
        related_posts = []
        if post.get('niche'):
            # Fetch posts with the same niche, excluding the current post
            related_posts = await content_generator.get_posts_by_hashtag(post['niche'])
            related_posts = [p for p in related_posts if p['_id'] != post['_id']][:3]  # Limit to 3 related posts
            
        post['content'] = markdown2.markdown(post['content'])
        
        return templates.TemplateResponse("post.html", {
            "request": request,
            "post": post
        })
    except Exception as e:
        logger.error(f"Post detail error: {e}")
        return RedirectResponse(url="/")

# Update the generate_content route
@app.post("/")
async def generate_content(request: Request, niche: str = Form(...)):
    try:
        logger.info(f"Starting content generation for niche: {niche}")
        start_time = time.time()
        
        # Fetch news articles based on selected niche
        logger.info("Fetching news articles...")
        articles = await news_service.fetch_news_by_niche(niche)
        logger.info(f"Fetched {len(articles)} articles")
        
        # Add niche information to articles
        for article in articles:
            article['niche'] = niche
            
        # Generate blog posts for up to 3 articles
        logger.info("Starting blog post generation...")
        tasks = [content_generator.generate_blog_post(article) for article in articles[:3]]
        generated_posts = await asyncio.gather(*tasks)
        
        for post in generated_posts:
            post['content'] = markdown2.markdown(post['content'])
            post['niche'] = niche
        
        # Save to MongoDB
        logger.info("Saving posts to database...")
        await content_generator.update_cached_posts(generated_posts)
        
        end_time = time.time()
        logger.info(f"Content generation completed in {end_time - start_time:.2f} seconds")
        
        return templates.TemplateResponse("preview.html", {
            "request": request,
            "posts": generated_posts
        })
    except Exception as e:
        logger.error(f"Admin generate error: {e}")
        return templates.TemplateResponse("preview.html", {
            "request": request,
            "posts": []
        })


@app.get("/page/{page_number}")
async def paginated_posts(request: Request, page_number: int = 1):
    try:
        result = await content_generator.db.get_paginated_posts(page_number)
        
        for post in result["posts"]:
            post['content'] = markdown2.markdown(post['content'])
        
        return templates.TemplateResponse("home.html", {
            "request": request,
            "posts": result["posts"],
            "pagination": {
                "current": result["page"],
                "total_pages": result["pages"],
                "total_posts": result["total"]
            }
        })
    except Exception as e:
        logger.error(f"Pagination error: {e}")
        return RedirectResponse(url="/")

# First, remove all duplicate category routes and keep only these routes in this order:

# 1. Add the search route BEFORE any catch-all routes
# Remove these imports if they're only used for search
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

# Remove the entire search route
# DELETE this section:
@app.get("/search")
async def search_posts(request: Request, q: str = ""):
    try:
        if not q:
            return templates.TemplateResponse("search.html", {
                "request": request,
                "posts": [],
                "query": "",
                "show_empty_state": True
            })
        
        # Search in MongoDB
        posts = await content_generator.db.search_posts(q)
        
        # Convert markdown content for display
        for post in posts:
            if 'content' in post:
                post['content'] = markdown2.markdown(post['content'])
        
        return templates.TemplateResponse("search.html", {
            "request": request,
            "posts": posts,
            "query": q,
            "total_results": len(posts),
            "show_empty_state": len(posts) == 0
        })
    except Exception as e:
        logger.error(f"Search error: {e}")
        return templates.TemplateResponse("search.html", {
            "request": request,
            "posts": [],
            "query": q,
            "error": "An error occurred while searching"
        })

# 2. Keep all admin routes

# 3. Finally, keep only this version of the category route at the END
@app.get("/{category}")
async def category_page(request: Request, category: str):
    # Define valid categories
    valid_categories = ['tech', 'ai', 'startup', 'meditation']
    
    # Skip processing for favicon.ico and other invalid categories
    if category not in valid_categories:
        return RedirectResponse(url="/")
    
    try:
        # Get category posts from MongoDB
        posts = await content_generator.get_posts_by_category(category)
        
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "posts": posts,
            "category": category
        })
    except Exception as e:
        logger.error(f"Category error: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "posts": [],
            "category": category
        })

security = HTTPBasic()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("ADMIN_USERNAME", "admin")
    correct_password = os.getenv("ADMIN_PASSWORD", "admin")
    is_correct_username = secrets.compare_digest(credentials.username.encode("utf8"), correct_username.encode("utf8"))
    is_correct_password = secrets.compare_digest(credentials.password.encode("utf8"), correct_password.encode("utf8"))
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Move the admin routes before the category route
@app.get("/admin")
async def admin_dashboard(request: Request, username: str = Depends(verify_admin)):
    try:
        # Get statistics and posts for dashboard
        stats = await content_generator.db.get_statistics()
        posts = await content_generator.get_cached_posts()
        
        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "stats": stats,
            "posts": posts,
            "username": username
        })
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Move the category route after all admin routes
@app.get("/{category}")
async def category_page(request: Request, category: str):
    try:
        result = await content_generator.db.get_paginated_posts(1, 10)
        stats = await content_generator.db.get_stats()
        
        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "posts": result["posts"],
            "stats": stats,
            "username": username
        })
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/admin/post/delete/{post_id}")
async def delete_post(post_id: str, username: str = Depends(verify_admin)):
    try:
        # Delete from MongoDB
        success = await content_generator.db.delete_post(post_id)
        if not success:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Clear all caches
        await content_generator.clear_all_caches()
        
        return {"message": "Post deleted successfully"}
    except Exception as e:
        logger.error(f"Delete post error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete post")

@app.get("/admin/post/edit/{post_id}")
async def edit_post_form(request: Request, post_id: str, username: str = Depends(verify_admin)):
    try:
        post = await content_generator.db.get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return templates.TemplateResponse("admin/edit_post.html", {
            "request": request,
            "post": post,
            "username": username
        })
    except Exception as e:
        logger.error(f"Edit post form error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load post")

@app.post("/admin/post/edit/{post_id}")
async def update_post(
    request: Request,
    post_id: str,
    title: str = Form(...),
    content: str = Form(...),
    meta_description: str = Form(...),
    hashtags: str = Form(...),
    username: str = Depends(verify_admin)
):
    try:
        post_data = {
            "title": title,
            "content": content,
            "meta_description": meta_description,
            "hashtags": [tag.strip() for tag in hashtags.split(",")]
        }
        
        success = await content_generator.db.update_post(post_id, post_data)
        if not success:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return RedirectResponse(url="/admin/generate", status_code=303)
    except Exception as e:
        logger.error(f"Update post error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update post")

@app.get("/analytics")
async def analytics_dashboard(request: Request, username: str = Depends(verify_admin)):
    try:
        analytics = await content_generator.db.get_analytics()
        return templates.TemplateResponse("admin/analytics.html", {
            "request": request,
            "analytics": analytics
        })
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load analytics")


@app.get("/admin/generate")
async def admin_generate_page(request: Request, username: str = Depends(verify_admin)):
    try:
        # Get all existing posts
        all_posts = await content_generator.get_cached_posts()
        
        return templates.TemplateResponse("admin_generate.html", {
            "request": request,
            "username": username,
            "all_posts": all_posts
        })
    except Exception as e:
        logger.error(f"Admin page error: {e}")
        return templates.TemplateResponse("admin_generate.html", {
            "request": request,
            "username": username,
            "error": "Failed to load posts"
        })

@app.post("/admin/generate")
async def admin_generate_content(
    request: Request,
    niche: str = Form(...),
    username: str = Depends(verify_admin)
):
    try:
        logger.info(f"Admin generating content for niche: {niche}")
        start_time = time.time()
        
        # Fetch news articles based on selected niche
        articles = await news_service.fetch_news_by_niche(niche)
        
        # Add niche information to articles
        for article in articles:
            article['niche'] = niche
            
        # Generate blog posts
        tasks = [content_generator.generate_blog_post(article) for article in articles[:3]]
        generated_posts = await asyncio.gather(*tasks)
        
        # Save to MongoDB and clear cache
        await content_generator.update_cached_posts(generated_posts)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Return to preview.html instead of admin/preview.html
        return templates.TemplateResponse("preview.html", {
            "request": request,
            "posts": generated_posts,
            "username": username,
            "success": f"Successfully generated {len(generated_posts)} articles in {generation_time:.1f} seconds!"
        })
    except Exception as e:
        logger.error(f"Admin generate error: {str(e)}")
        return templates.TemplateResponse("admin_generate.html", {
            "request": request,
            "username": username,
            "error": f"Failed to generate content: {str(e)}"
        })

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", 8000))  # Render injects the correct PORT
    uvicorn.run("main:app", host="0.0.0.0", port=port)

