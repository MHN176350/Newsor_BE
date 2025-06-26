# Newsor API Documentation

## Base URL
```
http://localhost:8000/api/
```

## Authentication
The API supports both session-based authentication and basic authentication for REST endpoints.

## REST API Endpoints

### 1. User Registration

**Endpoint:** `POST /api/auth/register/`  
**Description:** Register a new user as a reader  
**Authentication:** Not required  

**Request Body:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123",
    "password_confirm": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Success Response (201):**
```json
{
    "success": true,
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_joined": "2025-06-26T14:30:00Z",
        "profile": {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "full_name": "John Doe",
            "role": "reader",
            "bio": "",
            "avatar": null,
            "phone": "",
            "date_of_birth": null,
            "is_verified": false,
            "created_at": "2025-06-26T14:30:00Z",
            "updated_at": "2025-06-26T14:30:00Z"
        }
    }
}
```

**Error Response (400):**
```json
{
    "success": false,
    "message": "Registration failed",
    "errors": {
        "username": ["A user with this username already exists."],
        "email": ["A user with this email already exists."],
        "password": ["This password is too short. It must contain at least 8 characters."]
    }
}
```

### 2. Get User Profile

**Endpoint:** `GET /api/auth/profile/`  
**Description:** Get current user's profile information  
**Authentication:** Required  

**Success Response (200):**
```json
{
    "success": true,
    "profile": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "role": "reader",
        "bio": "I love reading news!",
        "avatar": "https://res.cloudinary.com/...",
        "phone": "+1234567890",
        "date_of_birth": "1990-01-01",
        "is_verified": true,
        "created_at": "2025-06-26T14:30:00Z",
        "updated_at": "2025-06-26T14:35:00Z"
    }
}
```

### 3. Update User Profile

**Endpoint:** `PUT /api/auth/profile/update/` or `PATCH /api/auth/profile/update/`  
**Description:** Update current user's profile information  
**Authentication:** Required  

**Request Body (partial update with PATCH):**
```json
{
    "bio": "Updated bio text",
    "phone": "+1234567890",
    "date_of_birth": "1990-01-01"
}
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Profile updated successfully",
    "profile": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "role": "reader",
        "bio": "Updated bio text",
        "avatar": null,
        "phone": "+1234567890",
        "date_of_birth": "1990-01-01",
        "is_verified": false,
        "created_at": "2025-06-26T14:30:00Z",
        "updated_at": "2025-06-26T14:40:00Z"
    }
}
```

### 4. Check Username Availability

**Endpoint:** `POST /api/utils/check-username/`  
**Description:** Check if a username is available  
**Authentication:** Not required  

**Request Body:**
```json
{
    "username": "new_user"
}
```

**Success Response (200):**
```json
{
    "success": true,
    "username": "new_user",
    "available": true,
    "message": "Username is available"
}
```

### 5. Check Email Availability

**Endpoint:** `POST /api/utils/check-email/`  
**Description:** Check if an email is available  
**Authentication:** Not required  

**Request Body:**
```json
{
    "email": "newuser@example.com"
}
```

**Success Response (200):**
```json
{
    "success": true,
    "email": "newuser@example.com",
    "available": true,
    "message": "Email is available"
}
```

### 6. List Users

**Endpoint:** `GET /api/users/`  
**Description:** List users (filtered by role permissions)  
**Authentication:** Required  

**Success Response (200):**
```json
{
    "count": 10,
    "next": "http://localhost:8000/api/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "date_joined": "2025-06-26T14:30:00Z",
            "profile": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "role": "reader",
                "bio": "I love reading news!",
                "is_verified": true
            }
        }
    ]
}
```

### 7. Health Check

**Endpoint:** `GET /api/health/`  
**Description:** Check API health status  
**Authentication:** Not required  

**Success Response (200):**
```json
{
    "status": "healthy",
    "message": "Newsor API is running successfully"
}
```

### 8. Upload Image

**Endpoint:** `POST /api/upload-image/`  
**Description:** Upload an image to Cloudinary and get the URL  
**Authentication:** Not required  

**Request Body (form-data):**
```
image: [image file]
```

**Success Response (200):**
```json
{
    "success": true,
    "url": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/newsor/profiles/profile_abc123.jpg",
    "public_id": "newsor/profiles/profile_abc123"
}
```

**Error Response (400):**
```json
{
    "success": false,
    "error": "Image upload failed: Invalid image format"
}
```

### 9. Register User with Avatar
```

### Using the Django REST Framework Browser

Visit `http://localhost:8000/api/` in your browser to access the browsable API interface where you can:
- Test endpoints interactively
- View API documentation
- Make requests with form data

## Error Handling

All API endpoints follow a consistent error response format:

```json
{
    "success": false,
    "message": "Error description",
    "errors": {
        "field_name": ["Specific error message"]
    }
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created successfully
- `400`: Bad request (validation errors)
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not found
- `500`: Internal server error

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider adding rate limiting for security.

## CORS

CORS is configured to allow requests from frontend applications. Update the `CORS_ALLOWED_ORIGINS` setting for production use.
