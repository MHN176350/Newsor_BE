"""
Cache-enabled GraphQL resolvers for improved performance.
"""
from core.infrastructure.cache.managers import news_cache, user_cache, category_cache, comment_cache
from core.infrastructure.cache.decorators import cache_with_key_generator
from api.models import News, User, Category, Comment
import logging

logger = logging.getLogger(__name__)


class CachedNewsResolver:
    """Cache-enabled resolvers for News/Articles."""
    
    @staticmethod
    @cache_with_key_generator(
        lambda info, id=None, slug=None, **kwargs: 
            f"article:id:{id}" if id else f"article:slug:{slug}",
        timeout=3600
    )
    def resolve_news_by_id_or_slug(info, id=None, slug=None):
        """Get news article by ID or slug with caching."""
        try:
            if id:
                # Try cache first
                cached_article = news_cache.get_article_by_id(id)
                if cached_article:
                    return cached_article
                
                # Fallback to database
                article = News.objects.select_related('author', 'category').prefetch_related('tags').get(id=id)
                
                # Cache the result
                article_data = {
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug,
                    'content': article.content,
                    'excerpt': article.excerpt,
                    'featured_image_url': article.featured_image_url,
                    'status': article.status,
                    'view_count': article.view_count,
                    'like_count': article.like_count,
                    'created_at': article.created_at.isoformat(),
                    'updated_at': article.updated_at.isoformat(),
                    'author': {
                        'id': article.author.id,
                        'username': article.author.username,
                        'first_name': article.author.first_name,
                        'last_name': article.author.last_name,
                    },
                    'category': {
                        'id': article.category.id if article.category else None,
                        'name': article.category.name if article.category else None,
                        'slug': article.category.slug if article.category else None,
                    },
                    'tags': [{'id': tag.id, 'name': tag.name, 'slug': tag.slug} for tag in article.tags.all()]
                }
                news_cache.cache_article(article_data)
                return article
                
            elif slug:
                # Try cache first
                cached_article = news_cache.get_article_by_slug(slug)
                if cached_article:
                    # Convert cached data back to model instance if needed
                    return News.objects.get(id=cached_article['id'])
                
                # Fallback to database
                article = News.objects.select_related('author', 'category').prefetch_related('tags').get(slug=slug)
                
                # Cache logic similar to above
                article_data = {
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug,
                    'content': article.content,
                    'excerpt': article.excerpt,
                    'featured_image_url': article.featured_image_url,
                    'status': article.status,
                    'view_count': article.view_count,
                    'like_count': article.like_count,
                    'created_at': article.created_at.isoformat(),
                    'updated_at': article.updated_at.isoformat(),
                }
                news_cache.cache_article(article_data)
                return article
                
        except News.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error in cached news resolver: {e}")
            return None
    
    @staticmethod
    def resolve_published_news_with_cache(info, page=1, per_page=20, category_id=None):
        """Get published news with caching."""
        try:
            # Try cache first
            cache_key = f"published:page:{page}:per_page:{per_page}"
            if category_id:
                cache_key += f":category:{category_id}"
            
            cached_data = news_cache.get_published_articles(page, per_page)
            if cached_data and not category_id:  # Simple case for now
                return cached_data
            
            # Fallback to database
            queryset = News.objects.filter(status='published').select_related('author', 'category').prefetch_related('tags')
            
            if category_id:
                queryset = queryset.filter(category_id=category_id)
            
            # Pagination
            offset = (page - 1) * per_page
            articles = list(queryset[offset:offset + per_page])
            total_count = queryset.count()
            
            # Prepare data for caching
            articles_data = {
                'articles': [
                    {
                        'id': article.id,
                        'title': article.title,
                        'slug': article.slug,
                        'excerpt': article.excerpt,
                        'featured_image_url': article.featured_image_url,
                        'view_count': article.view_count,
                        'like_count': article.like_count,
                        'created_at': article.created_at.isoformat(),
                        'author': article.author.username,
                        'category': article.category.name if article.category else None,
                    }
                    for article in articles
                ],
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'has_next': (page * per_page) < total_count
            }
            
            # Cache the result (only for simple cases)
            if not category_id:
                news_cache.cache_published_articles(articles_data, page, per_page)
            
            return articles_data
            
        except Exception as e:
            logger.error(f"Error in published news resolver: {e}")
            return {'articles': [], 'total_count': 0, 'page': page, 'per_page': per_page, 'has_next': False}
    
    @staticmethod
    def resolve_trending_news():
        """Get trending news with caching."""
        try:
            # Try cache first
            cached_trending = news_cache.get_trending_articles()
            if cached_trending:
                return cached_trending
            
            # Fallback to database
            trending = list(
                News.objects.filter(status='published')
                .select_related('author', 'category')
                .order_by('-view_count', '-like_count', '-created_at')[:10]
            )
            
            # Cache the result
            trending_data = [
                {
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug,
                    'excerpt': article.excerpt,
                    'featured_image_url': article.featured_image_url,
                    'view_count': article.view_count,
                    'like_count': article.like_count,
                    'created_at': article.created_at.isoformat(),
                    'author': article.author.username,
                    'category': article.category.name if article.category else None,
                }
                for article in trending
            ]
            
            news_cache.cache_trending_articles(trending_data)
            return trending
            
        except Exception as e:
            logger.error(f"Error in trending news resolver: {e}")
            return []


