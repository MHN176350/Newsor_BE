
import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from .models import (
    Category, Tag, UserProfile, News, Comment, 
    Like, ReadingHistory, NewsletterSubscription, ArticleImage, Notification, ContactMessage,
    EmailTemplate
)

from .utils import sanitize_html_content, get_cloudinary_upload_signature
import base64
import io
from PIL import Image
import cloudinary.uploader
import uuid
from .cloudinary_utils import CloudinaryUtils
from django.db.models import Count, Q
from django.db.models import Case, When, Value, IntegerField
from datetime import timedelta
from django.utils import timezone
from mail.send_mail import send_html_email
from django.template import Template, Context

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


class ContactMessageType(DjangoObjectType):
    """
    GraphQL ContactMessage type
    """
    class Meta:
        model = ContactMessage
        fields = '__all__'
    
    def resolve_user(self, info):
        """Resolve the user who sent the message"""
        return self.user if self.user else None

class EmailTemplateType(DjangoObjectType):
    """
    GraphQL EmailTemplate type
    """
    class Meta:
        model = EmailTemplate
        fields = ('id', 'subject', 'html_content', 'updated_at')

class Query(graphene.ObjectType):
    """
    API GraphQL Queries
    """
# Basic queries
    hello = graphene.String(name=graphene.String(default_value='World'))
    def resolve_hello(self, info, name):
        """Simple hello world resolver"""
        return f'Hello {name}'

    # User queries
    me = graphene.Field(UserType)
    def resolve_me(self, info):
        """Get current authenticated user"""
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
    
    users = graphene.List(UserType)
    def resolve_users(self, info):
        """Get all users"""
        return User.objects.all()
    
    user = graphene.Field(UserType, id=graphene.Int(required=True))

    user_profile = graphene.Field(UserProfileType, user_id=graphene.Int(required=True))
    def resolve_user_profile(self, info, user_id):
        """Get user profile by user ID"""
        try:
            return UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return None

    
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
        user = info.context.user

        try:
            if id:
                news = News.objects.get(pk=id)
            elif slug:
                news = News.objects.get(slug=slug)
            else:
                return None
        except News.DoesNotExist:
            return None

        # check publish
        if news.status != 'published':
            if not user.is_authenticated:
                return None
            if user != news.author and not user.is_staff:
                return None
        return news

    published_news = graphene.List(NewsType,
                                  search=graphene.String(),
                                  category_id=graphene.Int(),
                                  tag_id=graphene.Int())
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

    news_for_review = graphene.List(NewsType)
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
        return News.objects.filter(status__in=['draft', 'pending', 'published', 'rejected']) \
        .annotate(
            is_pending=Case(
                When(status='pending', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('is_pending', '-created_at')

    my_news = graphene.List(NewsType)
    def resolve_my_news(self, info):
        """Get current user's news articles"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Return all articles by the current user
        return News.objects.filter(author=user).annotate(
        priority_order=Case(
            When(status__in=['draft', 'rejected'], then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
        ).order_by('priority_order', '-created_at')

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
    search_categories = graphene.List(CategoryType, keyword=graphene.String(required=True),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),)
    def resolve_search_categories(self, info, keyword,limit, offset):
        """ Filter category name containing the keyword (case-insensitive) """
        return Category.objects.filter(name__icontains=keyword)[offset:offset + limit] 
    tags = graphene.List(TagType)


    admin_tags = graphene.List(TagType)  # Admin-only query to get all tags including inactive
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
    def resolve_article_comments(self, info, article_id=None):
        """Get comments for an article"""
        if article_id is None:
            return []
        return Comment.objects.filter(article_id=article_id)
    
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
    # # Analytics queries
    # user_reading_history = graphene.List(ReadingHistoryType, user_id=graphene.Int(required=True))
    
    # Dashboard queries
    dashboard_stats = graphene.Field(DashboardStatsType)
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
    
    
    recent_activity = graphene.List(RecentActivityType, limit=graphene.Int())
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

    
    # Notification queries
    notifications = graphene.List(NotificationType)
    def resolve_notifications(self, info):
        """Get all notifications for the current user"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        return Notification.objects.filter(
            recipient=user
        ).select_related('sender', 'article').order_by('-created_at')
    
    unread_notifications = graphene.List(NotificationType)
    def resolve_unread_notifications(self, info):
        """Get unread notifications for the current user"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).select_related('sender', 'article').order_by('-created_at')

    notification_count = graphene.Int()
    def resolve_notification_count(self, info):
        """Get count of unread notifications for the current user"""
        user = info.context.user
        if not user.is_authenticated:
            return 0
        
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()    

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
    
    
    
    user = graphene.Field(UserType, id=graphene.Int(required=True))

    def resolve_user(self, info, id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=id)
        except User.DoesNotExist:
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

    

    
    

    # def resolve_user_reading_history(self, info, user_id):
    #     """Get user's reading history"""
    #     return ReadingHistory.objects.filter(user_id=user_id)
         
    

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

    contact_messages = graphene.List(
        ContactMessageType,
        from_date=graphene.Date(required=False),
        to_date=graphene.Date(required=False),
        search=graphene.String(required=False),
        service=graphene.String(required=False),  
    )
    def resolve_contact_messages(self, info, from_date=None, to_date=None, search=None, service=None):
        qs = ContactMessage.objects.all()

        # filter by date range
        if from_date:
            qs = qs.filter(created_at__date__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__date__lte=to_date)

        # filter by search term
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )

        # filter by service
        if service:
            qs = qs.filter(service=service)

        return qs.order_by("-created_at")

    first_email_template = graphene.Field(EmailTemplateType)

    def resolve_first_email_template(self, info):
        return EmailTemplate.objects.first()

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
            # if not tag.is_active:
            #     articles_with_tag = News.objects.filter(tags=tag, status__in=['published', 'draft', 'pending'])
            #     for article in articles_with_tag:
            #         article.status = 'archived'
            #         article.save()

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


class UploadRegistrationAvatarImage(graphene.Mutation):
    """
    Upload avatar image for registration (no authentication required)
    """
    class Arguments:
        base64Data = graphene.String(required=True, description="Base64 encoded avatar image")

    url = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, base64Data):
        """
        Upload avatar image without authentication for registration
        """
        try:
            # Upload the image with avatar-specific settings
            upload_mutation = UploadBase64Image()
            upload_result = upload_mutation.mutate(
                info, 
                base64Data=base64Data,
                folder="newsor/avatars/temp",  # Use temp folder for registration avatars
                maxWidth=400,
                maxHeight=400,
                quality="auto",
                format="auto"
            )
            
            if not upload_result.success:
                return UploadRegistrationAvatarImage(success=False, errors=upload_result.errors)
            
            return UploadRegistrationAvatarImage(url=upload_result.url, success=True, errors=[])
            
        except Exception as e:
            return UploadRegistrationAvatarImage(success=False, errors=[f"Avatar upload failed: {str(e)}"])


