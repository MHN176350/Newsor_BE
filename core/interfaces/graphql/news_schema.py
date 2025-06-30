"""
GraphQL interface layer for news operations.
This layer converts between GraphQL and domain entities.
"""

import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User

from api.models import News as DjangoNews, Category as DjangoCategory, Tag as DjangoTag
from ...domain.entities import News, NewsStatus
from ...application.use_cases.news_use_cases import (
    CreateNewsUseCase, GetPublishedNewsUseCase, GetNewsBySlugUseCase
)
from ...infrastructure.repositories.django_repositories import (
    DjangoNewsRepository, DjangoUserProfileRepository, 
    DjangoCategoryRepository, DjangoTagRepository
)
from ...infrastructure.services.cloudinary_service import (
    BleachContentSanitizationService, CloudinaryImageUploadService
)
from ...application.services import SlugGenerationService


class NewsType(DjangoObjectType):
    """GraphQL News type."""
    featured_image_url = graphene.String()
    
    class Meta:
        model = DjangoNews
        exclude = ['featured_image']
    
    def resolve_featured_image_url(self, info):
        if self.featured_image:
            try:
                return str(self.featured_image.url)
            except Exception:
                return "/static/images/default-news.svg"
        return "/static/images/default-news.svg"


class CreateNewsInput(graphene.InputObjectType):
    """Input type for creating news."""
    title = graphene.String(required=True)
    content = graphene.String(required=True)
    excerpt = graphene.String(required=True)
    category_id = graphene.Int(required=True)
    tag_ids = graphene.List(graphene.Int)
    featured_image = graphene.String()
    meta_description = graphene.String()
    meta_keywords = graphene.String()


class CreateNewsMutation(graphene.Mutation):
    """GraphQL mutation for creating news."""
    
    class Arguments:
        input = CreateNewsInput(required=True)
    
    news = graphene.Field(NewsType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, input):
        """Execute create news mutation."""
        user = info.context.user
        if not user.is_authenticated:
            return CreateNewsMutation(success=False, errors=['Authentication required'])
        
        try:
            # Initialize repositories and services
            news_repository = DjangoNewsRepository()
            user_profile_repository = DjangoUserProfileRepository()
            category_repository = DjangoCategoryRepository()
            tag_repository = DjangoTagRepository()
            content_sanitization_service = BleachContentSanitizationService()
            slug_generation_service = SlugGenerationService()
            
            # Initialize use case
            create_news_use_case = CreateNewsUseCase(
                news_repository=news_repository,
                user_profile_repository=user_profile_repository,
                category_repository=category_repository,
                tag_repository=tag_repository,
                content_sanitization_service=content_sanitization_service,
                slug_generation_service=slug_generation_service,
            )
            
            # Create domain entity from input
            news = News(
                title=input.title,
                content=input.content,
                excerpt=input.excerpt,
                category_id=input.category_id,
                tag_ids=input.tag_ids or [],
                featured_image_url=input.featured_image or "",
                meta_description=input.meta_description or "",
                meta_keywords=input.meta_keywords or "",
            )
            
            # Execute use case
            created_news = create_news_use_case.execute(news, user.id)
            
            # Convert back to Django model for GraphQL response
            django_news = DjangoNews.objects.get(id=created_news.id)
            
            return CreateNewsMutation(news=django_news, success=True, errors=[])
            
        except PermissionError as e:
            return CreateNewsMutation(success=False, errors=[str(e)])
        except ValueError as e:
            return CreateNewsMutation(success=False, errors=[str(e)])
        except Exception as e:
            return CreateNewsMutation(success=False, errors=[f"Unexpected error: {str(e)}"])


class GetCloudinarySignatureMutation(graphene.Mutation):
    """GraphQL mutation for getting Cloudinary upload signature."""
    
    signature = graphene.String()
    timestamp = graphene.String()
    api_key = graphene.String()
    cloud_name = graphene.String()
    folder = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info):
        """Execute get Cloudinary signature mutation."""
        user = info.context.user
        if not user.is_authenticated:
            return GetCloudinarySignatureMutation(success=False, errors=['Authentication required'])
        
        try:
            # Check user permissions
            user_profile_repository = DjangoUserProfileRepository()
            profile = user_profile_repository.get_by_user_id(user.id)
            if not profile or profile.role.value not in ['writer', 'manager', 'admin']:
                return GetCloudinarySignatureMutation(
                    success=False, 
                    errors=['Permission denied. Writer role required.']
                )
            
            # Get upload signature
            image_service = CloudinaryImageUploadService()
            upload_params = image_service.get_upload_signature()
            
            return GetCloudinarySignatureMutation(
                signature=upload_params['signature'],
                timestamp=str(upload_params['timestamp']),
                api_key=upload_params['api_key'],
                cloud_name=upload_params['cloud_name'],
                folder=upload_params['folder'],
                success=True,
                errors=[]
            )
            
        except Exception as e:
            return GetCloudinarySignatureMutation(success=False, errors=[str(e)])


class NewsQuery(graphene.ObjectType):
    """GraphQL queries for news."""
    
    published_news = graphene.List(
        NewsType,
        search=graphene.String(),
        category_id=graphene.Int(),
        tag_id=graphene.Int()
    )
    news_article = graphene.Field(NewsType, slug=graphene.String())
    
    def resolve_published_news(self, info, search=None, category_id=None, tag_id=None):
        """Resolve published news query."""
        news_repository = DjangoNewsRepository()
        use_case = GetPublishedNewsUseCase(news_repository)
        
        filters = {}
        if search:
            filters['search'] = search
        if category_id:
            filters['category_id'] = category_id
        if tag_id:
            filters['tag_id'] = tag_id
        
        domain_news_list = use_case.execute(filters)
        
        # Convert to Django models for GraphQL response
        django_news_ids = [news.id for news in domain_news_list]
        return DjangoNews.objects.filter(id__in=django_news_ids).order_by('-published_at')
    
    def resolve_news_article(self, info, slug):
        """Resolve news article by slug."""
        news_repository = DjangoNewsRepository()
        use_case = GetNewsBySlugUseCase(news_repository)
        
        domain_news = use_case.execute(slug)
        if not domain_news:
            return None
        
        return DjangoNews.objects.get(id=domain_news.id)


class NewsMutation(graphene.ObjectType):
    """GraphQL mutations for news."""
    
    create_news = CreateNewsMutation.Field()
    get_cloudinary_signature = GetCloudinarySignatureMutation.Field()
