import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from .models import (
    Category, Tag, UserProfile, News, Comment, 
    Like, ReadingHistory, NewsletterSubscription
)
from .utils import sanitize_html_content, get_cloudinary_upload_signature
import base64
import io
from PIL import Image
import cloudinary.uploader
import uuid
from .cloudinary_utils import CloudinaryUtils
from django.db.models import Count, Q


class UserType(DjangoObjectType):
    """
    GraphQL User type
    """
    profile = graphene.Field(lambda: UserProfileType)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined')

    def resolve_profile(self, info):
        """
        Resolve user profile
        """
        try:
            return self.profile
        except UserProfile.DoesNotExist:
            return None


class CategoryType(DjangoObjectType):
    """
    GraphQL Category type
    """
    class Meta:
        model = Category
        fields = '__all__'


class TagType(DjangoObjectType):
    """
    GraphQL Tag type
    """
    class Meta:
        model = Tag
        fields = '__all__'


class UserProfileType(DjangoObjectType):
    """
    GraphQL UserProfile type
    """
    avatar_url = graphene.String()  # Custom field for avatar URL
    
    class Meta:
        model = UserProfile
        exclude = ['avatar']  # Exclude the CloudinaryField from auto-generation
    
    def resolve_avatar_url(self, info):
        """
        Resolve avatar URL with fallback to default image
        """
        if self.avatar:
            try:
                return str(self.avatar.url)
            except Exception:
                # If there's an error getting the cloudinary URL, return default
                return "/static/images/default-avatar.svg"
        else:
            # Return default avatar if no avatar is set
            return "/static/images/default-avatar.svg"


class NewsType(DjangoObjectType):
    """
    GraphQL News type
    """
    featured_image_url = graphene.String()  # Custom field for featured image URL
    
    class Meta:
        model = News
        exclude = ['featured_image']  # Exclude the CloudinaryField from auto-generation
    
    def resolve_featured_image_url(self, info):
        """
        Resolve featured image URL with fallback to default image
        """
        if self.featured_image:
            try:
                return str(self.featured_image.url)
            except Exception:
                # If there's an error getting the cloudinary URL, return default
                return "/static/images/default-news.svg"
        else:
            # Return default news image if no image is set
            return "/static/images/default-news.svg"


class CommentType(DjangoObjectType):
    """
    GraphQL Comment type
    """
    replies = graphene.List(lambda: CommentType)
    comment_like_count = graphene.Int()
    is_comment_liked = graphene.Boolean()

    class Meta:
        model = Comment
        fields = '__all__'

    def resolve_replies(self, info):
        return self.replies.all().order_by('created_at')

    def resolve_comment_like_count(self, info):
        """
        Count the number of active likes for this comment
        """
        return Like.objects.filter(comment_id=self.id, is_active=True).count()
    
    def resolve_is_comment_liked(self, info):
        """
        Check if current user liked this comment
        """
        user = info.context.user
        if user.is_anonymous:
            return False
        return Like.objects.filter(user=user, comment_id=self.id, is_active=True).exists()


class ArticleImageType(DjangoObjectType):
    """
    GraphQL ArticleImage type
    """
    image_url = graphene.String()
    
    class Meta:
        model = ArticleImage
        exclude = ['image']  # Exclude the CloudinaryField from auto-generation
    
    def resolve_image_url(self, info):
        """
        Resolve image URL
        """
        image_url = self.image_url  # Use the new property method
        return image_url or ""
        return ""


class LikeType(DjangoObjectType):
    """
    GraphQL Like type
    """
    class Meta:
        model = Like
        fields = '__all__'


class ReadingHistoryType(DjangoObjectType):
    """
    GraphQL ReadingHistory type
    """
    class Meta:
        model = ReadingHistory
        fields = '__all__'


class NewsletterSubscriptionType(DjangoObjectType):
    """
    GraphQL NewsletterSubscription type
    """
    class Meta:
        model = NewsletterSubscription
        fields = '__all__'


class Query(graphene.ObjectType):
    """
    API GraphQL Queries
    """