class UpdateNewsStatus(graphene.Mutation):
    """
    Update news article status (for managers)
    """
    class Arguments:
        id = graphene.Int(required=True)
        status = graphene.String(required=True)
        review_comment = graphene.String()

    news = graphene.Field(NewsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, status, review_comment=None):
        """
        Update news article status mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return UpdateNewsStatus(success=False, errors=['Authentication required'])

        try:
            # Check if user has manager role or higher
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['manager', 'admin']:
                return UpdateNewsStatus(success=False, errors=['Permission denied. Manager role required.'])

            # Get the news article
            try:
                news = News.objects.get(id=id)
            except News.DoesNotExist:
                return UpdateNewsStatus(success=False, errors=['News article not found'])

            # Validate status
            valid_statuses = ['draft', 'pending', 'published', 'rejected', 'archived']
            if status not in valid_statuses:
                return UpdateNewsStatus(success=False, errors=['Invalid status'])

            # Update the news article
            old_status = news.status
            news.status = status
            if status == 'published':
                from django.utils import timezone
                news.published_at = timezone.now()
            
            news.save()

            # Create notifications based on status change
            from .notification_service import NotificationService
            
            if old_status != status:
                if status == 'published':
                    NotificationService.notify_writer_of_publication(news)
                elif status == 'approved':
                    NotificationService.notify_writer_of_approval(news, user)
                elif status == 'rejected':
                    NotificationService.notify_writer_of_rejection(news, user, review_comment)

            return UpdateNewsStatus(news=news, success=True, errors=[])

        except UserProfile.DoesNotExist:
            return UpdateNewsStatus(success=False, errors=['User profile not found'])
        except Exception as e:
            return UpdateNewsStatus(success=False, errors=[str(e)])


class UpdateNews(graphene.Mutation):
    """
    Update an existing news article (for writers)
    """
    class Arguments:
        id = graphene.Int(required=True)
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

    def mutate(self, info, id, title, content, excerpt, categoryId, tagIds=None, 
               featuredImage=None, metaDescription=None, metaKeywords=None):
        """
        Update news article mutation
        """
        user = info.context.user
        if not user.is_authenticated:
            return UpdateNews(success=False, errors=['Authentication required'])

        try:
            # Check if user has writer role or higher
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['writer', 'manager', 'admin']:
                return UpdateNews(success=False, errors=['Permission denied. Writer role required.'])

            # Get the existing news article
            try:
                news = News.objects.get(id=id)
            except News.DoesNotExist:
                return UpdateNews(success=False, errors=['Article not found'])

            # Check if user owns the article (unless they're admin/manager)
            if profile.role.lower() not in ['admin', 'manager'] and news.author.id != user.id:
                return UpdateNews(success=False, errors=['Permission denied. You can only edit your own articles.'])

            # Check if article can be edited (only drafts and rejected articles)
            if news.status.lower() not in ['draft', 'rejected']:
                return UpdateNews(success=False, errors=['You can only edit articles that are in draft or rejected status.'])

            # Check if category exists
            try:
                category = Category.objects.get(id=categoryId)
            except Category.DoesNotExist:
                return UpdateNews(success=False, errors=['Category not found'])

            # Sanitize HTML content
            sanitized_content = sanitize_html_content(content)

            # Update news article
            news.title = title
            news.content = sanitized_content
            news.excerpt = excerpt
            news.category = category
            news.featured_image = featuredImage or ''
            news.meta_description = metaDescription or ''
            news.meta_keywords = metaKeywords or ''
            
            # Update slug if title changed
            from django.utils.text import slugify
            new_slug = slugify(title)
            if new_slug != news.slug:
                # Ensure slug is unique
                counter = 1
                original_slug = new_slug
                while News.objects.filter(slug=new_slug).exclude(id=id).exists():
                    new_slug = f"{original_slug}-{counter}"
                    counter += 1
                news.slug = new_slug
            
            # Change status to pending after update (for review)
            old_status = news.status
            news.status = 'pending'
            
            news.save()
            
            # Notify managers about the update if status changed
            if old_status != 'pending':
                from .notification_service import NotificationService
                NotificationService.notify_managers_of_submission(news)

            # Update tags if provided
            if tagIds is not None:
                tags = Tag.objects.filter(id__in=tagIds)
                news.tags.set(tags)

            return UpdateNews(news=news, success=True, errors=[])

        except UserProfile.DoesNotExist:
            return UpdateNews(success=False, errors=['User profile not found'])
        except Exception as e:
            return UpdateNews(success=False, errors=[str(e)])


# class ToggleLike(graphene.Mutation):
#     """
#     Toggle like/unlike for articles or comments
#     """
#     class Arguments:
#         newsId = graphene.Int()
#         commentId = graphene.Int()

