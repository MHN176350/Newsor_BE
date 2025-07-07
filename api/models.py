from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField
from django.urls import reverse
from .cloudinary_utils import CloudinaryUtils
from unidecode import unidecode
from django.utils.text import slugify


class Category(models.Model):
    """
    News categories (Sports, Politics, Technology, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)


class Tag(models.Model):
    """
    News tags for more specific categorization
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)



class UserProfile(models.Model):
    """
    Extended user profile for role management
    """
    ROLE_CHOICES = [
        ('reader', 'Reader'),
        ('writer', 'Writer'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='reader')
    bio = models.TextField(max_length=500, blank=True)
    avatar = CloudinaryField('avatar', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def save(self, *args, **kwargs):
        """Override save to optimize Cloudinary URLs"""
        if self.avatar:
            # Convert CloudinaryField to string URL if needed
            avatar_url = self.avatar.url if hasattr(self.avatar, 'url') else str(self.avatar)
            # Optimize the URL for storage
            optimized_url = CloudinaryUtils.optimize_for_storage(avatar_url)
            # Only store the resource path, not the full URL
            if optimized_url != avatar_url and len(optimized_url) < 255:
                self.avatar = optimized_url
        super().save(*args, **kwargs)

    @property
    def avatar_url(self):
        """Get the full avatar URL for display"""
        if self.avatar:
            return CloudinaryUtils.restore_for_display(str(self.avatar))
        return None


class News(models.Model):
    """
    Main news article model
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField(help_text="Rich HTML content with embedded images")
    excerpt = models.TextField(max_length=300, help_text="Short description of the article")
    
    # Media
    featured_image = CloudinaryField('news_image', blank=True, null=True)
    
    # Relationships
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles')
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Manager review
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_articles'
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Publishing
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'published_at']),
            models.Index(fields=['author', 'created_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news_detail', kwargs={'slug': self.slug})

    def is_published(self):
        return self.status == 'published' and self.published_at and self.published_at <= timezone.now() 

    def save(self, *args, **kwargs):
        """Override save to optimize Cloudinary URLs"""
        if self.featured_image:
            # Convert CloudinaryField to string URL if needed
            image_url = self.featured_image.url if hasattr(self.featured_image, 'url') else str(self.featured_image)
            # Optimize the URL for storage
            optimized_url = CloudinaryUtils.optimize_for_storage(image_url)
            # Only store the resource path, not the full URL
            if optimized_url != image_url and len(optimized_url) < 255:
                self.featured_image = optimized_url
        super().save(*args, **kwargs)

    @property
    def featured_image_url(self):
        """Get the full featured image URL for display"""
        if self.featured_image:
            return CloudinaryUtils.restore_for_display(str(self.featured_image))
        return None


class ArticleImage(models.Model):
    """
    Images embedded in article content
    """
    article = models.ForeignKey(News, on_delete=models.CASCADE, related_name='embedded_images')
    image = CloudinaryField('article_content_image')
    alt_text = models.CharField(max_length=255, blank=True)
    caption = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.article.title}"

    def save(self, *args, **kwargs):
        """Override save to optimize Cloudinary URLs"""
        if self.image:
            # Convert CloudinaryField to string URL if needed
            image_url = self.image.url if hasattr(self.image, 'url') else str(self.image)
            # Optimize the URL for storage
            optimized_url = CloudinaryUtils.optimize_for_storage(image_url)
            # Only store the resource path, not the full URL
            if optimized_url != image_url and len(optimized_url) < 255:
                self.image = optimized_url
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        """Get the full image URL for display"""
        if self.image:
            return CloudinaryUtils.restore_for_display(str(self.image))
        return None


class Comment(models.Model):
    """
    Comments on news articles
    """
    article = models.ForeignKey(News, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', 'created_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.article.title}"




class Like(models.Model):
    """
    Likes for news articles and comments
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(News, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'article'],
                condition=models.Q(article__isnull=False),
                name='unique_article_like'
            ),
            models.UniqueConstraint(
                fields=['user', 'comment'],
                condition=models.Q(comment__isnull=False),
                name='unique_comment_like'
            ),
        ]

    def __str__(self):
        if self.article:
            return f"{self.user.username} likes {self.article.title}"
        return f"{self.user.username} likes comment"


class ReadingHistory(models.Model):
    """
    Track user reading history for analytics
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_history')
    article = models.ForeignKey(News, on_delete=models.CASCADE, related_name='readers')
    read_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-read_at']
        indexes = [
            models.Index(fields=['user', 'read_at']),
            models.Index(fields=['article', 'read_at']),
        ]

    def __str__(self):
        return f"{self.user.username} read {self.article.title}"


class NewsletterSubscription(models.Model):
    """
    Newsletter subscriptions
    """
    email = models.EmailField(unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email


class Notification(models.Model):
    """
    Notifications for users (especially managers)
    """
    NOTIFICATION_TYPES = [
        ('article_submitted', 'Article Submitted for Review'),
        ('article_approved', 'Article Approved'),
        ('article_rejected', 'Article Rejected'),
        ('article_published', 'Article Published'),
        ('comment_added', 'New Comment Added'),
        ('user_registered', 'New User Registered'),
        ('system', 'System Notification'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Optional related objects
    article = models.ForeignKey(News, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])