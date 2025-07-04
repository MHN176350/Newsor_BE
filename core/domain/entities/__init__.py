"""
Domain entities representing the core business concepts.
These are pure Python classes without any framework dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum


class UserRole(Enum):
    READER = "reader"
    WRITER = "writer"
    MANAGER = "manager"
    ADMIN = "admin"


class NewsStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class NewsPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class User:
    """User entity representing a user in the system."""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    is_active: bool = True
    date_joined: Optional[datetime] = None
    last_login: Optional[datetime] = None


@dataclass
class UserProfile:
    """User profile entity with extended user information."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    role: UserRole = UserRole.READER
    bio: str = ""
    avatar_url: str = ""
    phone: str = ""
    date_of_birth: Optional[datetime] = None
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Category:
    """News category entity."""
    id: Optional[int] = None
    name: str = ""
    slug: str = ""
    description: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Tag:
    """News tag entity."""
    id: Optional[int] = None
    name: str = ""
    slug: str = ""
    created_at: Optional[datetime] = None


@dataclass
class News:
    """News article entity."""
    id: Optional[int] = None
    title: str = ""
    slug: str = ""
    content: str = ""
    excerpt: str = ""
    featured_image_url: str = ""
    author_id: Optional[int] = None
    category_id: Optional[int] = None
    tag_ids: List[int] = None
    status: NewsStatus = NewsStatus.DRAFT
    priority: NewsPriority = NewsPriority.MEDIUM
    reviewed_by_id: Optional[int] = None
    review_notes: str = ""
    reviewed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    view_count: int = 0
    like_count: int = 0
    meta_description: str = ""
    meta_keywords: str = ""

    def __post_init__(self):
        if self.tag_ids is None:
            self.tag_ids = []


@dataclass
class Comment:
    """Comment entity for news articles."""
    id: Optional[int] = None
    article_id: Optional[int] = None
    author_id: Optional[int] = None
    content: str = ""
    parent_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    like_count: int = 0


@dataclass
class Like:
    """Like entity for news articles and comments."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    article_id: Optional[int] = None
    comment_id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class ArticleImage:
    """Image entity for news articles."""
    id: Optional[int] = None
    article_id: Optional[int] = None
    image_url: str = ""
    alt_text: str = ""
    caption: str = ""
    order: int = 0
    created_at: Optional[datetime] = None
