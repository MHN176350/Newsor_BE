"""
Django ORM implementation of domain repositories.
"""

from typing import List, Optional
from django.contrib.auth.models import User as DjangoUser
from api.models import News as DjangoNews, Category as DjangoCategory, Tag as DjangoTag
from api.models import UserProfile as DjangoUserProfile, Comment as DjangoComment
from api.models import ArticleImage as DjangoArticleImage

from ...domain.entities import User, UserProfile, News, Category, Tag, Comment, ArticleImage
from ...domain.entities import NewsStatus, UserRole
from ...domain.repositories import (
    UserRepository, UserProfileRepository, NewsRepository, 
    CategoryRepository, TagRepository, CommentRepository, ArticleImageRepository
)


class DjangoUserRepository(UserRepository):
    """Django ORM implementation of UserRepository."""

    def get_by_id(self, user_id: int) -> Optional[User]:
        try:
            django_user = DjangoUser.objects.get(id=user_id)
            return self._to_domain_entity(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_username(self, username: str) -> Optional[User]:
        try:
            django_user = DjangoUser.objects.get(username=username)
            return self._to_domain_entity(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Optional[User]:
        try:
            django_user = DjangoUser.objects.get(email=email)
            return self._to_domain_entity(django_user)
        except DjangoUser.DoesNotExist:
            return None

    def create(self, user: User) -> User:
        django_user = DjangoUser.objects.create_user(
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        return self._to_domain_entity(django_user)

    def update(self, user: User) -> User:
        django_user = DjangoUser.objects.get(id=user.id)
        django_user.username = user.username
        django_user.email = user.email
        django_user.first_name = user.first_name
        django_user.last_name = user.last_name
        django_user.is_active = user.is_active
        django_user.save()
        return self._to_domain_entity(django_user)

    def get_all(self) -> List[User]:
        django_users = DjangoUser.objects.all()
        return [self._to_domain_entity(u) for u in django_users]

    def _to_domain_entity(self, django_user: DjangoUser) -> User:
        return User(
            id=django_user.id,
            username=django_user.username,
            email=django_user.email,
            first_name=django_user.first_name,
            last_name=django_user.last_name,
            is_active=django_user.is_active,
            date_joined=django_user.date_joined,
            last_login=django_user.last_login,
        )


class DjangoUserProfileRepository(UserProfileRepository):
    """Django ORM implementation of UserProfileRepository."""

    def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        try:
            django_profile = DjangoUserProfile.objects.get(user_id=user_id)
            return self._to_domain_entity(django_profile)
        except DjangoUserProfile.DoesNotExist:
            return None

    def create(self, profile: UserProfile) -> UserProfile:
        django_profile = DjangoUserProfile.objects.create(
            user_id=profile.user_id,
            role=profile.role.value,
            bio=profile.bio,
            phone=profile.phone,
            date_of_birth=profile.date_of_birth,
            is_verified=profile.is_verified,
        )
        return self._to_domain_entity(django_profile)

    def update(self, profile: UserProfile) -> UserProfile:
        django_profile = DjangoUserProfile.objects.get(id=profile.id)
        django_profile.role = profile.role.value
        django_profile.bio = profile.bio
        django_profile.phone = profile.phone
        django_profile.date_of_birth = profile.date_of_birth
        django_profile.is_verified = profile.is_verified
        django_profile.save()
        return self._to_domain_entity(django_profile)

    def get_users_by_role(self, role: UserRole) -> List[UserProfile]:
        django_profiles = DjangoUserProfile.objects.filter(role=role.value)
        return [self._to_domain_entity(p) for p in django_profiles]

    def _to_domain_entity(self, django_profile: DjangoUserProfile) -> UserProfile:
        avatar_url = ""
        if django_profile.avatar:
            try:
                avatar_url = str(django_profile.avatar.url)
            except:
                avatar_url = "/static/images/default-avatar.svg"

        return UserProfile(
            id=django_profile.id,
            user_id=django_profile.user_id,
            role=UserRole(django_profile.role),
            bio=django_profile.bio,
            avatar_url=avatar_url,
            phone=django_profile.phone,
            date_of_birth=django_profile.date_of_birth,
            is_verified=django_profile.is_verified,
            created_at=django_profile.created_at,
            updated_at=django_profile.updated_at,
        )


class DjangoNewsRepository(NewsRepository):
    """Django ORM implementation of NewsRepository."""

    def get_by_id(self, news_id: int) -> Optional[News]:
        try:
            django_news = DjangoNews.objects.get(id=news_id)
            return self._to_domain_entity(django_news)
        except DjangoNews.DoesNotExist:
            return None

    def get_by_slug(self, slug: str) -> Optional[News]:
        try:
            django_news = DjangoNews.objects.get(slug=slug)
            return self._to_domain_entity(django_news)
        except DjangoNews.DoesNotExist:
            return None

    def create(self, news: News) -> News:
        django_news = DjangoNews.objects.create(
            title=news.title,
            slug=news.slug,
            content=news.content,
            excerpt=news.excerpt,
            featured_image=news.featured_image_url,
            author_id=news.author_id,
            category_id=news.category_id,
            status=news.status.value,
            priority=news.priority.value,
            meta_description=news.meta_description,
            meta_keywords=news.meta_keywords,
        )
        
        # Set tags
        if news.tag_ids:
            django_news.tags.set(news.tag_ids)
        
        return self._to_domain_entity(django_news)

    def update(self, news: News) -> News:
        django_news = DjangoNews.objects.get(id=news.id)
        django_news.title = news.title
        django_news.slug = news.slug
        django_news.content = news.content
        django_news.excerpt = news.excerpt
        django_news.featured_image = news.featured_image_url
        django_news.category_id = news.category_id
        django_news.status = news.status.value
        django_news.priority = news.priority.value
        django_news.reviewed_by_id = news.reviewed_by_id
        django_news.review_notes = news.review_notes
        django_news.reviewed_at = news.reviewed_at
        django_news.published_at = news.published_at
        django_news.meta_description = news.meta_description
        django_news.meta_keywords = news.meta_keywords
        django_news.save()
        
        # Update tags
        if news.tag_ids is not None:
            django_news.tags.set(news.tag_ids)
        
        return self._to_domain_entity(django_news)

    def delete(self, news_id: int) -> bool:
        try:
            DjangoNews.objects.get(id=news_id).delete()
            return True
        except DjangoNews.DoesNotExist:
            return False

    def get_by_status(self, status: NewsStatus) -> List[News]:
        django_news_list = DjangoNews.objects.filter(status=status.value)
        return [self._to_domain_entity(n) for n in django_news_list]

    def get_by_author(self, author_id: int) -> List[News]:
        django_news_list = DjangoNews.objects.filter(author_id=author_id)
        return [self._to_domain_entity(n) for n in django_news_list]

    def get_by_category(self, category_id: int) -> List[News]:
        django_news_list = DjangoNews.objects.filter(category_id=category_id)
        return [self._to_domain_entity(n) for n in django_news_list]

    def search(self, query: str, filters: dict = None) -> List[News]:
        from django.db.models import Q
        queryset = DjangoNews.objects.all()
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query)
            )
        
        if filters:
            if filters.get('category_id'):
                queryset = queryset.filter(category_id=filters['category_id'])
            if filters.get('tag_id'):
                queryset = queryset.filter(tags__id=filters['tag_id'])
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
        
        return [self._to_domain_entity(n) for n in queryset.distinct()]

    def get_published(self, filters: dict = None) -> List[News]:
        queryset = DjangoNews.objects.filter(status='published')
        
        if filters:
            if filters.get('category_id'):
                queryset = queryset.filter(category_id=filters['category_id'])
            if filters.get('tag_id'):
                queryset = queryset.filter(tags__id=filters['tag_id'])
            if filters.get('search'):
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(title__icontains=filters['search']) |
                    Q(content__icontains=filters['search'])
                )
        
        return [self._to_domain_entity(n) for n in queryset.distinct().order_by('-published_at')]

    def _to_domain_entity(self, django_news: DjangoNews) -> News:
        featured_image_url = ""
        if django_news.featured_image:
            try:
                featured_image_url = str(django_news.featured_image.url)
            except:
                featured_image_url = "/static/images/default-news.svg"

        tag_ids = list(django_news.tags.values_list('id', flat=True))

        return News(
            id=django_news.id,
            title=django_news.title,
            slug=django_news.slug,
            content=django_news.content,
            excerpt=django_news.excerpt,
            featured_image_url=featured_image_url,
            author_id=django_news.author_id,
            category_id=django_news.category_id,
            tag_ids=tag_ids,
            status=NewsStatus(django_news.status),
            priority=NewsStatus(django_news.priority) if hasattr(NewsStatus, django_news.priority.upper()) else NewsStatus.DRAFT,
            reviewed_by_id=django_news.reviewed_by_id,
            review_notes=django_news.review_notes,
            reviewed_at=django_news.reviewed_at,
            published_at=django_news.published_at,
            created_at=django_news.created_at,
            updated_at=django_news.updated_at,
            view_count=django_news.view_count,
            like_count=django_news.like_count,
            meta_description=django_news.meta_description,
            meta_keywords=django_news.meta_keywords,
        )