# Basic queries
    hello = graphene.String(name=graphene.String(default_value='World'))
    
    # User queries
    me = graphene.Field(UserType)
    users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.Int(required=True))
    user_profile = graphene.Field(UserProfileType, user_id=graphene.Int(required=True))
    
    # News queries
    news_list = graphene.List(NewsType, 
                             status=graphene.String(),
                             category_id=graphene.Int(),
                             author_id=graphene.Int(),
                             search=graphene.String(),
                             tag_id=graphene.Int())
    news_article = graphene.Field(NewsType, id=graphene.Int(), slug=graphene.String())
    published_news = graphene.List(NewsType,
                                  search=graphene.String(),
                                  category_id=graphene.Int(),
                                  tag_id=graphene.Int())

    articles_by_category = graphene.List(
        NewsType,
        category_id=graphene.Int(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0)
    )
    def resolve_articles_by_category(self, info, category_id, limit, offset):
        """
        Get articles filtered by category ID
        """
        return News.objects.filter(category_id=category_id, status='published').order_by('-published_at')[offset:offset + limit]

    articles_by_tag = graphene.List(
        NewsType,
        tag_id=graphene.Int(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0)
    )
    def resolve_articles_by_tag(self, info, tag_id, limit, offset):
        """
        Get articles filtered by tag ID
        """
        return News.objects.filter(tags__id=tag_id, status='published').order_by('-published_at')[offset:offset + limit]
    
    article_like_count = graphene.Int(
        article_id=graphene.Int(required=False)
    )
    def resolve_article_like_count(self, info, article_id=None):
        """
        Get total active like count for a specific article
        """
        if article_id is None:
            return 0
        return Like.objects.filter(article_id=article_id, is_active=True).count()
    article_comment_count = graphene.Int(
        article_id=graphene.Int(required=False)
    )
    def resolve_article_comment_count(self, info, article_id=None):
        """
        Count number of comments for a specific article
        """
        if article_id is None:
            return 0
        return Comment.objects.filter(article_id=article_id).count()
    has_read_article = graphene.Boolean(
        article_id=graphene.Int(required=True)
    )
    def resolve_has_read_article(self, info, article_id):
        """
        Return True if the user has a reading history entry for this article
        """
        user = info.context.user
        if user.is_anonymous:
            return False  # Guest users don't have reading history
        return ReadingHistory.objects.filter(user=user, article_id=article_id).exists()
    # Category and Tag queries
    categories = graphene.List(CategoryType)
    category = graphene.Field(CategoryType, id=graphene.Int())
    #Search category by key word
    search_categories = graphene.List(CategoryType, keyword=graphene.String(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),)
    def resolve_search_categories(self, info, keyword,limit, offset):
        """ Filter category name containing the keyword (case-insensitive) """
        return Category.objects.filter(name__icontains=keyword)[offset:offset + limit] 
    tags = graphene.List(TagType)

    #Search tag by key word
    search_tags = graphene.List(
        TagType,
        keyword=graphene.String(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),
    )
    def resolve_search_tags(self, info, keyword, limit, offset):
        """ Filter tag name containing the keyword (case-insensitive) """
        return Tag.objects.filter(name__icontains=keyword)[offset:offset + limit]
    # Comment queries
    article_comments = graphene.List(CommentType, article_id=graphene.Int(required=False))
    article_comments_with_replies = graphene.List(CommentType, article_id=graphene.Int(required=False))
    def resolve_article_comments_with_replies(self, info, article_id):
        """
        Get all comments for an article with nested replies (all levels)
        """
        try:
            # Get all comments for the article
            all_comments = Comment.objects.filter(article_id=article_id).select_related('author', 'author__profile', 'parent', 'parent__author', 'parent__author__profile')
            
            # Separate parent comments and replies
            parent_comments = []
            all_replies = {}
            
            for comment in all_comments:
                if comment.parent is None:
                    parent_comments.append(comment)
                else:
                    parent_id = comment.parent.id
                    if parent_id not in all_replies:
                        all_replies[parent_id] = []
                    all_replies[parent_id].append(comment)
            
            # Build nested structure
            def build_comment_tree(comment):
                comment_data = comment
                comment_data.nested_replies = all_replies.get(comment.id, [])
                
                # Recursively build replies
                for reply in comment_data.nested_replies:
                    build_comment_tree(reply)
                
                return comment_data
            
            # Build the tree for each parent comment
            result = []
            for parent in parent_comments:
                result.append(build_comment_tree(parent))
            
            return result
        except Exception as e:
            print(f"Error in resolve_article_comments_with_replies: {e}")
            return []
    # Search latest cmt by article id 
    latest_article_comments = graphene.List(
        CommentType, article_id=graphene.Int(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0)
    )
    def resolve_latest_article_comments(self, info, article_id,limit, offset):
        """Get comments for an article"""
        return Comment.objects.filter(article_id=article_id, parent__isnull=True).order_by('-created_at')[offset:offset + limit]
    
    # Search top cmt by article id
    top_liked_comments = graphene.List(
        CommentType,
        article_id=graphene.Int(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0)
    )
    def resolve_top_liked_comments(self, info, article_id, limit, offset):
        """
        Get top liked comments for an article (ordered by like_count descending)
        """
        return Comment.objects.filter(
        article_id=article_id,
        parent__isnull=True
        ).annotate(
            real_like_count=Count('likes', filter=Q(likes__is_active=True))
        ).order_by('-real_like_count', '-created_at')[offset:offset + limit]

    comment_like_count = graphene.Int(
        comment_id=graphene.Int(required=True)
    )

    def resolve_comment_like_count(self, info, comment_id):
        """
        Count the number of active likes for a specific comment
        """
        return Like.objects.filter(comment_id=comment_id, is_active=True).count()
    # Analytics queries
    user_reading_history = graphene.List(ReadingHistoryType, user_id=graphene.Int(required=True))
    
    # Dashboard queries
    dashboard_stats = graphene.Field(DashboardStatsType)
    recent_activity = graphene.List(RecentActivityType, limit=graphene.Int())

    # Like queries:
    is_article_liked = graphene.Boolean(article_id=graphene.Int(required=False))
    def resolve_is_article_liked(self, info, article_id=None):
        user = info.context.user
        if user.is_anonymous or article_id is None:
            return False
        return Like.objects.filter(user=user, article_id=article_id,is_active=True).exists()
    
    is_comment_liked = graphene.Boolean(comment_id=graphene.Int(required=False))
    def resolve_is_comment_liked(self, info, comment_id=None):
        user = info.context.user
        if user.is_anonymous or comment_id is None:
            return False
        return Like.objects.filter(user=user, comment_id=comment_id, is_active=True).exists()
    article_read_count = graphene.Int(
        article_id=graphene.Int(required=False)
    )
    def resolve_article_read_count(self, info, article_id=None):
        if article_id is None:
            return 0
        return ReadingHistory.objects.filter(article_id=article_id).values('user').distinct().count()
    
    def resolve_hello(self, info, name):
        """Simple hello world resolver"""
        return f'Hello {name}'
    
