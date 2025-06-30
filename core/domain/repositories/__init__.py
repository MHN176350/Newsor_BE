"""
Domain repository interfaces.
These define the contracts for data access without implementation details.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import User, UserProfile, News, Category, Tag, Comment, Like, ArticleImage
from ..entities import NewsStatus, UserRole


class UserRepository(ABC):
    """Abstract repository for User entities."""

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def create(self, user: User) -> User:
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        pass

    @abstractmethod
    def get_all(self) -> List[User]:
        pass


class UserProfileRepository(ABC):
    """Abstract repository for UserProfile entities."""

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        pass

    @abstractmethod
    def create(self, profile: UserProfile) -> UserProfile:
        pass

    @abstractmethod
    def update(self, profile: UserProfile) -> UserProfile:
        pass

    @abstractmethod
    def get_users_by_role(self, role: UserRole) -> List[UserProfile]:
        pass


class NewsRepository(ABC):
    """Abstract repository for News entities."""

    @abstractmethod
    def get_by_id(self, news_id: int) -> Optional[News]:
        pass

    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[News]:
        pass

    @abstractmethod
    def create(self, news: News) -> News:
        pass

    @abstractmethod
    def update(self, news: News) -> News:
        pass

    @abstractmethod
    def delete(self, news_id: int) -> bool:
        pass

    @abstractmethod
    def get_by_status(self, status: NewsStatus) -> List[News]:
        pass

    @abstractmethod
    def get_by_author(self, author_id: int) -> List[News]:
        pass

    @abstractmethod
    def get_by_category(self, category_id: int) -> List[News]:
        pass

    @abstractmethod
    def search(self, query: str, filters: dict = None) -> List[News]:
        pass

    @abstractmethod
    def get_published(self, filters: dict = None) -> List[News]:
        pass


class CategoryRepository(ABC):
    """Abstract repository for Category entities."""

    @abstractmethod
    def get_by_id(self, category_id: int) -> Optional[Category]:
        pass

    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[Category]:
        pass

    @abstractmethod
    def create(self, category: Category) -> Category:
        pass

    @abstractmethod
    def update(self, category: Category) -> Category:
        pass

    @abstractmethod
    def get_all_active(self) -> List[Category]:
        pass


class TagRepository(ABC):
    """Abstract repository for Tag entities."""

    @abstractmethod
    def get_by_id(self, tag_id: int) -> Optional[Tag]:
        pass

    @abstractmethod
    def get_by_ids(self, tag_ids: List[int]) -> List[Tag]:
        pass

    @abstractmethod
    def create(self, tag: Tag) -> Tag:
        pass

    @abstractmethod
    def get_all(self) -> List[Tag]:
        pass


class CommentRepository(ABC):
    """Abstract repository for Comment entities."""

    @abstractmethod
    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        pass

    @abstractmethod
    def create(self, comment: Comment) -> Comment:
        pass

    @abstractmethod
    def get_by_article(self, article_id: int) -> List[Comment]:
        pass


class ArticleImageRepository(ABC):
    """Abstract repository for ArticleImage entities."""

    @abstractmethod
    def create(self, image: ArticleImage) -> ArticleImage:
        pass

    @abstractmethod
    def get_by_article(self, article_id: int) -> List[ArticleImage]:
        pass

    @abstractmethod
    def delete(self, image_id: int) -> bool:
        pass
