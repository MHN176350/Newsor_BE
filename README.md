# Newsor - Django GraphQL News API

A comprehensive news management system built with Django, GraphQL (using Graphene), and PostgreSQL. This API supports role-based access control for readers, writers, managers, and admins.

## Features

### User Roles
- **Readers**: Can read news, like articles, leave comments
- **Writers**: Can create and manage their own news articles
- **Managers**: Review and approve/reject news articles before publication
- **Admins**: Full system management including user management and analytics

### Core Functionality
- **News Management**: Create, edit, publish news articles with categories and tags
- **Content Moderation**: Manager approval workflow for news publication
- **User Interaction**: Comments, likes, reading history tracking
- **Media Management**: Cloudinary integration for image storage
- **Analytics**: Track user reading patterns and engagement
- **Newsletter**: Email subscription management

## Technology Stack

- **Backend**: Django 5.2.3
- **API**: GraphQL with Graphene-Django
- **Database**: PostgreSQL
- **Media Storage**: Cloudinary
- **Environment Management**: python-decouple
- **CORS**: django-cors-headers

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd newsor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   # Django Configuration
   SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_HOSTS=

   # Database Configuration
   DB_NAME=newsor
   DB_USER=postgres
   DB_PASSWORD=your-password
   DB_HOST=localhost
   DB_PORT=5432

   # Cloudinary Configuration
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret

   # CORS Configuration
   CORS_ALLOW_ALL_ORIGINS=True
   ```

5. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run the server**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### GraphQL
- **GraphQL Playground**: `http://localhost:8000/graphql/`
- **GraphQL Endpoint**: `http://localhost:8000/graphql/`

### REST API
- **Health Check**: `http://localhost:8000/api/health/`
- **Admin Panel**: `http://localhost:8000/admin/`

## GraphQL Schema

### Queries
```graphql
query {
  # Basic queries
  hello(name: "World")
  
  # User queries
  users
  user(id: 1)
  userProfile(userId: 1)
  
  # News queries
  newsList(status: "published", categoryId: 1)
  newsArticle(id: 1)
  publishedNews
  
  # Category and Tag queries
  categories
  tags
  
  # Comments
  articleComments(articleId: 1)
  
  # Analytics
  userReadingHistory(userId: 1)
}
```

### Mutations
```graphql
mutation {
  createUser(
    username: "john_doe"
    email: "john@example.com"
    password: "securepassword"
    firstName: "John"
    lastName: "Doe"
  ) {
    user {
      id
      username
      email
    }
    success
    errors
  }
}
```

## Database Models

### Core Models
- **User**: Extended Django user model
- **UserProfile**: Role-based user profiles (Reader, Writer, Manager, Admin)
- **Category**: News categories (Sports, Politics, Technology, etc.)
- **Tag**: Article tags for detailed categorization
- **News**: Main news article model with workflow states
- **Comment**: User comments on articles
- **Like**: User likes for articles and comments
- **ReadingHistory**: Analytics for user reading patterns
- **NewsletterSubscription**: Email subscription management

### News Workflow States
- **Draft**: Initial creation by writer
- **Pending**: Submitted for manager review
- **Approved**: Approved by manager, ready for publishing
- **Published**: Live on the website
- **Rejected**: Rejected by manager with feedback
- **Archived**: Removed from active content

## Development

### Project Structure
```
newsor/
├── api/                    # Main API app
│   ├── models.py          # Database models
│   ├── schema.py          # GraphQL schema
│   ├── admin.py           # Django admin configuration
│   └── views.py           # API views
├── newsor/                # Django project settings
│   ├── settings.py        # Main settings
│   ├── urls.py           # URL configuration
│   └── schema.py         # Root GraphQL schema
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
└── manage.py             # Django management script
```

### Key Features Implementation

1. **Role-Based Access Control**
   - User profiles with different roles
   - Permission-based content access
   - Workflow management for content publication

2. **Content Management**
   - Rich text content support
   - Image upload via Cloudinary
   - SEO optimization fields
   - Category and tag system

3. **User Engagement**
   - Comment system with moderation
   - Like functionality
   - Reading history tracking
   - Newsletter subscriptions

4. **Analytics**
   - User reading patterns
   - Content performance metrics
   - Engagement tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team.