class DjangoCategoryRepository(CategoryRepository):
    """Django ORM implementation of CategoryRepository."""

    def get_by_id(self, category_id: int) -> Optional[Category]:
        try:
            from api.models import Category as DjangoCategory
            django_category = DjangoCategory.objects.get(id=category_id)
            return self._to_domain_entity(django_category)
        except DjangoCategory.DoesNotExist:
            return None

    def get_by_slug(self, slug: str) -> Optional[Category]:
        try:
            from api.models import Category as DjangoCategory
            django_category = DjangoCategory.objects.get(slug=slug)
            return self._to_domain_entity(django_category)
        except DjangoCategory.DoesNotExist:
            return None

    def create(self, category: Category) -> Category:
        from api.models import Category as DjangoCategory
        django_category = DjangoCategory.objects.create(
            name=category.name,
            slug=category.slug,
            description=category.description,
            is_active=category.is_active,
        )
        return self._to_domain_entity(django_category)

    def update(self, category: Category) -> Category:
        from api.models import Category as DjangoCategory
        django_category = DjangoCategory.objects.get(id=category.id)
        django_category.name = category.name
        django_category.slug = category.slug
        django_category.description = category.description
        django_category.is_active = category.is_active
        django_category.save()
        return self._to_domain_entity(django_category)

    def get_all_active(self) -> List[Category]:
        from api.models import Category as DjangoCategory
        django_categories = DjangoCategory.objects.filter(is_active=True)
        return [self._to_domain_entity(c) for c in django_categories]

    def _to_domain_entity(self, django_category) -> Category:
        return Category(
            id=django_category.id,
            name=django_category.name,
            slug=django_category.slug,
            description=django_category.description,
            is_active=django_category.is_active,
            created_at=django_category.created_at,
            updated_at=django_category.updated_at,
        )