#     success = graphene.Boolean()
#     liked = graphene.Boolean()
#     likes_count = graphene.Int()
#     errors = graphene.List(graphene.String)

#     def mutate(self, info, newsId=None, commentId=None):
#         """
#         Toggle like mutation
#         """
#         user = info.context.user
#         if not user.is_authenticated:
#             return ToggleLike(success=False, errors=['Authentication required'])

#         try:
#             # Validate input - must provide either newsId or commentId
#             if not newsId and not commentId:
#                 return ToggleLike(success=False, errors=['Must provide either newsId or commentId'])
            
#             if newsId and commentId:
#                 return ToggleLike(success=False, errors=['Cannot like both news and comment in same request'])

#             if newsId:
#                 # Handle news like
#                 try:
#                     news = News.objects.get(id=newsId)
#                 except News.DoesNotExist:
#                     return ToggleLike(success=False, errors=['News article not found'])

#                 like, created = Like.objects.get_or_create(
#                     user=user,
#                     article=news,
#                     defaults={'comment': None}
#                 )

#                 if not created:
#                     # Unlike - remove the like
#                     like.delete()
#                     liked = False
#                 else:
#                     # Like created
#                     liked = True

#                 # Get updated like count
#                 likes_count = news.likes.count()
                
#                 return ToggleLike(
#                     success=True,
#                     liked=liked,
#                     likes_count=likes_count,
#                     errors=[]
#                 )

#             elif commentId:
#                 # Handle comment like
#                 try:
#                     comment = Comment.objects.get(id=commentId)
#                 except Comment.DoesNotExist:
#                     return ToggleLike(success=False, errors=['Comment not found'])