class CachedUserResolver:
    """Cache-enabled resolvers for Users."""
    
    @staticmethod
    def resolve_user_with_cache(info, user_id=None, username=None):
        """Get user with caching."""
        try:
            if user_id:
                # Try cache first
                cached_user = user_cache.get_user_by_id(user_id)
                if cached_user:
                    return User.objects.get(id=cached_user['id'])
                
                # Fallback to database
                user = User.objects.select_related('profile').get(id=user_id)
                
                # Cache the result
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.isoformat(),
                }
                user_cache.cache_user(user_data)
                return user
                
            elif username:
                # Similar logic for username
                cached_user = user_cache.get_user_by_username(username)
                if cached_user:
                    return User.objects.get(id=cached_user['id'])
                
                user = User.objects.select_related('profile').get(username=username)
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.isoformat(),
                }
                user_cache.cache_user(user_data)
                return user
                
        except User.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error in cached user resolver: {e}")
            return None


class CachedCategoryResolver:
    """Cache-enabled resolvers for Categories."""
    
    @staticmethod
    def resolve_all_categories():
        """Get all categories with caching."""
        try:
            # Try cache first
            cached_categories = category_cache.get_all_categories()
            if cached_categories:
                return [Category.objects.get(id=cat['id']) for cat in cached_categories]
            
            # Fallback to database
            categories = list(Category.objects.filter(is_active=True).order_by('name'))
            
            # Cache the result
            categories_data = [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'slug': cat.slug,
                    'description': cat.description,
                    'is_active': cat.is_active,
                }
                for cat in categories
            ]
            category_cache.cache_all_categories(categories_data)
            return categories
            
        except Exception as e:
            logger.error(f"Error in cached categories resolver: {e}")
            return []


class CachedCommentResolver:
    """Cache-enabled resolvers for Comments."""
    
    @staticmethod
    def resolve_article_comments_with_cache(info, article_id, page=1, per_page=20):
        """Get article comments with caching."""
        try:
            # Try cache first
            cached_comments = comment_cache.get_article_comments(article_id, page, per_page)
            if cached_comments:
                return cached_comments
            
            # Fallback to database
            comments = Comment.objects.filter(article_id=article_id, parent=None).select_related('author').order_by('-created_at')
            
            # Pagination
            offset = (page - 1) * per_page
            paginated_comments = list(comments[offset:offset + per_page])
            total_count = comments.count()
            
            # Prepare data for caching
            comments_data = {
                'comments': [
                    {
                        'id': comment.id,
                        'content': comment.content,
                        'author': comment.author.username,
                        'created_at': comment.created_at.isoformat(),
                        'like_count': comment.like_count,
                    }
                    for comment in paginated_comments
                ],
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'has_next': (page * per_page) < total_count
            }
            
            # Cache the result
            comment_cache.cache_article_comments(article_id, comments_data, page, per_page)
            return comments_data
            
        except Exception as e:
            logger.error(f"Error in cached comments resolver: {e}")
            return {'comments': [], 'total_count': 0, 'page': page, 'per_page': per_page, 'has_next': False}


# Cache invalidation helpers
class CacheInvalidator:
    """Helpers for cache invalidation."""
    
    @staticmethod
    def invalidate_news_cache(news_id, slug=None):
        """Invalidate news-related cache."""
        news_cache.invalidate_article(news_id, slug)
    
    @staticmethod
    def invalidate_user_cache(user_id, username=None):
        """Invalidate user-related cache."""
        user_cache.invalidate_user(user_id, username)
    
    @staticmethod
    def invalidate_category_cache(category_id, slug=None):
        """Invalidate category-related cache."""
        category_cache.invalidate_category(category_id, slug)
    
    @staticmethod
    def invalidate_comments_cache(article_id):
        """Invalidate comments cache for an article."""
        comment_cache.invalidate_article_comments(article_id)
