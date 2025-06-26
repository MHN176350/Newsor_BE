# Copilot Instructions for Newsor Django GraphQL API

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

This is a Django GraphQL API project with the following specifications:

## Project Structure
- Django backend API with GraphQL support using Graphene-Django
- PostgreSQL database integration
- Apollo GraphQL compatibility
- CORS support for frontend integration

## Key Technologies
- **Framework**: Django
- **GraphQL**: Graphene-Django
- **Database**: PostgreSQL with psycopg2
- **Environment**: python-decouple for configuration
- **CORS**: django-cors-headers

## Development Guidelines
- Follow Django best practices for models, views, and serializers
- Use GraphQL mutations and queries for API endpoints
- Implement proper error handling and validation
- Use environment variables for sensitive configuration
- Follow RESTful principles where GraphQL doesn't apply
- Ensure proper database migrations and relationships

## Code Style
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Add docstrings to functions and classes
- Keep business logic in models and services
- Use Django's built-in authentication and permissions