class DjangoTagRepository(TagRepository):
    """Django ORM implementation of TagRepository."""

    def get_by_id(self, tag_id: int) -> Optional[Tag]:
        try:
            from api.models import Tag as DjangoTag
            django_tag = DjangoTag.objects.get(id=tag_id)
            return self._to_domain_entity(django_tag)
        except DjangoTag.DoesNotExist:
            return None

    def get_by_ids(self, tag_ids: List[int]) -> List[Tag]:
        from api.models import Tag as DjangoTag
        django_tags = DjangoTag.objects.filter(id__in=tag_ids)
        return [self._to_domain_entity(t) for t in django_tags]

    def create(self, tag: Tag) -> Tag:
        from api.models import Tag as DjangoTag
        django_tag = DjangoTag.objects.create(
            name=tag.name,
            slug=tag.slug,
        )
        return self._to_domain_entity(django_tag)

    def get_all(self) -> List[Tag]:
        from api.models import Tag as DjangoTag
        django_tags = DjangoTag.objects.all()
        return [self._to_domain_entity(t) for t in django_tags]

    def _to_domain_entity(self, django_tag) -> Tag:
        return Tag(
            id=django_tag.id,
            name=django_tag.name,
            slug=django_tag.slug,
            created_at=django_tag.created_at,
        )