#                 like, created = Like.objects.get_or_create(
#                     user=user,
#                     comment=comment,
#                     defaults={'article': None}
#                 )

#                 if not created:
#                     # Unlike - remove the like
#                     like.delete()
#                     liked = False
#                 else:
#                     # Like created
#                     liked = True

#                 # Get updated like count
#                 likes_count = comment.likes.count()
                
#                 return ToggleLike(
#                     success=True,
#                     liked=liked,
#                     likes_count=likes_count,
#                     errors=[]
#                 )

#         except Exception as e:
#             return ToggleLike(success=False, errors=[str(e)])

# ...existing mutations...

class MarkNotificationAsRead(graphene.Mutation):
    """
    Mark a notification as read
    """
    class Arguments:
        notificationId = graphene.Int(required=True)

    success = graphene.Boolean()
    notification = graphene.Field(NotificationType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, notificationId):
        user = info.context.user
        if not user.is_authenticated:
            return MarkNotificationAsRead(success=False, errors=["Authentication required"])

        try:
            notification = Notification.objects.get(id=notificationId, recipient=user)
            notification.mark_as_read()
            return MarkNotificationAsRead(success=True, notification=notification)
        except Notification.DoesNotExist:
            return MarkNotificationAsRead(success=False, errors=["Notification not found"])
        except Exception as e:
            return MarkNotificationAsRead(success=False, errors=[str(e)])