# User queries
    users = graphene.List(UserType)
    def resolve_users(self, info):
        """Get all users"""
        return User.objects.all()
    
    user = graphene.Field(UserType, id=graphene.Int(required=True))

    def resolve_user(self, info, id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=id)
        except User.DoesNotExist:
            return None
        
    user_profile = graphene.Field(UserProfileType, user_id=graphene.Int(required=True))
    def resolve_user_profile(self, info, user_id):
        """Get user profile by user ID"""
        try:
            return UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return None
    
# News queries
    news_list = graphene.List(NewsType, 
                             status=graphene.String(),
                             category_id=graphene.Int(),
                             author_id=graphene.Int())
    def resolve_news_list(self, info, status=None, category_id=None, author_id=None):
        """Get news articles with optional filters"""
        queryset = News.objects.all()
        
        if status:
            queryset = queryset.filter(status=status)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
            
        return queryset

    news_article = graphene.Field(NewsType, id=graphene.Int(), slug=graphene.String())
    def resolve_news_article(self, info, id=None, slug=None):
        """Get news article by ID or slug"""
        try:
            if id:
                return News.objects.get(pk=id)
            elif slug:
                return News.objects.get(slug=slug)
        except News.DoesNotExist:
            return None
        
    published_news = graphene.List(NewsType)
    def resolve_published_news(self, info):
        """Get published news articles"""
        return News.objects.filter(status='published').order_by('-published_at')    
    
    articles_by_category = graphene.List(
        NewsType,
        category_id=graphene.ID(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0)
    )
    def resolve_articles_by_category(self, info, category_id, limit, offset):
        """
        Get articles filtered by category ID
        """
        return News.objects.filter(category_id=category_id, status='published').order_by('-published_at')[offset:offset + limit]

    articles_by_tag = graphene.List(
        NewsType,
        tag_id=graphene.ID(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0)
    )
    def resolve_articles_by_tag(self, info, tag_id, limit, offset):
        """
        Get articles filtered by tag ID
        """
        return News.objects.filter(tags__id=tag_id, status='published').order_by('-published_at')[offset:offset + limit]
