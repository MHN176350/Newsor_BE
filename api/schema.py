# --- News Delete Mutation ---
import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from .models import (
    Category, Tag, UserProfile, News, Comment, 
    Like, ReadingHistory, NewsletterSubscription, ArticleImage, Notification, Contact, EmailTemplate
)
from .utils import sanitize_html_content, get_cloudinary_upload_signature
import base64
import io
from PIL import Image
import cloudinary.uploader
import uuid
from .cloudinary_utils import CloudinaryUtils
from django.db.models import Count, Q


class DeleteNews(graphene.Mutation):
    """
    Delete a news article (for managers/admins, or the article's author if draft/archived)
    """
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            return DeleteNews(success=False, errors=["Authentication required"])

        try:
            # Get the article
            try:
                news = News.objects.get(id=id)
            except News.DoesNotExist:
                return DeleteNews(success=False, errors=["Article not found"]) 

            # Only allow delete if:
            # - user is admin/manager, or
            # - user is the author and article is draft/archived
            profile = UserProfile.objects.get(user=user)
            user_role = profile.role.lower()
            if user_role in ["admin", "manager"]:
                pass  # can delete any
            elif news.author.id == user.id and news.status.lower() in ["draft", "archived"]:
                pass  # can delete own draft/archived
            else:
                return DeleteNews(success=False, errors=["Permission denied. Only admins, managers, or the article's author (if draft/archived) can delete."])

            news.delete()
            return DeleteNews(success=True, errors=[])

        except UserProfile.DoesNotExist:
            return DeleteNews(success=False, errors=["User profile not found"])
        except Exception as e:
            return DeleteNews(success=False, errors=[str(e)])


class UserType(DjangoObjectType):
    """
    GraphQL User type
    """
    profile = graphene.Field(lambda: UserProfileType)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'last_login')

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
    article_count = graphene.Int()
    
    class Meta:
        model = Category
        fields = '__all__'
    
    def resolve_article_count(self, info):
        """
        Resolve the number of published articles in this category
        """
        return self.articles.filter(status='published').count()


class TagType(DjangoObjectType):
    """
    GraphQL Tag type
    """
    article_count = graphene.Int()
    
    class Meta:
        model = Tag
        fields = '__all__'
    
    def resolve_article_count(self, info):
        """
        Resolve the number of published articles with this tag
        """
        return self.articles.filter(status='published').count()


class UserProfileType(DjangoObjectType):
    """
    GraphQL UserProfile type
    """
    avatar_url = graphene.String()  # Custom field for avatar URL
    has_write_permission = graphene.Boolean()
    has_admin_permission = graphene.Boolean()
    has_manager_permission = graphene.Boolean()
    
    class Meta:
        model = UserProfile
        exclude = ['avatar']  # Exclude the CloudinaryField from auto-generation
    
    def resolve_avatar_url(self, info):
        """
        Resolve avatar URL with fallback to default image
        """
        avatar_url = self.avatar_url  # Use the new property method
        if avatar_url:
            return avatar_url
        else:
            # Return default avatar if no avatar is set
            return "/static/images/default-avatar.svg"
    
    def resolve_has_write_permission(self, info):
        """Check if user has write permission"""
        return self.role.lower() in ['writer', 'manager', 'admin']
    
    def resolve_has_admin_permission(self, info):
        """Check if user has admin permission"""
        return self.role.lower() == 'admin'
    
    def resolve_has_manager_permission(self, info):
        """Check if user has manager permission"""
        return self.role.lower() in ['manager', 'admin']


class NewsType(DjangoObjectType):
    """
    GraphQL News type
    """
    featured_image_url = graphene.String()  # Custom field for featured image URL
    likes_count = graphene.Int()
    comments_count = graphene.Int()
    read_count = graphene.Int()
    is_liked_by_user = graphene.Boolean()
    
    class Meta:
        model = News
        exclude = ['featured_image']  # Exclude the CloudinaryField from auto-generation
    
    def resolve_featured_image_url(self, info):
        """
        Resolve featured image URL with fallback to default image
        """
        featured_image_url = self.featured_image_url  # Use the new property method
        if featured_image_url:
            return featured_image_url
        else:
            # Return default news image if no image is set
            return "/static/images/default-news.svg"
    
    def resolve_likes_count(self, info):
        """
        Get the number of likes for this article
        """
        return self.likes.count()
    
    def resolve_comments_count(self, info):
        """
        Get the number of comments for this article
        """
        return self.comments.count()
    
    def resolve_read_count(self, info):
        """
        Get the read count (view count) for this article
        """
        return self.view_count
    
    def resolve_is_liked_by_user(self, info):
        """
        Check if the current user has liked this article
        """
        user = info.context.user
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()


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


class NotificationType(DjangoObjectType):
    """
    GraphQL Notification type
    """
    class Meta:
        model = Notification
        fields = '__all__'


class ContactType(DjangoObjectType):
    """
    GraphQL Contact type
    """
    class Meta:
        model = Contact
        fields = '__all__'


class EmailTemplateType(DjangoObjectType):
    """
    GraphQL Email Template type
    """
    class Meta:
        model = EmailTemplate
        fields = '__all__'


# Contact Connection for pagination
class ContactConnection(graphene.relay.Connection):
    class Meta:
        node = ContactType
    
    total_count = graphene.Int()
    
    def resolve_total_count(self, info):
        return Contact.objects.count()