class MarkAllNotificationsAsRead(graphene.Mutation):
    """
    Mark all notifications as read for the current user
    """
    success = graphene.Boolean()
    count = graphene.Int()
    errors = graphene.List(graphene.String)

    def mutate(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return MarkAllNotificationsAsRead(success=False, errors=["Authentication required"])

        try:
            from .notification_service import NotificationService
            count = NotificationService.mark_notifications_as_read(user)
            return MarkAllNotificationsAsRead(success=True, count=count)
        except Exception as e:
            return MarkAllNotificationsAsRead(success=False, errors=[str(e)])


class SubmitNewsForReview(graphene.Mutation):
    """
    Submit a news article for review (changes status from draft to pending)
    """
    class Arguments:
        id = graphene.Int(required=True)

    news = graphene.Field(NewsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            return SubmitNewsForReview(success=False, errors=["Authentication required"])

        try:
            # Check if user has writer role or higher
            profile = UserProfile.objects.get(user=user)
            if profile.role.lower() not in ['writer', 'manager', 'admin']:
                return SubmitNewsForReview(success=False, errors=["Permission denied. Writer role required."])

            # Get the news article
            try:
                news = News.objects.get(id=id, author=user)
            except News.DoesNotExist:
                return SubmitNewsForReview(success=False, errors=["News article not found or you don't have permission to modify it"])

            # Check if article is in draft status
            if news.status != 'draft' and news.status != 'rejected':
                return SubmitNewsForReview(success=False, errors=["Article must be in draft and rejected status to submit for review"])

            # Update status to pending
            news.status = 'pending'
            news.save()

            # Notify managers about the submission
            from .notification_service import NotificationService
            NotificationService.notify_managers_of_submission(news)

            return SubmitNewsForReview(news=news, success=True, errors=[])

        except UserProfile.DoesNotExist:
            return SubmitNewsForReview(success=False, errors=["User profile not found"])
        except Exception as e:
            return SubmitNewsForReview(success=False, errors=[str(e)])


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

# class UpdateLikeStatus(graphene.Mutation):
#     """
#     Deactivate (cancel) an existing like by setting is_active=False
#     """

#     success = graphene.Boolean()
#     errors = graphene.List(graphene.String)

#     def mutate(self, info, base64_data, folder="newsor/uploads", max_width=800, max_height=600, quality="auto", format="auto"):
#         """
#         Process base64 image and upload to Cloudinary
#         """
#         try:
#             # Remove data URL prefix if present
#             if base64_data.startswith('data:image'):
#                 base64_data = base64_data.split(',')[1]
            
#             # Decode base64 data
#             try:
#                 image_data = base64.b64decode(base64_data)
#             except Exception as e:
#                 return UploadBase64Image(success=False, errors=[f"Invalid base64 data: {str(e)}"])
            
#             # Open image with PIL
#             try:
#                 image = Image.open(io.BytesIO(image_data))
#             except Exception as e:
#                 return UploadBase64Image(success=False, errors=[f"Invalid image data: {str(e)}"])
            
#             # Convert RGBA to RGB if necessary
#             if image.mode == 'RGBA':
#                 background = Image.new('RGB', image.size, (255, 255, 255))
#                 background.paste(image, mask=image.split()[-1])
#                 image = background
            
#             # Resize image if needed
#             if image.width > max_width or image.height > max_height:
#                 image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
#             # Convert back to bytes
#             output = io.BytesIO()
#             image.save(output, format='JPEG', quality=85, optimize=True)
#             output.seek(0)
            
#             # Generate unique filename
#             unique_filename = f"upload_{uuid.uuid4().hex}"
            
#             # Upload to Cloudinary
#             upload_result = cloudinary.uploader.upload(
#                 output.getvalue(),
#                 public_id=unique_filename,
#                 folder=folder,
#                 transformation=[
#                     {'quality': quality},
#                     {'fetch_format': format}
#                 ],
#                 resource_type="image"
#             )
            
#             # Optimize URL for storage
#             optimized_url = CloudinaryUtils.optimize_for_storage(upload_result['secure_url'])
            
#             return UploadBase64Image(
#                 url=optimized_url,
#                 public_id=upload_result['public_id'],
#                 success=True,
#                 errors=[]
#             )
            
#         except Exception as e:
#             return UploadBase64Image(success=False, errors=[f"Upload failed: {str(e)}"])


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

class CreateContact(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        message = graphene.String(required=True)
        phone = graphene.String(required=True)
        service = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, email, message,phone, service):
        now = timezone.now()
        # Kiểm tra nếu có bản ghi gần đây từ cùng email chưa được gửi
        recent = ContactMessage.objects.filter(email=email).order_by("-created_at").first()
        if recent and recent.email_sent==True and (now - recent.created_at) < timedelta(minutes=5):
            return CreateContact(
                success=False,
                message="Bạn vừa gửi liên hệ gần đây. Vui lòng chờ vài phút trước khi gửi lại."
            )

        # Lưu bản ghi mới
        contact = ContactMessage.objects.create(name=name, email=email, message=message, phone=phone, service=service)
        # from .notification_service import NotificationService
        # NotificationService.notify_admin_form_submission(contact)
        # Soạn nội dung email

        context = Context({
            "name": name,
            "email": email,
            "message": message,
            "phone": phone,
            "service": service
        })
        template_obj = EmailTemplate.objects.get(id=1)  # Assuming template ID 1 is the contact confirmation template
        # Render HTML template with context
        template = Template(template_obj.html_content)
        rendered_html = template.render(context)
        # send the email
        success, msg = send_html_email(to_email=email,subject=template_obj.subject, html_content=rendered_html)

        if success:
            contact.email_sent = True
            contact.save(update_fields=["email_sent"])

        return CreateContact(success=success, message=msg)
    
class UpdateEmailTemplate(graphene.Mutation):
    """
    Update an existing email template's subject and HTML content
    """

    class Arguments:
        subject = graphene.String(required=False)
        html_content = graphene.String(required=False)

    success = graphene.Boolean()
    errors = graphene.String()
    emailTemplate = graphene.Field(EmailTemplateType)

    def mutate(self, info, subject=None, html_content=None):
        try:
            template = EmailTemplate.objects.get(id=1)

            if subject:
                template.subject = subject

            if html_content:
                template.html_content = html_content

            template.save()

            return UpdateEmailTemplate(
                success=True,
                errors="Template updated successfully.",
                emailTemplate=template
            )

        except EmailTemplate.DoesNotExist:
            return UpdateEmailTemplate(
                success=False,
                errors="Email template not found.",
                emailTemplate=None
            )

        except Exception as e:
            return UpdateEmailTemplate(
                success=False,
                errors=f"Unexpected error: {str(e)}",
                emailTemplate=None
            )

class Mutation(graphene.ObjectType):
    create_contact = CreateContact.Field()

# ...existing mutations...

class Mutation(graphene.ObjectType):
    """
    API GraphQL Mutations
    """
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
    upload_registration_avatar_image = UploadRegistrationAvatarImage.Field()
    update_news_status = UpdateNewsStatus.Field()
    submit_news_for_review = SubmitNewsForReview.Field()
    update_news = UpdateNews.Field()
    # toggle_like = ToggleLike.Field()
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
    update_email_template = UpdateEmailTemplate.Field()


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