# Category queries
    categories = graphene.List(CategoryType)
    def resolve_categories(self, info):
        """Get all categories"""
        return Category.objects.filter(is_active=True)
    
    category = graphene.Field(CategoryType, id=graphene.Int())
    def resolve_category(self, info, id):
        """Get category by ID"""
        try:
            return Category.objects.get(pk=id)
        except Category.DoesNotExist:
            return None
        
    #Search category by key word
    search_categories = graphene.List(CategoryType, keyword=graphene.String(required=True))
    def resolve_search_categories(self, info, keyword):
        """ Filter category name containing the keyword (case-insensitive) """
        return Category.objects.filter(name__icontains=keyword)[:10]  # Limit to 10 results

# Tag queries
    tags = graphene.List(TagType)
    def resolve_tags(self, info):
        """Get all tags"""
        return Tag.objects.all()

    def resolve_article_comments(self, info, article_id=None):
        """Get comments for an article"""
        if article_id is None:
            return []
        return Comment.objects.filter(article_id=article_id)

    def resolve_user_reading_history(self, info, user_id):
        """Get user's reading history"""
        return ReadingHistory.objects.filter(user_id=user_id)
     
# Like queries:
    is_article_liked = graphene.Boolean(article_id=graphene.ID(required=True))
    def resolve_is_article_liked(self, info, article_id):
        """Check user liked article"""
        user = info.context.user
        if user.is_anonymous:
            return False
        return Like.objects.filter(user=user, article_id=article_id).exists()
    
    is_comment_liked = graphene.Boolean(comment_id=graphene.ID(required=True))
    def resolve_is_comment_liked(self, info, comment_id):
        """Check user liked comment"""
        user = info.context.user
        if not user.is_authenticated:
            return []
            
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['admin', 'manager']:
                return []
        except UserProfile.DoesNotExist:
            return []
        
        # Get recent news as activity
        recent_news = News.objects.select_related('author').order_by('-created_at')[:limit]
        
        activities = []
        for news in recent_news:
            activities.append(RecentActivityType(
                id=news.id,
                action='news_created',
                description=f'New article "{news.title}" was created',
                timestamp=news.created_at,
                user=news.author
            ))
        
        return activities


    # ...existing code...
    
class CreateUser(graphene.Mutation):
    """
    Create a new user with profile
    """
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        avatar = graphene.String()  # Cloudinary URL or base64 image data

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, username, email, password, first_name=None, last_name=None, avatar=None):
        """
        Create user mutation with profile creation
        """
        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                return CreateUser(success=False, errors=['Username already exists'])
            
            if User.objects.filter(email=email).exists():
                return CreateUser(success=False, errors=['Email already exists'])

            # Create new user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name or '',
                last_name=last_name or ''
            )
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                role='reader',
                is_verified=False
            )
            
            # Handle avatar if provided
            if avatar:
                try:
                    # If avatar is a Cloudinary URL, save it directly
                    if avatar.startswith('http'):
                        profile.avatar = avatar
                        profile.save()
                except Exception:
                    # If avatar processing fails, continue without avatar
                    pass
            
            return CreateUser(user=user, success=True, errors=[])
        
        except Exception as e:
            return CreateUser(success=False, errors=[str(e)])


class UpdateUserProfile(graphene.Mutation):
    """
    Update user profile
    """
    class Arguments:
        bio = graphene.String()
        phone = graphene.String()
        date_of_birth = graphene.Date()
        avatar = graphene.String()  # Cloudinary URL

    profile = graphene.Field(UserProfileType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, bio=None, phone=None, date_of_birth=None, avatar=None):
        """
        Update user profile mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return UpdateUserProfile(success=False, errors=['Authentication required'])

        try:
            profile = UserProfile.objects.get(user=user)
            
            if bio is not None:
                profile.bio = bio
            if phone is not None:
                profile.phone = phone
            if date_of_birth is not None:
                profile.date_of_birth = date_of_birth
            if avatar is not None:
                profile.avatar = avatar
                
            profile.save()
            
            return UpdateUserProfile(profile=profile, success=True, errors=[])
        
        except UserProfile.DoesNotExist:
            return UpdateUserProfile(success=False, errors=['Profile not found'])
        except Exception as e:
            return UpdateUserProfile(success=False, errors=[str(e)])


class CreateNews(graphene.Mutation):
    """
    Create a new news article (for writers)
    """
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        excerpt = graphene.String(required=True)
        category_id = graphene.Int(required=True)
        tag_ids = graphene.List(graphene.Int)
        featured_image = graphene.String()  # Cloudinary URL
        meta_description = graphene.String()
        meta_keywords = graphene.String()

    news = graphene.Field(NewsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, content, excerpt, category_id, tag_ids=None, 
               featured_image=None, meta_description=None, meta_keywords=None):
        """
        Create news article mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return CreateNews(success=False, errors=['Authentication required'])

        try:
            # Check if user has writer role or higher
            profile = UserProfile.objects.get(user=user)
            if profile.role not in ['writer', 'manager', 'admin']:
                return CreateNews(success=False, errors=['Permission denied. Writer role required.'])

            # Check if category exists
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                return CreateNews(success=False, errors=['Category not found'])

            # Create slug from title
            from django.utils.text import slugify
            slug = slugify(title)
            
            # Ensure slug is unique
            counter = 1
            original_slug = slug
            while News.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1

            # Create news article
            news = News.objects.create(
                title=title,
                slug=slug,
                content=content,
                excerpt=excerpt,
                author=user,
                category=category,
                featured_image=featured_image or '',
                meta_description=meta_description or '',
                meta_keywords=meta_keywords or '',
                status='draft'  # Default to draft
            )

            # Add tags if provided
            if tag_ids:
                tags = Tag.objects.filter(id__in=tag_ids)
                news.tags.set(tags)

            return CreateNews(news=news, success=True, errors=[])

        except UserProfile.DoesNotExist:
            return CreateNews(success=False, errors=['User profile not found'])
        except Exception as e:
            return CreateNews(success=False, errors=[str(e)])
        