class DashboardStatsType(graphene.ObjectType):
    """
    Dashboard statistics type
    """
    # User statistics
    total_users = graphene.Int()
    total_readers = graphene.Int()
    total_writers = graphene.Int()
    total_managers = graphene.Int()
    total_admins = graphene.Int()
    new_users_this_month = graphene.Int()
    
    # News statistics
    total_news = graphene.Int()
    published_news = graphene.Int()
    draft_news = graphene.Int()
    pending_news = graphene.Int()
    rejected_news = graphene.Int()
    news_this_month = graphene.Int()
    
    # Category and Tag statistics
    total_categories = graphene.Int()
    total_tags = graphene.Int()
    
    # Activity statistics
    total_views = graphene.Int()
    total_likes = graphene.Int()
    total_comments = graphene.Int()


class RecentActivityType(graphene.ObjectType):
    """
    Recent activity type
    """
    id = graphene.ID()
    action = graphene.String()
    description = graphene.String()
    timestamp = graphene.DateTime()
    user = graphene.Field(UserType)


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
    user_comment_history = graphene.List(
        CommentType,
        user_id=graphene.Int(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),
        from_date=graphene.Date(required=False),
        to_date=graphene.Date(required=False)
    )
    def resolve_user_comment_history(self, info, user_id, limit, offset, from_date=None, to_date=None):
        qs = Comment.objects.filter(author_id=user_id)

        if from_date:
            qs = qs.filter(created_at__date__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__date__lte=to_date)

        return qs.order_by('-created_at')[offset:offset + limit]
        
    user_reading_history = graphene.List(
        ReadingHistoryType,
        user_id=graphene.Int(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),
        from_date=graphene.Date(required=False),
        to_date=graphene.Date(required=False)
    )
    def resolve_user_reading_history(self, info, user_id, limit, offset, from_date=None, to_date=None):
        qs = ReadingHistory.objects.filter(user_id=user_id)

        if from_date:
            qs = qs.filter(read_at__date__gte=from_date)
        if to_date:
            qs = qs.filter(read_at__date__lte=to_date)

        return qs.order_by('-read_at')[offset:offset + limit]

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
    news_for_review = graphene.List(NewsType)
    my_news = graphene.List(NewsType)
    ##############################################  add
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
    ####################################################
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
    admin_tags = graphene.List(TagType)  # Admin-only query to get all tags including inactive
    ######################################### add
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
    ############################################
    # Comment queries
    article_comments = graphene.List(CommentType, article_id=graphene.Int(required=False))
   
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
    # # Analytics queries
    # user_reading_history = graphene.List(ReadingHistoryType, user_id=graphene.Int(required=True))
    
    # Dashboard queries
    dashboard_stats = graphene.Field(DashboardStatsType)
    recent_activity = graphene.List(RecentActivityType, limit=graphene.Int())
    
    # Notification queries
    notifications = graphene.List(NotificationType)
    unread_notifications = graphene.List(NotificationType)
    notification_count = graphene.Int()
    
    # Contact queries
    contacts = graphene.relay.ConnectionField(
        'api.schema.ContactConnection',
        first=graphene.Int(),
        after=graphene.String()
    )
    email_template = graphene.Field(
        EmailTemplateType,
        name=graphene.String(required=True)
    )
    email_templates = graphene.List(
        EmailTemplateType,
        template_type=graphene.String()
    )
    

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
    
    def resolve_me(self, info):
        """Get current authenticated user"""
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

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

    def resolve_news_list(self, info, status=None, category_id=None, author_id=None, search=None, tag_id=None):
        """Get news articles with optional filters"""
        from django.db.models import Q
        
        queryset = News.objects.all()
        
        if status:
            queryset = queryset.filter(status=status)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(excerpt__icontains=search) |
                Q(meta_keywords__icontains=search)
            )
            
        return queryset.distinct().order_by('-created_at')

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
    def resolve_published_news(self, info, search=None, category_id=None, tag_id=None):
        """Get published news articles with optional filters"""
        from django.db.models import Q
        
        queryset = News.objects.filter(status='published')
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(excerpt__icontains=search) |
                Q(meta_keywords__icontains=search)
            )
            
        return queryset.distinct().order_by('-published_at')
    
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
        """Get all active tags for public use"""
        # For admin users, show all tags. For others, show only active tags
        user = info.context.user
        if user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=user)
                if profile.role.lower() == 'admin':
                    return Tag.objects.all()
            except UserProfile.DoesNotExist:
                pass
        
        # For non-admin users, return only active tags
        return Tag.objects.filter(is_active=True)

    def resolve_admin_tags(self, info):
        """Get all tags for admin management (admin only)"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() != 'admin':
                return []
        except UserProfile.DoesNotExist:
            return []
        
        return Tag.objects.all()

    def resolve_news_for_review(self, info):
        """Get news articles that need review (for managers)"""
        # Only allow managers and admins to access this
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['manager', 'admin']:
                return []
        except UserProfile.DoesNotExist:
            return []
        
        # Return articles that are in draft or pending status
        return News.objects.filter(status__in=['draft', 'pending']).order_by('-created_at')

    def resolve_my_news(self, info):
        """Get current user's news articles"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Return all articles by the current user
        return News.objects.filter(author=user).order_by('-created_at')

    def resolve_article_comments(self, info, article_id=None):
        """Get comments for an article"""
        if article_id is None:
            return []
        return Comment.objects.filter(article_id=article_id)

    # def resolve_user_reading_history(self, info, user_id):
    #     """Get user's reading history"""
    #     return ReadingHistory.objects.filter(user_id=user_id)
         
    def resolve_dashboard_stats(self, info):
        """Get dashboard statistics"""
        from datetime import datetime
        from django.db.models import Count, Sum
        
        # Check if user is admin or manager
        user = info.context.user
        if not user.is_authenticated:
            return None
            
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['admin', 'manager']:
                return None
        except UserProfile.DoesNotExist:
            return None
        
        # Calculate statistics
        current_month = datetime.now().replace(day=1)
        
        # User statistics
        total_users = User.objects.count()
        user_roles = UserProfile.objects.values('role').annotate(count=Count('role'))
        role_counts = {role['role']: role['count'] for role in user_roles}
        
        new_users_this_month = User.objects.filter(date_joined__gte=current_month).count()
        
        # News statistics
        news_stats = News.objects.values('status').annotate(count=Count('status'))
        status_counts = {stat['status']: stat['count'] for stat in news_stats}
        
        news_this_month = News.objects.filter(created_at__gte=current_month).count()
        
        # Category and Tag statistics
        total_categories = Category.objects.filter(is_active=True).count()
        total_tags = Tag.objects.count()
        
        # Activity statistics (using model fields)
        total_views = News.objects.aggregate(total=Sum('view_count'))['total'] or 0
        total_likes = News.objects.aggregate(total=Sum('like_count'))['total'] or 0
        total_comments = Comment.objects.count() if hasattr(Comment, 'objects') else 0
        
        return DashboardStatsType(
            # User statistics
            total_users=total_users,
            total_readers=role_counts.get('reader', 0),
            total_writers=role_counts.get('writer', 0),
            total_managers=role_counts.get('manager', 0),
            total_admins=role_counts.get('admin', 0),
            new_users_this_month=new_users_this_month,
            
            # News statistics
            total_news=News.objects.count(),
            published_news=status_counts.get('published', 0),
            draft_news=status_counts.get('draft', 0),
            pending_news=status_counts.get('pending', 0),
            rejected_news=status_counts.get('rejected', 0),
            news_this_month=news_this_month,
            
            # Category and Tag statistics
            total_categories=total_categories,
            total_tags=total_tags,
            
            # Activity statistics
            total_views=total_views,
            total_likes=total_likes,
            total_comments=total_comments,
        )
    
    def resolve_recent_activity(self, info, limit=10):
        """Get recent activity"""
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

    def resolve_notifications(self, info):
        """Get all notifications for the current user"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        return Notification.objects.filter(
            recipient=user
        ).select_related('sender', 'article').order_by('-created_at')

    def resolve_unread_notifications(self, info):
        """Get unread notifications for the current user"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).select_related('sender', 'article').order_by('-created_at')

    def resolve_notification_count(self, info):
        """Get count of unread notifications for the current user"""
        user = info.context.user
        if not user.is_authenticated:
            return 0
        
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()

    def resolve_contacts(self, info, **kwargs):
        """
        Get all contacts (admin/manager only)
        """
        user = info.context.user
        if not user.is_authenticated:
            return Contact.objects.none()
        
        try:
            profile = UserProfile.objects.get(user=user)
            user_role = profile.role.lower()
            if user_role not in ["admin", "manager"]:
                return Contact.objects.none()
        except UserProfile.DoesNotExist:
            return Contact.objects.none()
        
        return Contact.objects.all().order_by('-created_at')
    
    def resolve_email_template(self, info, name):
        """
        Get email template by name
        """
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            profile = UserProfile.objects.get(user=user)
            user_role = profile.role.lower()
            if user_role not in ["admin", "manager"]:
                return None
        except UserProfile.DoesNotExist:
            return None
        
        try:
            return EmailTemplate.objects.get(name=name)
        except EmailTemplate.DoesNotExist:
            # Return default template if not found
            return EmailTemplate(
                name=name,
                subject="Thank you for contacting us",
                content="Dear {{name}},\n\nThank you for contacting us regarding {{request_service}}. We have received your message and will get back to you soon.\n\nBest regards,\nEvoluSoft Team",
                variables=['name', 'request_service', 'request_content']
            )

    def resolve_email_templates(self, info, template_type=None):
        """
        Get all email templates, optionally filtered by type
        """
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            profile = UserProfile.objects.get(user=user)
            user_role = profile.role.lower()
            if user_role not in ["admin", "manager"]:
                return []
        except UserProfile.DoesNotExist:
            return []
        
        if template_type:
            return EmailTemplate.objects.filter(template_type=template_type, is_active=True)
        return EmailTemplate.objects.filter(is_active=True)

    # ...existing code...
    # Like queries:
    # is_article_liked = graphene.Boolean(article_id=graphene.ID(required=True))  ########### add
    # def resolve_is_article_liked(self, info, article_id):
    #     """Check user liked article"""
    #     user = info.context.user
    #     if user.is_anonymous:
    #         return False
    #     return Like.objects.filter(user=user, article_id=article_id).exists()
    
    is_comment_liked = graphene.Boolean(comment_id=graphene.ID(required=True))
    def resolve_is_comment_liked(self, info, comment_id, limit=10):
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
            
            # Create user profile with avatar if provided
            profile_data = {
                'user': user,
                'role': 'reader',
                'is_verified': False
            }
            
            # Handle avatar if provided
            if avatar and avatar.strip():
                try:
                    print(f"DEBUG: Received avatar URL: {avatar}")
                    # Check if it's a Cloudinary URL or other image URL
                    if avatar.startswith(('http://', 'https://')):
                        # For Cloudinary URLs, optimize for storage
                        from .cloudinary_utils import CloudinaryUtils
                        if 'cloudinary.com' in avatar:
                            # Optimize Cloudinary URL for storage
                            optimized_avatar = CloudinaryUtils.optimize_for_storage(avatar)
                            profile_data['avatar'] = optimized_avatar
                            print(f"DEBUG: Optimized Cloudinary avatar: {optimized_avatar}")
                        else:
                            # For other URLs, store directly
                            profile_data['avatar'] = avatar
                            print(f"DEBUG: Storing non-Cloudinary URL: {avatar}")
                    else:
                        # For non-URL strings (base64, etc.), store directly
                        profile_data['avatar'] = avatar
                        print(f"DEBUG: Storing non-URL avatar: {avatar[:50]}...")
                except Exception as e:
                    # If avatar processing fails, log the error but continue without avatar
                    print(f"Avatar processing error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Create profile with or without avatar
            UserProfile.objects.create(**profile_data)
            
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
        dateOfBirth = graphene.Date()
        avatar = graphene.String()  # Cloudinary URL

    profile = graphene.Field(UserProfileType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, bio=None, phone=None, dateOfBirth=None, avatar=None):
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
            if dateOfBirth is not None:
                profile.date_of_birth = dateOfBirth
            if avatar is not None:
                profile.avatar = avatar
                
            profile.save()
            
            return UpdateUserProfile(profile=profile, success=True, errors=[])
        
        except UserProfile.DoesNotExist:
            return UpdateUserProfile(success=False, errors=['Profile not found'])
        except Exception as e:
            return UpdateUserProfile(success=False, errors=[str(e)])


class ChangePassword(graphene.Mutation):
    """
    Change user password
    """
    class Arguments:
        currentPassword = graphene.String(required=True)
        newPassword = graphene.String(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, currentPassword, newPassword):
        """
        Change user password mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return ChangePassword(success=False, errors=['Authentication required'])

        try:
            # Check if current password is correct
            if not user.check_password(currentPassword):
                return ChangePassword(success=False, errors=['Current password is incorrect'])

            # Validate new password
            if len(newPassword) < 8:
                return ChangePassword(success=False, errors=['New password must be at least 8 characters long'])

            # Set new password
            user.set_password(newPassword)
            user.save()
            
            return ChangePassword(success=True, errors=[])
        
        except Exception as e:
            return ChangePassword(success=False, errors=[str(e)])


class CreateNews(graphene.Mutation):
    """
    Create a new news article (for writers)
    """
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        excerpt = graphene.String(required=True)
        categoryId = graphene.Int(required=True)
        tagIds = graphene.List(graphene.Int)
        featuredImage = graphene.String()  # Cloudinary URL
        metaDescription = graphene.String()
        metaKeywords = graphene.String()

    news = graphene.Field(NewsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, content, excerpt, categoryId, tagIds=None, 
               featuredImage=None, metaDescription=None, metaKeywords=None):
        """
        Create news article mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return CreateNews(success=False, errors=['Authentication required'])

        try:
            # Check if user has writer role or higher
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['writer', 'manager', 'admin']:
                return CreateNews(success=False, errors=['Permission denied. Writer role required.'])

            # Check if category exists
            try:
                category = Category.objects.get(id=categoryId)
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

            # Sanitize HTML content
            sanitized_content = sanitize_html_content(content)

            # Create news article
            news = News.objects.create(
                title=title,
                slug=slug,
                content=sanitized_content,
                excerpt=excerpt,
                author=user,
                category=category,
                featured_image=featuredImage or '',
                meta_description=metaDescription or '',
                meta_keywords=metaKeywords or '',
                status='draft'  # Default to draft
            )

            # Add tags if provided
            if tagIds:
                tags = Tag.objects.filter(id__in=tagIds)
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
        description = graphene.String(required=False)
    category = graphene.Field(CategoryType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, name, description=""):
        try:
            # Check if name already exists
            if Category.objects.filter(name=name).exists():
                return CreateCategory(success=False, errors="Name already exists.", category=None)

            # Create new Category (slug will be auto-generated in model save method)
            category = Category.objects.create(
                name=name,
                description=description,
            )
            return CreateCategory(category=category, success=True, errors="Category created successfully.")
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
    tag = graphene.Field(TagType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, name):
        try:
            # Check if name already exists
            if Tag.objects.filter(name=name).exists():
                return CreateTag(success=False, errors="Name already exists.", tag=None)

            # Create new Tag (slug will be auto-generated in model save method)
            tag = Tag.objects.create(
                name=name,
            )
            return CreateTag(tag=tag, success=True, errors="Tag created successfully.")
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

class ToggleTag(graphene.Mutation):
    """
    Toggle tag active status (admin only)
    """
    class Arguments:
        id = graphene.Int(required=True)
    
    tag = graphene.Field(TagType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        try:
            # Check if user is authenticated and is admin
            user = info.context.user
            if not user.is_authenticated:
                return ToggleTag(success=False, errors=["User not authenticated"])
            
            # Check if user has admin role
            try:
                user_profile = user.profile
                if user_profile.role.lower() != 'admin':
                    return ToggleTag(success=False, errors=["Admin access required"])
            except UserProfile.DoesNotExist:
                return ToggleTag(success=False, errors=["User profile not found"])

            # Get the tag
            try:
                tag = Tag.objects.get(id=id)
            except Tag.DoesNotExist:
                return ToggleTag(success=False, errors=["Tag not found"])

            # Toggle the is_active status
            tag.is_active = not tag.is_active
            tag.save()

            # If tag is being deactivated, archive all articles with this tag
            if not tag.is_active:
                articles_with_tag = News.objects.filter(tags=tag, status__in=['published', 'draft', 'pending'])
                for article in articles_with_tag:
                    article.status = 'archived'
                    article.save()

            return ToggleTag(tag=tag, success=True, errors=[])

        except Exception as e:
            return ToggleTag(success=False, errors=[str(e)])
        
class CreateComment(graphene.Mutation):
    """
    Create a new comment
    """

    class Arguments:
        articleId = graphene.Int(required=True)
        content = graphene.String(required=True)
        parentId = graphene.Int(required=False)

    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, articleId, content, parentId=None):
        try:
            user = info.context.user

            # Check user authentication
            if user.is_anonymous:
                return CreateComment(success=False, errors="Authentication required.", comment=None)

            # Check if the article exists
            try:
                article = News.objects.get(pk=articleId)
            except News.DoesNotExist:
                return CreateComment(success=False, errors="Article not found.", comment=None)

            # Check if parent comment exists, if provided
            parent = None
            if parentId:
                try:
                    parent = Comment.objects.get(pk=parentId, article=article)
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

class ChangeUserRole(graphene.Mutation):
    """
    Change user role (admin only)
    """
    class Arguments:
        userId = graphene.Int(required=True)
        newRole = graphene.String(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    user = graphene.Field(UserType)

    def mutate(self, info, userId, newRole):
        """
        Change user role mutation (admin only)
        """
        current_user = info.context.user
        if not current_user.is_authenticated:
            return ChangeUserRole(success=False, errors=['Authentication required'])

        try:
            # Check if current user is admin
            current_profile = UserProfile.objects.get(user=current_user)
            if current_profile.role.lower() != 'admin':
                return ChangeUserRole(success=False, errors=['Admin privileges required'])

            # Validate new role
            valid_roles = ['reader', 'writer', 'manager', 'admin']
            if newRole not in valid_roles:
                return ChangeUserRole(success=False, errors=[f'Invalid role. Must be one of: {", ".join(valid_roles)}'])

            # Get target user
            target_user = User.objects.get(id=userId)
            target_profile, created = UserProfile.objects.get_or_create(
                user=target_user,
                defaults={'role': newRole}
            )
            
            if not created:
                target_profile.role = newRole
                target_profile.save()

            return ChangeUserRole(success=True, errors=[], user=target_user)

        except UserProfile.DoesNotExist:
            return ChangeUserRole(success=False, errors=['User profile not found'])
        except User.DoesNotExist:
            return ChangeUserRole(success=False, errors=['User not found'])
        except Exception as e:
            return ChangeUserRole(success=False, errors=[str(e)])


class GetCloudinarySignature(graphene.Mutation):
    """
    Get signed upload parameters for Cloudinary
    """
    signature = graphene.String()
    timestamp = graphene.String()
    api_key = graphene.String()
    cloud_name = graphene.String()
    folder = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info):
        """
        Generate Cloudinary upload signature
        """
        user = info.context.user
        if not user.is_authenticated:
            return GetCloudinarySignature(success=False, errors=['Authentication required'])

        try:
            # Check if user has writer role or higher
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['writer', 'manager', 'admin']:
                return GetCloudinarySignature(success=False, errors=['Permission denied. Writer role required.'])

            upload_params = get_cloudinary_upload_signature()
            
            return GetCloudinarySignature(
                signature=upload_params['signature'],
                timestamp=str(upload_params['timestamp']),
                api_key=upload_params['api_key'],
                cloud_name=upload_params['cloud_name'],
                folder=upload_params['folder'],
                success=True,
                errors=[]
            )

        except UserProfile.DoesNotExist:
            return GetCloudinarySignature(success=False, errors=['User profile not found'])
        except Exception as e:
            return GetCloudinarySignature(success=False, errors=[str(e)])


class UploadBase64Image(graphene.Mutation):
    """
    Upload base64 image to Cloudinary with proper sizing and optimization
    """
    class Arguments:
        base64Data = graphene.String(required=True, description="Base64 encoded image data")
        folder = graphene.String(default_value="newsor/uploads", description="Cloudinary folder")
        maxWidth = graphene.Int(default_value=800, description="Maximum width for resizing")
        maxHeight = graphene.Int(default_value=600, description="Maximum height for resizing")
        quality = graphene.String(default_value="auto", description="Image quality (auto, 100, 80, etc.)")
        format = graphene.String(default_value="auto", description="Image format (auto, jpg, png, webp)")

    url = graphene.String()
    public_id = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, base64Data, folder="newsor/uploads", maxWidth=800, maxHeight=600, quality="auto", format="auto"):
        """
        Process base64 image and upload to Cloudinary
        """
        try:
            # Remove data URL prefix if present
            if base64Data.startswith('data:image'):
                base64Data = base64Data.split(',')[1]
            
            # Decode base64 data
            try:
                image_data = base64.b64decode(base64Data)
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
            
            # Only resize if image is significantly larger than target
            # Use a more gentle approach to preserve quality
            if image.width > maxWidth * 1.5 or image.height > maxHeight * 1.5:
                # Calculate new size maintaining aspect ratio
                ratio = min(maxWidth / image.width, maxHeight / image.height)
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                
                # Use high-quality resampling
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # If image is only slightly larger, keep original size
            
            # Convert back to bytes (use high quality to preserve image fidelity)
            output = io.BytesIO()
            if image.mode == 'RGBA':
                # For PNG with transparency, save as PNG
                image.save(output, format='PNG', optimize=False)
            else:
                # For regular images, save as JPEG with maximum quality
                image.save(output, format='JPEG', quality=95, optimize=False)
            output.seek(0)
            
            # Generate unique filename
            unique_filename = f"upload_{uuid.uuid4().hex}"
            
            # Upload to Cloudinary with minimal processing to preserve quality
            upload_result = cloudinary.uploader.upload(
                output.getvalue(),
                public_id=unique_filename,
                folder=folder,
                # Remove quality transformation to avoid double compression
                # Let Cloudinary handle optimization automatically
                resource_type="image",
                quality="auto:best"  # Use Cloudinary's best automatic quality
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
        base64Data = graphene.String(required=True, description="Base64 encoded avatar image")

    profile = graphene.Field(UserProfileType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, base64Data):
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
                base64Data=base64Data,
                folder="newsor/avatars",
                maxWidth=400,
                maxHeight=400,
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



# =========================
# Mutations and Schema
# =========================


# =========================
# Contact Mutations
# =========================

class CreateContact(graphene.Mutation):
    """
    Create a new contact entry
    """
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()
        request_service = graphene.String(required=True)
        request_content = graphene.String(required=True)
    
    contact = graphene.Field(ContactType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, name, email, request_service, request_content, phone=None):
        """
        Create contact mutation
        """
        try:
            # Validate required fields
            if not name or not email or not request_service or not request_content:
                return CreateContact(
                    success=False, 
                    errors=['Name, email, request service, and request content are required'],
                    contact=None
                )
            
            # Check if this email is new (not already in database)
            from .utils import should_send_welcome_email
            should_send_email = should_send_welcome_email(email)
            
            # Create contact
            contact = Contact.objects.create(
                name=name,
                email=email,
                phone=phone or '',
                request_service=request_service,
                request_content=request_content,
                status='new'
            )
            
            # Send thank-you email only for new contacts (email not previously in database)
            if should_send_email:
                try:
                    from .email_service import EmailService
                    email_template = EmailService.get_default_thank_you_template()
                    EmailService.send_thank_you_email(contact, email_template)
                    from .notification_service import NotificationService
                    NotificationService.notify_admin_form_submission(contact)

                except Exception as email_error:
                    # Log the email error but don't fail the contact creation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send thank-you email: {str(email_error)}")
            else:
                # Log that email was not sent due to existing contact
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Thank-you email not sent to {email} - email already exists in contact database")
            
            return CreateContact(
                contact=contact,
                success=True,
                errors=[]
            )
            
        except Exception as e:
            return CreateContact(
                success=False,
                errors=[str(e)],
                contact=None
            )


class UpdateContactStatus(graphene.Mutation):
    """
    Update contact status (admin/manager only)
    """
    class Arguments:
        id = graphene.Int(required=True)
        status = graphene.String(required=True)
    
    contact = graphene.Field(ContactType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, id, status):
        """
        Update contact status mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return UpdateContactStatus(
                success=False, 
                errors=['Authentication required'],
                contact=None
            )
        
        try:
            # Check user permissions
            profile = UserProfile.objects.get(user=user)
            user_role = profile.role.lower()
            if user_role not in ["admin", "manager"]:
                return UpdateContactStatus(
                    success=False,
                    errors=['Permission denied. Admin or manager role required.'],
                    contact=None
                )
            
            # Get and update contact
            contact = Contact.objects.get(id=id)
            
            # Validate status
            valid_statuses = ['new', 'in_progress', 'resolved', 'closed']
            if status not in valid_statuses:
                return UpdateContactStatus(
                    success=False,
                    errors=[f'Invalid status. Must be one of: {", ".join(valid_statuses)}'],
                    contact=None
                )
            
            contact.status = status
            contact.save()
            
            return UpdateContactStatus(
                contact=contact,
                success=True,
                errors=[]
            )
            
        except UserProfile.DoesNotExist:
            return UpdateContactStatus(
                success=False,
                errors=['User profile not found'],
                contact=None
            )
        except Contact.DoesNotExist:
            return UpdateContactStatus(
                success=False,
                errors=['Contact not found'],
                contact=None
            )
        except Exception as e:
            return UpdateContactStatus(
                success=False,
                errors=[str(e)],
                contact=None
            )


class UpdateEmailTemplate(graphene.Mutation):
    """
    """
    class Arguments:
        name = graphene.String(required=True)
        subject = graphene.String(required=True)
        content = graphene.String(required=True)
        variables = graphene.List(graphene.String)
    
    email_template = graphene.Field(EmailTemplateType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, name, subject, content, variables=None):
        """
        Update email template mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return UpdateEmailTemplate(
                success=False,
                errors=['Authentication required'],
                email_template=None
            )
        
        try:
            # Check user permissions
            profile = UserProfile.objects.get(user=user)
            user_role = profile.role.lower()
            if user_role not in ["admin", "manager"]:
                return UpdateEmailTemplate(
                    success=False,
                    errors=['Permission denied. Admin or manager role required.'],
                    email_template=None
                )
            
            # Get or create email template
            email_template, created = EmailTemplate.objects.get_or_create(
                name=name,
                defaults={
                    'subject': subject,
                    'content': content,
                    'variables': variables or []
                }
            )
            
            if not created:
                # Update existing template
                email_template.subject = subject
                email_template.content = content
                email_template.variables = variables or []
                email_template.save()
            
            return UpdateEmailTemplate(
                email_template=email_template,
                success=True,
                errors=[]
            )
            
        except UserProfile.DoesNotExist:
            return UpdateEmailTemplate(
                success=False,
                errors=['User profile not found'],
                email_template=None
            )
        except Exception as e:
            return UpdateEmailTemplate(
                success=False,
                errors=[str(e)],
                email_template=None
            )


class SendThankYouEmail(graphene.Mutation):
    """
    Send thank you email to a contact using a specific email template
    """
    class Arguments:
        contact_id = graphene.ID(required=True)
        template_id = graphene.ID()  # Optional: use specific template
    
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(graphene.String)
    
    @staticmethod
    def mutate(root, info, contact_id, template_id=None):
        user = info.context.user
        
        if not user.is_authenticated:
            return SendThankYouEmail(
                success=False,
                message="Authentication required",
                errors=["You must be logged in to perform this action"]
            )
        
        try:
            # Check if user is admin
            profile = UserProfile.objects.get(user=user)
            user_role = profile.role.lower()
            if user_role not in ["admin", "manager"]:
                return SendThankYouEmail(
                    success=False,
                    message="Permission denied",
                    errors=["You don't have permission to perform this action"]
                )
        except UserProfile.DoesNotExist:
            return SendThankYouEmail(
                success=False,
                message="User profile not found",
                errors=["User profile not found"]
            )
        
        try:
            # Get the contact
            contact = Contact.objects.get(id=contact_id)
            
            # Get the email template
            if template_id:
                email_template = EmailTemplate.objects.get(id=template_id, is_active=True)
            else:
                # Use default thank you template
                from .email_service import EmailService
                email_template = EmailService.get_default_thank_you_template()
            
            # Send the email
            from .email_service import EmailService
            success = EmailService.send_thank_you_email(contact, email_template)
            
            if success:
                return SendThankYouEmail(
                    success=True,
                    message=f"Thank you email sent successfully to {contact.email}",
                    errors=[]
                )
            else:
                return SendThankYouEmail(
                    success=False,
                    message="Failed to send email",
                    errors=["Email delivery failed"]
                )
                
        except Contact.DoesNotExist:
            return SendThankYouEmail(
                success=False,
                message="Contact not found",
                errors=["Contact with provided ID does not exist"]
            )
        except EmailTemplate.DoesNotExist:
            return SendThankYouEmail(
                success=False,
                message="Email template not found",
                errors=["Email template with provided ID does not exist"]
            )
        except Exception as e:
            return SendThankYouEmail(
                success=False,
                message="An error occurred while sending email",
                errors=[str(e)]
            )


# =========================
# GraphQL Mutation Root
# =========================

# Define the SubmitNewsForReview mutation
class SubmitNewsForReview(graphene.Mutation):
    """
    Submit a news article for review (writer/manager/admin only)
    """
    class Arguments:
        article_id = graphene.Int(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, article_id):
        user = info.context.user
        if not user.is_authenticated:
            return SubmitNewsForReview(success=False, errors=["Authentication required"])
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ["writer", "manager", "admin"]:
                return SubmitNewsForReview(success=False, errors=["Permission denied."])
            try:
                news = News.objects.get(id=article_id, author=user)
            except News.DoesNotExist:
                return SubmitNewsForReview(success=False, errors=["Article not found or not owned by user."])
            if news.status.lower() != "draft":
                return SubmitNewsForReview(success=False, errors=["Only draft articles can be submitted for review."])
            news.status = "pending"
            news.save()
            return SubmitNewsForReview(success=True, errors=[])
        except UserProfile.DoesNotExist:
            return SubmitNewsForReview(success=False, errors=["User profile not found"])
        except Exception as e:
            return SubmitNewsForReview(success=False, errors=[str(e)])

# Define MarkNotificationAsRead mutation
class MarkNotificationAsRead(graphene.Mutation):
    """
    Mark a notification as read for the authenticated user
    """
    class Arguments:
        notification_id = graphene.Int(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, notification_id):
        user = info.context.user
        if not user.is_authenticated:
            return MarkNotificationAsRead(success=False, errors=["Authentication required"])
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.is_read = True
            notification.save()
            return MarkNotificationAsRead(success=True, errors=[])
        except Notification.DoesNotExist:
            return MarkNotificationAsRead(success=False, errors=["Notification not found"])
        except Exception as e:
            return MarkNotificationAsRead(success=False, errors=[str(e)])

# Define MarkAllNotificationsAsRead mutation
class MarkAllNotificationsAsRead(graphene.Mutation):
    """
    Mark all notifications as read for the authenticated user
    """
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return MarkAllNotificationsAsRead(success=False, errors=["Authentication required"])
        try:
            Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
            return MarkAllNotificationsAsRead(success=True, errors=[])
        except Exception as e:
            return MarkAllNotificationsAsRead(success=False, errors=[str(e)])

# Define the UpdateNews mutation
class UpdateNews(graphene.Mutation):
    """
    Update an existing news article (for writers, managers, admins)
    """
    class Arguments:
        id = graphene.Int(required=True)
        title = graphene.String()
        content = graphene.String()
        excerpt = graphene.String()
        categoryId = graphene.Int()
        tagIds = graphene.List(graphene.Int)
        featuredImage = graphene.String()
        metaDescription = graphene.String()
        metaKeywords = graphene.String()
        status = graphene.String()

    news = graphene.Field(NewsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, title=None, content=None, excerpt=None, categoryId=None, tagIds=None,
               featuredImage=None, metaDescription=None, metaKeywords=None, status=None):
        user = info.context.user
        if not user.is_authenticated:
            return UpdateNews(success=False, errors=['Authentication required'])

        try:
            news = News.objects.get(id=id)
            profile = UserProfile.objects.get(user=user)
            user_role = profile.role.lower()
            # Only allow update if user is admin/manager, or the author
            if user_role in ["admin", "manager"] or news.author == user:
                if title is not None:
                    news.title = title
                if content is not None:
                    news.content = sanitize_html_content(content)
                if excerpt is not None:
                    news.excerpt = excerpt
                if categoryId is not None:
                    try:
                        category = Category.objects.get(id=categoryId)
                        news.category = category
                    except Category.DoesNotExist:
                        return UpdateNews(success=False, errors=['Category not found'])
                if tagIds is not None:
                    tags = Tag.objects.filter(id__in=tagIds)
                    news.tags.set(tags)
                if featuredImage is not None:
                    news.featured_image = featuredImage
                if metaDescription is not None:
                    news.meta_description = metaDescription
                if metaKeywords is not None:
                    news.meta_keywords = metaKeywords
                if status is not None:
                    news.status = status
                news.save()
                return UpdateNews(news=news, success=True, errors=[])
            else:
                return UpdateNews(success=False, errors=['Permission denied.'])
        except News.DoesNotExist:
            return UpdateNews(success=False, errors=['News article not found'])
        except UserProfile.DoesNotExist:
            return UpdateNews(success=False, errors=['User profile not found'])
        except Exception as e:
            return UpdateNews(success=False, errors=[str(e)])

class UpdateNewsStatus(graphene.Mutation):
    """
    Update the status of a news article (publish, archive, etc.)
    """
    class Arguments:
        id = graphene.Int(required=True)
        status = graphene.String(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, status):
        user = info.context.user
        if not user.is_authenticated:
            return UpdateNewsStatus(success=False, errors=["Authentication required"])
        try:
            news = News.objects.get(id=id)
            profile = UserProfile.objects.get(user=user)
            user_role = profile.role.lower()
            # Only allow update if user is admin/manager, or the author
            if user_role in ["admin", "manager"] or news.author == user:
                # Only allow valid status transitions
                valid_statuses = ["draft", "pending", "published", "archived"]
                if status.lower() not in valid_statuses:
                    return UpdateNewsStatus(success=False, errors=[f"Invalid status: {status}"])
                news.status = status.lower()
                news.save()
                return UpdateNewsStatus(success=True, errors=[])
            else:
                return UpdateNewsStatus(success=False, errors=["Permission denied."])
        except News.DoesNotExist:
            return UpdateNewsStatus(success=False, errors=["News article not found"])
        except UserProfile.DoesNotExist:
            return UpdateNewsStatus(success=False, errors=["User profile not found"])
        except Exception as e:
            return UpdateNewsStatus(success=False, errors=[str(e)])

class Mutation(graphene.ObjectType):
    """
    API GraphQL Mutations
    """
    delete_news = DeleteNews.Field()
    create_user = CreateUser.Field()
    update_user_profile = UpdateUserProfile.Field()
    change_password = ChangePassword.Field()
    create_news = CreateNews.Field()
    create_category = CreateCategory.Field()
    create_tag = CreateTag.Field()
    toggle_tag = ToggleTag.Field()
    create_comment = CreateComment.Field()
    change_user_role = ChangeUserRole.Field()
    get_cloudinary_signature = GetCloudinarySignature.Field()
    upload_base64_image = UploadBase64Image.Field()
    upload_avatar_image = UploadAvatarImage.Field()
    # update_news_status = UpdateNewsStatus.Field()
    submit_news_for_review = SubmitNewsForReview.Field()
    # UpdateNewsStatus mutation for updating article status (publish, archive, etc.)
    update_news_status = UpdateNewsStatus.Field()
    update_news = UpdateNews.Field()
    mark_notification_as_read = MarkNotificationAsRead.Field()
    mark_all_notifications_as_read = MarkAllNotificationsAsRead.Field()
    create_like_article = CreateLikeArticle.Field()
    create_like_comment = CreateLikeComment.Field()
    update_like_status = UpdateLikeStatus.Field()
    create_readinghistory = CreateReadingHistory.Field()
    update_category = UpdateCategory.Field()
    delete_category = DeleteCategory.Field()
    update_tag = UpdateTag.Field()
    delete_tag = DeleteTag.Field()
    create_contact = CreateContact.Field()
    update_contact_status = UpdateContactStatus.Field()
    update_email_template = UpdateEmailTemplate.Field()
    send_thank_you_email = SendThankYouEmail.Field()


class Subscription(graphene.ObjectType):
    """
    GraphQL Subscriptions for real-time updates
    """
    notification_added = graphene.Field(NotificationType)
    
    def resolve_notification_added(root, info):
        """
        Subscribe to new notifications for the authenticated user
        """
        # This will be handled by our custom consumer
        # The subscription field is just a placeholder for the schema
        return None


# =========================
# GraphQL Schema Definition
# =========================

schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)
