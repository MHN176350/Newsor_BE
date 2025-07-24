"""
Model-specific cache managers for Newsor entities.
"""
from typing import List, Optional, Dict, Any
import logging
from .base import RedisCache, WriteBackCache

logger = logging.getLogger(__name__)


class NewsCacheManager:
    """Cache manager for News/Articles."""
    
    def __init__(self):
        self.cache = RedisCache('default')
        self.write_back = WriteBackCache('write_back')
        self.cache_timeout = 3600  # 1 hour for news articles
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get article from cache by ID."""
        key = f"article:id:{article_id}"
        return self.cache.get(key)
    
    def get_article_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get article from cache by slug."""
        key = f"article:slug:{slug}"
        return self.cache.get(key)
    
    def cache_article(self, article_data: Dict[str, Any]) -> bool:
        """Cache article data."""
        try:
            article_id = article_data.get('id')
            slug = article_data.get('slug')
            
            success = True
            if article_id:
                id_key = f"article:id:{article_id}"
                success &= self.cache.set(id_key, article_data, self.cache_timeout)
            
            if slug:
                slug_key = f"article:slug:{slug}"
                success &= self.cache.set(slug_key, article_data, self.cache_timeout)
            
            return success
        except Exception as e:
            logger.error(f"Error caching article: {e}")
            return False
    
    def invalidate_article(self, article_id: int, slug: Optional[str] = None) -> bool:
        """Invalidate article cache."""
        try:
            keys_to_delete = [f"article:id:{article_id}"]
            if slug:
                keys_to_delete.append(f"article:slug:{slug}")
            
            # Also invalidate related lists
            keys_to_delete.extend([
                "articles:published",
                "articles:trending",
                "articles:category:*",
                f"articles:author:{article_id}",
            ])
            
            return self.cache.delete_many(keys_to_delete)
        except Exception as e:
            logger.error(f"Error invalidating article cache: {e}")
            return False
    
    def get_published_articles(self, page: int = 1, per_page: int = 20) -> Optional[Dict[str, Any]]:
        """Get cached published articles."""
        key = f"articles:published:page:{page}:per_page:{per_page}"
        return self.cache.get(key)
    
    def cache_published_articles(self, articles_data: Dict[str, Any], page: int = 1, per_page: int = 20) -> bool:
        """Cache published articles list."""
        key = f"articles:published:page:{page}:per_page:{per_page}"
        return self.cache.set(key, articles_data, 600)  # 10 minutes for lists
    
    def get_trending_articles(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached trending articles."""
        key = "articles:trending"
        return self.cache.get(key)
    
    def cache_trending_articles(self, articles: List[Dict[str, Any]]) -> bool:
        """Cache trending articles."""
        key = "articles:trending"
        return self.cache.set(key, articles, 1800)  # 30 minutes for trending
    
    def queue_article_update(self, article_id: int, update_data: Dict[str, Any]) -> bool:
        """Queue article update for write-back."""
        return self.write_back.queue_write('update', 'News', str(article_id), update_data)
    
    def queue_view_count_increment(self, article_id: int) -> bool:
        """Queue view count increment."""
        # Use cache to track view counts and batch update
        key = f"views:article:{article_id}"
        try:
            current_views = self.cache.get(key) or 0
            new_views = current_views + 1
            self.cache.set(key, new_views, 3600)  # 1 hour
            
            # Queue for write-back every 10 views or after timeout
            if new_views % 10 == 0:
                return self.write_back.queue_write('update', 'News', str(article_id), {'view_count': new_views})
            return True
        except Exception as e:
            logger.error(f"Error queuing view count increment: {e}")
            return False


class UserCacheManager:
    """Cache manager for Users."""
    
    def __init__(self):
        self.cache = RedisCache('default')
        self.write_back = WriteBackCache('write_back')
        self.cache_timeout = 1800  # 30 minutes for user data
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user from cache by ID."""
        key = f"user:id:{user_id}"
        return self.cache.get(key)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user from cache by username."""
        key = f"user:username:{username}"
        return self.cache.get(key)
    
    def cache_user(self, user_data: Dict[str, Any]) -> bool:
        """Cache user data."""
        try:
            user_id = user_data.get('id')
            username = user_data.get('username')
            
            success = True
            if user_id:
                id_key = f"user:id:{user_id}"
                success &= self.cache.set(id_key, user_data, self.cache_timeout)
            
            if username:
                username_key = f"user:username:{username}"
                success &= self.cache.set(username_key, user_data, self.cache_timeout)
            
            return success
        except Exception as e:
            logger.error(f"Error caching user: {e}")
            return False
    
    def invalidate_user(self, user_id: int, username: Optional[str] = None) -> bool:
        """Invalidate user cache."""
        try:
            keys_to_delete = [f"user:id:{user_id}"]
            if username:
                keys_to_delete.append(f"user:username:{username}")
            
            return self.cache.delete_many(keys_to_delete)
        except Exception as e:
            logger.error(f"Error invalidating user cache: {e}")
            return False
    
    def get_user_permissions(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user permissions."""
        key = f"user:permissions:{user_id}"
        return self.cache.get(key)
    
    def cache_user_permissions(self, user_id: int, permissions: Dict[str, Any]) -> bool:
        """Cache user permissions."""
        key = f"user:permissions:{user_id}"
        return self.cache.set(key, permissions, 3600)  # 1 hour for permissions


class CategoryCacheManager:
    """Cache manager for Categories."""
    
    def __init__(self):
        self.cache = RedisCache('default')
        self.cache_timeout = 3600  # 1 hour for categories
    
    def get_all_categories(self) -> Optional[List[Dict[str, Any]]]:
        """Get all cached categories."""
        key = "categories:all"
        return self.cache.get(key)
    
    def cache_all_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """Cache all categories."""
        key = "categories:all"
        return self.cache.set(key, categories, self.cache_timeout)
    
    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category from cache by ID."""
        key = f"category:id:{category_id}"
        return self.cache.get(key)
    
    def get_category_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get category from cache by slug."""
        key = f"category:slug:{slug}"
        return self.cache.get(key)
    
    def cache_category(self, category_data: Dict[str, Any]) -> bool:
        """Cache category data."""
        try:
            category_id = category_data.get('id')
            slug = category_data.get('slug')
            
            success = True
            if category_id:
                id_key = f"category:id:{category_id}"
                success &= self.cache.set(id_key, category_data, self.cache_timeout)
            
            if slug:
                slug_key = f"category:slug:{slug}"
                success &= self.cache.set(slug_key, category_data, self.cache_timeout)
            
            return success
        except Exception as e:
            logger.error(f"Error caching category: {e}")
            return False
    
    def invalidate_category(self, category_id: int, slug: Optional[str] = None) -> bool:
        """Invalidate category cache."""
        try:
            keys_to_delete = [f"category:id:{category_id}", "categories:all"]
            if slug:
                keys_to_delete.append(f"category:slug:{slug}")
            
            return self.cache.delete_many(keys_to_delete)
        except Exception as e:
            logger.error(f"Error invalidating category cache: {e}")
            return False


class CommentCacheManager:
    """Cache manager for Comments."""
    
    def __init__(self):
        self.cache = RedisCache('default')
        self.write_back = WriteBackCache('write_back')
        self.cache_timeout = 1800  # 30 minutes for comments
    
    def get_article_comments(self, article_id: int, page: int = 1, per_page: int = 20) -> Optional[Dict[str, Any]]:
        """Get cached comments for an article."""
        key = f"comments:article:{article_id}:page:{page}:per_page:{per_page}"
        return self.cache.get(key)
    
    def cache_article_comments(self, article_id: int, comments_data: Dict[str, Any], page: int = 1, per_page: int = 20) -> bool:
        """Cache comments for an article."""
        key = f"comments:article:{article_id}:page:{page}:per_page:{per_page}"
        return self.cache.set(key, comments_data, self.cache_timeout)
    
    def invalidate_article_comments(self, article_id: int) -> bool:
        """Invalidate all comments cache for an article."""
        try:
            # This would require pattern matching in a real implementation
            # For now, just clear specific pages
            keys_to_delete = [f"comments:article:{article_id}:page:{i}:per_page:20" for i in range(1, 6)]
            return self.cache.delete_many(keys_to_delete)
        except Exception as e:
            logger.error(f"Error invalidating article comments cache: {e}")
            return False
    
    def queue_comment_creation(self, comment_data: Dict[str, Any]) -> bool:
        """Queue comment creation for write-back."""
        import uuid
        temp_id = str(uuid.uuid4())
        return self.write_back.queue_write('create', 'Comment', temp_id, comment_data)


# Global cache manager instances
news_cache = NewsCacheManager()
user_cache = UserCacheManager()
category_cache = CategoryCacheManager()
comment_cache = CommentCacheManager()