class CreateCategory(graphene.Mutation):
    """
    Create a new category
    """

    class Arguments:
        name = graphene.String(required=True)
        slug = graphene.String(required=True)
        description = graphene.String(required=True)
    category = graphene.Field(CategoryType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, name, slug, description=""):
        try:
            # Check name and slug existed
            if Category.objects.filter(slug=slug).exists():
                return CreateCategory(success=False, errors="Slug already exists.", category=None)
            if Category.objects.filter(name=name).exists():
                return CreateCategory(success=False, errors="Name already exists.", category=None)

            # Create new Category
            
            category = Category.objects.create(
                name=name,
                slug=slug,
                description=description,
            )
            return CreateCategory(category = category, success=True, errors="Category created successfully.")
        except Exception as e:
            return CreateCategory(success=False, errors="Unexpected error: " + str(e), category=None)

class UpdateCategory(graphene.Mutation):
    """
    Update an existing category's name, or description
    """

    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String(required=False)
        description = graphene.String(required=False)

    success = graphene.Boolean()
    errors = graphene.String()
    category = graphene.Field(CategoryType)

    def mutate(self, info, id, name=None, description=None):
        try:
            category = Category.objects.get(id=id)

            # Check for unique name and slug if being updated
            if name and name != category.name:
                if Category.objects.filter(name=name).exclude(id=id).exists():
                    return UpdateCategory(success=False, errors="Name already exists.", category=None)
                category.name = name

            if description is not None:
                category.description = description

            category.save()
            return UpdateCategory(success=True, errors="Category updated successfully.", category=category)

        except Category.DoesNotExist:
            return UpdateCategory(success=False, errors="Category not found.", category=None)
        except Exception as e:
            return UpdateCategory(success=False, errors="Unexpected error: " + str(e), category=None)
        
class DeleteCategory(graphene.Mutation):
    """
    Soft delete a category by setting is_active=False
    """

    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    errors = graphene.String()
    category = graphene.Field(CategoryType)

    def mutate(self, info, id):
        try:
            # Try to find the category
            category = Category.objects.get(id=id)

            # Check if already inactive
            if not category.is_active:
                return DeleteCategory(success=False, errors="Category is already inactive.", category=None)

            # Soft delete by setting is_active to False
            category.is_active = False
            category.save()

            return DeleteCategory(success=True, errors="Category deactivated successfully.", category=category)

        except Category.DoesNotExist:
            return DeleteCategory(success=False, errors="Category not found.", category=None)

        except Exception as e:
            return DeleteCategory(success=False, errors="Unexpected error: " + str(e), category=None)
                
class CreateTag(graphene.Mutation):
    """
    Create a new tag
    """

    class Arguments:
        name = graphene.String(required=True)
        slug = graphene.String(required=True)
    tag = graphene.Field(TagType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, name, slug, description=""):
        try:
            # Check name and slug existed
            if Tag.objects.filter(slug=slug).exists():
                return CreateTag(success=False, errors="Slug already exists.", tag=None)
            if Tag.objects.filter(name=name).exists():
                return CreateTag(success=False, errors="Name already exists.", tag=None)

            # Create new Tag
            
            tag = Tag.objects.create(
                name=name,
                slug=slug,
            )
            return CreateTag(tag = tag, success=True, errors="Tag created successfully.")
        except Exception as e:
            return CreateTag(success=False, errors="Unexpected error: " + str(e), tag=None)

