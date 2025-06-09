from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from bson import ObjectId
import logging
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        try:
            MONGODB_URI = os.getenv("MONGODB_URI")
            if not MONGODB_URI:
                raise ValueError("MongoDB URI not found in environment variables")
            
            # Remove directConnection and adjust timeouts
            self.client = AsyncIOMotorClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            self.db = self.client.blog_db
            self.posts = self.db.posts
            logger.info("MongoDB client initialized")
        except Exception as e:
            logger.error(f"MongoDB initialization error: {e}")
            raise

    async def check_connection(self) -> bool:
        try:
            # Test the connection immediately
            await self.client.admin.command('ping')
            # Create necessary indexes
            await self.posts.create_index([("title", "text"), ("content", "text")])
            logger.info("Successfully connected to MongoDB and created indexes")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    async def save_post(self, post: Dict) -> Optional[str]:
        try:
            post["created_at"] = datetime.utcnow()
            post["updated_at"] = datetime.utcnow()
            result = await self.posts.insert_one(post)
            logger.info(f"Successfully saved post with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except OperationFailure as e:
            logger.error(f"Failed to save post: {e}")
            return None

    async def get_all_posts(self) -> List[Dict]:
        try:
            cursor = self.posts.find().sort("created_at", -1)
            posts = await cursor.to_list(length=None)
            return [self._prepare_post(post) for post in posts]
        except OperationFailure as e:
            logger.error(f"Failed to fetch posts: {e}")
            return []

    async def get_posts_by_category(self, category: str) -> List[Dict]:
        try:
            logger.info(f"MongoDB: Searching for posts with category: {category}")
            # Search in both category and hashtags fields
            query = {
                "$or": [
                    {"category": category},
                    {"hashtags": {"$in": [category]}}
                ]
            }
            cursor = self.posts.find(query).sort("created_at", -1)
            posts = await cursor.to_list(length=None)
            logger.info(f"Found {len(posts)} posts for category {category}")
            return [self._prepare_post(post) for post in posts]
        except Exception as e:
            logger.error(f"Failed to fetch posts by category {category}: {e}")
            return []

    async def get_posts_by_hashtag(self, tag: str) -> List[Dict]:
        try:
            logger.info(f"Searching for posts with tag: {tag}")
            
            # Convert the tag to lowercase and replace spaces with hyphens
            normalized_tag = tag.lower().replace(' ', '-')
            
            # Search for the normalized tag in the first position
            query = {
                "niche": normalized_tag
            }
            
            cursor = self.posts.find(query).sort("created_at", -1)
            posts = await cursor.to_list(length=None)
            
            logger.info(f"Found {len(posts)} posts with tag '{tag}'")
            return [self._prepare_post(post) for post in posts]
        except Exception as e:
            logger.error(f"Failed to fetch posts by hashtag {tag}: {e}")
            return []

    async def get_post_by_id(self, post_id: str) -> Optional[Dict]:
        try:
            post = await self.posts.find_one({"_id": ObjectId(post_id)})
            return self._prepare_post(post) if post else None
        except (OperationFailure, InvalidId) as e:
            logger.error(f"Failed to fetch post {post_id}: {e}")
            return None

    def _prepare_post(self, post: Dict) -> Dict:
        """Prepare post for JSON serialization"""
        if post:
            post["_id"] = str(post["_id"])
        return post

    async def update_post(self, post_id: str, post_data: Dict) -> bool:
        try:
            post_data["updated_at"] = datetime.utcnow()
            result = await self.posts.update_one(
                {"_id": ObjectId(post_id)},
                {"$set": post_data}
            )
            if result.modified_count > 0:
                # Clear cache after update
                self.cache = {}
                logger.info(f"Successfully updated post {post_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update post {post_id}: {e}")
            return False

    async def track_view(self, post_id: str):
        try:
            await self.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$inc": {"views": 1},
                    "$push": {
                        "view_history": {
                            "timestamp": datetime.utcnow(),
                            "user_agent": request.headers.get("user-agent", "unknown")
                        }
                    }
                }
            )
        except Exception as e:
            logger.error(f"Track view error: {e}")

    async def delete_post(self, post_id: str) -> bool:
        try:
            result = await self.posts.delete_one({"_id": ObjectId(post_id)})
            if result.deleted_count > 0:
                logger.info(f"Successfully deleted post {post_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete post {post_id}: {e}")
            return False

    async def update_post(self, post_id: str, post_data: Dict) -> bool:
        try:
            post_data["updated_at"] = datetime.utcnow()
            result = await self.posts.update_one(
                {"_id": ObjectId(post_id)},
                {"$set": post_data}
            )
            if result.modified_count > 0:
                # Clear cache after update
                self.cache = {}
                logger.info(f"Successfully updated post {post_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update post {post_id}: {e}")
            return False

    async def get_paginated_posts(self, page: int = 1, per_page: int = 10) -> Dict:
        try:
            total = await self.posts.count_documents({})
            cursor = self.posts.find().sort("created_at", -1).skip((page - 1) * per_page).limit(per_page)
            posts = await cursor.to_list(length=None)
            return {
                "posts": [self._prepare_post(post) for post in posts],
                "total": total,
                "page": page,
                "pages": (total + per_page - 1) // per_page
            }
        except OperationFailure as e:
            logger.error(f"Pagination error: {e}")
            return {"posts": [], "total": 0, "page": page, "pages": 0}

    # Remove the search_posts method
    # DELETE this method:
    async def search_posts(self, query: str) -> List[Dict]:
        try:
            # Create text index if it doesn't exist
            await self.posts.create_index([("title", "text"), ("content", "text")])
            
            # Perform text search
            cursor = self.posts.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})])
            
            posts = await cursor.to_list(length=None)
            return [self._prepare_post(post) for post in posts]  # Don't forget to prepare posts
        except Exception as e:
            logger.error(f"Search error: {e}")