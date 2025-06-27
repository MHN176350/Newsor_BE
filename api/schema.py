import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from .models import (
    Category, Tag, UserProfile, News, Comment, 
    Like, ReadingHistory, NewsletterSubscription
)


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
    class Meta:
        model = Comment
        fields = '__all__'


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
    
    # Category and Tag queries
    categories = graphene.List(CategoryType)
    category = graphene.Field(CategoryType, id=graphene.Int())
    tags = graphene.List(TagType)
    
    # Comment queries
    article_comments = graphene.List(CommentType, article_id=graphene.Int(required=True))
    
    # Analytics queries
    user_reading_history = graphene.List(ReadingHistoryType, user_id=graphene.Int(required=True))

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

    def resolve_user(self, info, id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=id)
        except User.DoesNotExist:
            return None

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

    def resolve_category(self, info, id):
        """Get category by ID"""
        try:
            return Category.objects.get(pk=id)
        except Category.DoesNotExist:
            return None

    def resolve_tags(self, info):
        """Get all tags"""
        return Tag.objects.all()

    def resolve_article_comments(self, info, article_id):
        """Get comments for an article"""
        return Comment.objects.filter(article_id=article_id, status='approved')

    def resolve_user_reading_history(self, info, user_id):
        """Get user's reading history"""
        return ReadingHistory.objects.filter(user_id=user_id)


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
        
class CreateComment(graphene.Mutation):
    """
    Create a new comment
    """

    class Arguments:
        article_id = graphene.ID(required=True)
        content = graphene.String(required=True)
        parent_id = graphene.ID(required=False)

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
