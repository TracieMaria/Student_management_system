# Tracy E-Learning System - Developer Documentation

This document provides technical details about the implementation of the Tracy E-Learning System for developers who will maintain or extend the platform.

## System Architecture

The application follows Django's MVT (Model-View-Template) architecture:

1. **Models**: Database structure and business logic
2. **Views**: Request handling and response generation 
3. **Templates**: Presentation layer with HTML rendering

## Core Components

### 1. Accounts App

The `accounts` app manages user authentication, registration, and profile management.

#### Key Files:
- `models.py`: Defines User Profile models for both students and instructors
- `views.py`: Handles authentication, registration, and profile updates
- `urls.py`: URL routing for account-related features

#### Database Models:
- Profile: Extends Django's User model with additional fields
- Student and Instructor profiles with specialized fields

### 2. Courses App

The `courses` app handles course creation, management, and organization.

#### Key Files:
- `models.py`: Defines Course, Module, and Category models
- `views.py`: Handles course creation, editing, and listing
- `urls.py`: URL routing for course-related features

#### Database Models:
- Course: Main course information (title, description, etc.)
- Module: Organizational units within courses
- Category: Classification for courses

### 3. Learning App

The `learning` app manages content delivery, assignments, and grading.

#### Key Files:
- `models.py`: Defines Content, Assignment, and Grade models
- `assignment_models.py`: Assignment-specific data structures
- `grade_models.py`: Grading-specific data structures
- `views.py`: Handles content delivery and assignment management
- `urls.py`: URL routing for learning-related features

#### Database Models:
- Content: Learning materials attached to modules
- Assignment: Tasks for student assessment
- Submission: Student responses to assignments
- Grade: Evaluation of student work

## Database Schema

The system uses Django's ORM with the following key relationships:

- User ⟷ Profile (One-to-One)
- Profile ⟷ Student/Instructor Profile (One-to-One)
- Instructor ⟷ Course (One-to-Many)
- Course ⟷ Module (One-to-Many)
- Module ⟷ Content (One-to-Many)
- Course ⟷ Student (Many-to-Many through enrollment)
- Assignment ⟷ Submission (One-to-Many)
- Submission ⟷ Grade (One-to-One)

## Authentication & Authorization

- Custom authentication backends are used where needed
- Permission decorators (`@login_required`) protect restricted views
- Role-based access control differentiates instructor vs student permissions

## File Storage

- Course thumbnails: Stored in `media/course_thumbnails/`
- Profile pictures: Stored in `media/profile_pics/`
- Content files: Stored in `media/content_files/`
- All file uploads are processed through Django's FileField

## Important Features

### Course Enrollment
Students can browse and enroll in courses through a simple enrollment process that creates a relationship between the student and course.

### Module Management
Instructors can organize course content into modules, which serve as organizational units for course materials.

### Content Types
The system supports various content types (text, file, image, video) through a content model with content-type-specific handling.

### Duration Handling
Course duration is stored as a timedelta and parsed from user-friendly formats using regex.

## Common Issues and Solutions

### Duration Field
- The system converts human-readable duration strings (e.g., "6 weeks") into timedelta objects
- Multiple migrations were needed to fix duration field issues (see migrations 0002-0004)

### Media Handling
- Media files require proper configuration in settings.py
- Ensure the media root and URL are configured properly

## Extending the Platform

### Adding New Content Types
1. Update the `Content` model to include the new content type
2. Create appropriate templates for rendering the new content type
3. Update content creation views to handle the new type

### Adding New Features
1. Determine if the feature belongs in an existing app or requires a new app
2. Define models, views, and templates following Django conventions
3. Update URL routing to include new views
4. Integrate the feature with the existing UI

## Deployment Considerations

For production deployment:
1. Set DEBUG=False in settings.py
2. Configure a production-ready database (PostgreSQL recommended)
3. Set up proper static and media file serving
4. Configure HTTPS with a valid SSL certificate
5. Use a production WSGI server like Gunicorn with Nginx

## Testing Strategy

### Unit Tests
The system includes unit tests for critical components:
- Model validation
- View authentication and permissions
- Form submission and validation

### Integration Tests
Integration tests verify:
- User registration and authentication flow
- Course creation and enrollment process
- Content creation and delivery

### Running Tests
```bash
python manage.py test
```

## Performance Considerations

### Database Optimization
- Appropriate indexes are created on frequently queried fields
- Select_related and prefetch_related are used to minimize database queries

### Caching
- The system uses Django's caching framework for:
  - Course listings
  - User profiles
  - Static content

### Media File Handling
- Large media files are stored efficiently
- Thumbnails are generated for images when appropriate

## Security Considerations

### CSRF Protection
- All forms implement Django's CSRF protection
- Custom middleware validates CSRF tokens

### XSS Prevention
- Template auto-escaping is enabled
- User-generated content is sanitized

### Authentication
- Password hashing uses Django's default PBKDF2 algorithm
- Password validation enforces security requirements

## Logging

The system uses Django's logging framework:
- ERROR level logs for critical issues
- INFO level logs for significant actions
- DEBUG level logs for detailed debugging

Log files are stored in `django_error.log` by default.

## Background Tasks

For long-running tasks like:
- Email notifications
- Report generation
- Media processing

The system can be configured to use Celery with Redis or RabbitMQ as a message broker.

## Third-Party Integrations

The system can integrate with:
- Payment processors for course purchases
- Video hosting services
- External authentication providers

## Internationalization

- The system uses Django's translation framework
- Template strings use the translation tags
- Language preferences are stored in user profiles

## Technical Debt and Future Improvements

Areas identified for future improvement:
- Enhanced reporting capabilities
- Real-time notifications using WebSockets
- Advanced content search functionality
- Mobile application integration

## Development Workflow

For developing new features:
1. Create a feature branch from main
2. Implement and test the feature
3. Write tests covering the new functionality
4. Submit a pull request for review
5. Address feedback and merge

## Environment Configuration

The system can be configured through environment variables:
- Database connection parameters
- Email settings
- Debug mode
- Media storage locations

This documentation provides a comprehensive overview of the Tracy E-Learning System's technical implementation. It should serve as a guide for developers working on maintenance or extending the platform with new features.