class UpdateTag(graphene.Mutation):
    """
    Update an existing tag's name
    """

    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String(required=False)

    success = graphene.Boolean()
    errors = graphene.String()
    tag = graphene.Field(TagType)

    def mutate(self, info, id, name=None):
        try:
            tag = Tag.objects.get(id=id)

            # Check for unique name and slug if being updated
            if name and name != tag.name:
                if Category.objects.filter(name=name).exclude(id=id).exists():
                    return UpdateTag(success=False, errors="Name already exists.", tag=None)
                tag.name = name

            tag.save()
            return UpdateTag(success=True, errors="Tag updated successfully.", tag=tag)

        except Tag.DoesNotExist:
            return UpdateTag(success=False, errors="Tag not found.", tag=None)
        except Tag as e:
            return UpdateTag(success=False, errors="Unexpected error: " + str(e), tag=None)
        
class DeleteTag(graphene.Mutation):
    """
    Soft delete a tag by setting is_active=False
    """

    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    errors = graphene.String()
    tag = graphene.Field(TagType)

    def mutate(self, info, id):
        try:
            # Try to find the tag
            tag = Tag.objects.get(id=id)

            # Check if already inactive
            if not tag.is_active:
                return DeleteTag(success=False, errors="Tag is already inactive.", tag=None)

            # Soft delete by setting is_active to False
            tag.is_active = False
            tag.save()

            return DeleteTag(success=True, errors="Tag deactivated successfully.", tag=tag)

        except Tag.DoesNotExist:
            return DeleteTag(success=False, errors="Tag not found.", tag=None)

        except Exception as e:
            return DeleteTag(success=False, errors="Unexpected error: " + str(e), tag=None)
                
class CreateComment(graphene.Mutation):
    """
    Create a new comment
    """

    class Arguments:
        article_id = graphene.Int(required=True)
        content = graphene.String(required=True)
        parent_id = graphene.Int(required=False)

    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, article_id, content, parent_id=None):
        try:
            user = info.context.user

            # Check user authentication
            if user.is_anonymous:
                return CreateComment(success=False, errors="Authentication required.", comment=None)

            # Check if the article exists
            try:
                article = News.objects.get(pk=article_id)
            except News.DoesNotExist:
                return CreateComment(success=False, errors="Article not found.", comment=None)

            # Check if parent comment exists, if provided
            parent = None
            if parent_id:
                try:
                    parent = Comment.objects.get(pk=parent_id, article=article)
                except Comment.DoesNotExist:
                    return CreateComment(success=False, errors="Parent comment not found.", comment=None)

            # Create new comment
            comment = Comment.objects.create(
                article=article,
                author=user,
                content=content,
                parent=parent,
            )

            return CreateComment(comment=comment, success=True, errors="Comment created successfully.")

        except Exception as e:
            return CreateComment(success=False, errors="Unexpected error: " + str(e), comment=None)

class CreateLikeArticle(graphene.Mutation):
    """
    Like a news article by the authenticated user
    """

    success = graphene.Boolean()
    errors = graphene.String()

    class Arguments:
        article_id = graphene.ID(required=True)

    def mutate(self, info, article_id):
        try:
            user = info.context.user

            # Check user authentication
            if user.is_anonymous:
                return CreateLikeArticle(success=False, errors="Authentication required.")

            # Check if the article exists
            try:
                article = News.objects.get(pk=article_id)
            except News.DoesNotExist:
                return CreateLikeArticle(success=False, errors="Article not found.")

            # Check if already liked
            if Like.objects.filter(user=user, article=article).exists():
                return CreateLikeArticle(success=False, errors="You already liked this article.")

            # Create like
            Like.objects.create(user=user, article=article)

            return CreateLikeArticle(success=True, errors="Article liked successfully.")

        except Exception as e:
            return CreateLikeArticle(success=False, errors="Unexpected error: " + str(e))

class CreateLikeComment(graphene.Mutation):
    """
    Like a comment by the authenticated user
    """

    success = graphene.Boolean()
    errors = graphene.String()

    class Arguments:
        comment_id = graphene.ID(required=True)

    def mutate(self, info, comment_id):
        try:
            user = info.context.user

            # Check user authentication
            if user.is_anonymous:
                return CreateLikeComment(success=False, errors="Authentication required.")

            # Check if comment exists
            try:
                comment = Comment.objects.get(pk=comment_id)
            except Comment.DoesNotExist:
                return CreateLikeComment(success=False, errors="Comment not found.")

            # Check if already liked
            if Like.objects.filter(user=user, comment=comment).exists():
                return CreateLikeComment(success=False, errors="You already liked this comment.")

            # Create like
            Like.objects.create(user=user, comment=comment)

            return CreateLikeComment(success=True, errors="Comment liked successfully.")

        except Exception as e:
            return CreateLikeComment(success=False, errors="Unexpected error: " + str(e))

class UpdateLikeStatus(graphene.Mutation):
    """
    Deactivate (cancel) an existing like by setting is_active=False
    """

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, base64_data, folder="newsor/uploads", max_width=800, max_height=600, quality="auto", format="auto"):
        """
        Process base64 image and upload to Cloudinary
        """
        try:
            # Remove data URL prefix if present
            if base64_data.startswith('data:image'):
                base64_data = base64_data.split(',')[1]
            
            # Decode base64 data
            try:
                image_data = base64.b64decode(base64_data)
            except Exception as e:
                return UploadBase64Image(success=False, errors=[f"Invalid base64 data: {str(e)}"])
            
            # Open image with PIL
            try:
                image = Image.open(io.BytesIO(image_data))
            except Exception as e:
                return UploadBase64Image(success=False, errors=[f"Invalid image data: {str(e)}"])
            
            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            
            # Resize image if needed
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Generate unique filename
            unique_filename = f"upload_{uuid.uuid4().hex}"
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                output.getvalue(),
                public_id=unique_filename,
                folder=folder,
                transformation=[
                    {'quality': quality},
                    {'fetch_format': format}
                ],
                resource_type="image"
            )
            
            # Optimize URL for storage
            optimized_url = CloudinaryUtils.optimize_for_storage(upload_result['secure_url'])
            
            return UploadBase64Image(
                url=optimized_url,
                public_id=upload_result['public_id'],
                success=True,
                errors=[]
            )
            
        except Exception as e:
            return UploadBase64Image(success=False, errors=[f"Upload failed: {str(e)}"])


class UploadAvatarImage(graphene.Mutation):
    """
    Upload and set avatar image for user profile
    """
    class Arguments:
        base64_data = graphene.String(required=True, description="Base64 encoded avatar image")

    profile = graphene.Field(UserProfileType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, base64_data):
        """
        Upload avatar and update user profile
        """
        user = info.context.user
        if not user.is_authenticated:
            return UploadAvatarImage(success=False, errors=['Authentication required'])

        try:
            # Upload the image with avatar-specific settings
            upload_mutation = UploadBase64Image()
            upload_result = upload_mutation.mutate(
                info, 
                base64_data=base64_data,
                folder="newsor/avatars",
                max_width=400,
                max_height=400,
                quality="auto",
                format="auto"
            )
            
            if not upload_result.success:
                return UploadAvatarImage(success=False, errors=upload_result.errors)
            
            # Update user profile with new avatar
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.avatar = upload_result.url
            profile.save()
            
            return UploadAvatarImage(profile=profile, success=True, errors=[])
            
        except Exception as e:
            return UploadAvatarImage(success=False, errors=[f"Avatar upload failed: {str(e)}"])

class CreateLikeArticle(graphene.Mutation):
    """
    Like a news article by the authenticated user
    """

    success = graphene.Boolean()
    errors = graphene.String()

    class Arguments:
        article_id = graphene.Int(required=True)

    def mutate(self, info, article_id):
        try:
            user = info.context.user

            # Check user authentication
            if user.is_anonymous:
                return CreateLikeArticle(success=False, errors="Authentication required.")

            # Check if the article exists
            try:
                article = News.objects.get(pk=article_id)
            except News.DoesNotExist:
                return CreateLikeArticle(success=False, errors="Article not found.")

            # Check if already liked
            if Like.objects.filter(user=user, article=article).exists():
                return CreateLikeArticle(success=False, errors="You already liked this article.")

            # Create like
            Like.objects.create(user=user, article=article)

            return CreateLikeArticle(success=True, errors="Article liked successfully.")

        except Exception as e:
            return CreateLikeArticle(success=False, errors="Unexpected error: " + str(e))

class CreateLikeComment(graphene.Mutation):
    """
    Like a comment by the authenticated user
    """

    success = graphene.Boolean()
    errors = graphene.String()

    class Arguments:
        comment_id = graphene.Int(required=True)

    def mutate(self, info, comment_id):
        try:
            user = info.context.user

            # Check user authentication
            if user.is_anonymous:
                return CreateLikeComment(success=False, errors="Authentication required.")

            # Check if comment exists
            try:
                comment = Comment.objects.get(pk=comment_id)
            except Comment.DoesNotExist:
                return CreateLikeComment(success=False, errors="Comment not found.")

            # Check if already liked
            if Like.objects.filter(user=user, comment=comment).exists():
                return CreateLikeComment(success=False, errors="You already liked this comment.")

            # Create like
            Like.objects.create(user=user, comment=comment)

            return CreateLikeComment(success=True, errors="Comment liked successfully.")

        except Exception as e:
            return CreateLikeComment(success=False, errors="Unexpected error: " + str(e))

class UpdateLikeStatus(graphene.Mutation):
    """
    Toggle the like status for an article or comment.
    If like does not exist, it will be created and set to active.
    If it exists and is_active=True, it will be deactivated.
    If it exists and is_active=False, it will be reactivated.
    """

    success = graphene.Boolean()
    errors = graphene.String()
    is_active = graphene.Boolean()  # Current state after toggle

    class Arguments:
        article_id = graphene.Int(required=False)
        comment_id = graphene.Int(required=False)

    def mutate(self, info, article_id=None, comment_id=None):
        user = info.context.user
        if user.is_anonymous:
            return UpdateLikeStatus(success=False, errors="Authentication required.", is_active=None)

        if not article_id and not comment_id:
            return UpdateLikeStatus(success=False, errors="You must provide article_id or comment_id.", is_active=None)

        from .models import Like

        try:
            like_filter = {"user": user}
            if article_id:
                like_filter["article_id"] = article_id
            if comment_id:
                like_filter["comment_id"] = comment_id

            like, created = Like.objects.get_or_create(**like_filter)

            # Toggle the status
            if not created:
                like.is_active = not like.is_active
            else:
                like.is_active = True

            like.save()

            return UpdateLikeStatus(success=True, errors=None, is_active=like.is_active)

        except Exception as e:
            return UpdateLikeStatus(success=False, errors="Unexpected error: " + str(e), is_active=None)
        
class CreateReadingHistory(graphene.Mutation):
    """
    Record a user's article reading history
    """
    class Arguments:
        article_id = graphene.Int(required=True)
        ip_address = graphene.String(required=False)
        user_agent = graphene.String(required=False)
    success = graphene.Boolean()
    errors = graphene.String()    

    def mutate(self, info, article_id, ip_address=None, user_agent=None):
        try:
            user = info.context.user

            # Ensure user is authenticated
            if user.is_anonymous:
                return CreateReadingHistory(success=False, errors="Authentication required.")

            # Check if article exists
            try:
                article = News.objects.get(pk=article_id)
            except News.DoesNotExist:
                return CreateReadingHistory(success=False, errors="Article not found.")

            # Create reading history record
            ReadingHistory.objects.create(
                user=user,
                article=article,
                ip_address=ip_address or info.context.META.get("REMOTE_ADDR", ""),
                user_agent=user_agent or info.context.META.get("HTTP_USER_AGENT", ""),
            )

            return CreateReadingHistory(success=True, errors="Reading history recorded.")

        except Exception as e:
            return CreateReadingHistory(success=False, errors="Unexpected error: " + str(e))


# ...existing mutations...

class Mutation(graphene.ObjectType):
    """
    API GraphQL Mutations
    """
    create_user = CreateUser.Field()
    update_user_profile = UpdateUserProfile.Field()
    create_news = CreateNews.Field()
    create_category = CreateCategory.Field()
    create_tag = CreateTag.Field()
    create_comment = CreateComment.Field()
    change_user_role = ChangeUserRole.Field()
    get_cloudinary_signature = GetCloudinarySignature.Field()
    upload_base64_image = UploadBase64Image.Field()
    upload_avatar_image = UploadAvatarImage.Field()
    create_like_article = CreateLikeArticle.Field()
    create_like_comment = CreateLikeComment.Field()
    update_like_status = UpdateLikeStatus.Field()
    update_category = UpdateCategory.Field()
    delete_category = DeleteCategory.Field()
    update_tag = UpdateTag.Field()
    delete_tag = DeleteTag.Field()
    create_readinghistory = CreateReadingHistory.Field()
