# Tracy's E-Learning System Documentation django project

This comprehensive documentation provides everything you need to understand, use, develop, and deploy the Tracy E-Learning System.

![Tracy's E-Learning System Banner](/docs/screenshots/banner.png)

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Project Structure](#project-structure)
5. [System Architecture](#system-architecture)
6. [Core Components](#core-components)
7. [Database Schema](#database-schema)
8. [User Guide](#user-guide)
9. [Deployment Guide](#deployment-guide)
10. [Contributing](#contributing)
11. [License](#license)

## Introduction

Tracy E-Learning System is a modern learning management system built with Django that enables instructors to create and manage courses while allowing students to enroll and track their progress.

![Dashboard Screenshot](/docs/screenshots/dashboard.png)

## Features

- User authentication and profile management
- Course creation and management
- Module organization with drag-and-drop ordering
- Multiple content types support (text, video, quiz, assignments)
- Student progress tracking
- Responsive modern UI design

![Course List Screenshot](/docs/screenshots/course_list.png)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Process

1. Clone the repository:
```bash
git clone https://github.com/TracieMaria/Student_management_system.git
cd Student_management_system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply database migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser (admin account):
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

The application will be available at http://localhost:8000

![Registration Screenshot](/docs/screenshots/registration.png)

## Project Structure

```
tracy/
├── accounts/            # User authentication and profiles
├── courses/             # Course management
├── learning/            # Content delivery and progress tracking
├── elearning_system/    # Project settings
├── static/              # Static files (CSS, JS, images)
├── templates/           # HTML templates
├── media/               # User-uploaded files
└── docs/                # Documentation
```

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



## User Guide

### For Administrators
1. Access the admin interface at `/admin`
2. Manage users, courses, and system settings

### For Instructors
1. Create an account and get instructor privileges
2. Create and manage courses
3. Add modules and content
4. Track student progress


### For Students
1. Register an account
2. Browse available courses
3. Enroll in courses
4. Access course content and track progress


## Deployment Guide

### Prerequisites

- A server running Linux (Ubuntu/Debian recommended)
- Python 3.8 or higher
- PostgreSQL 12 or higher
- Nginx
- Domain name (optional, but recommended)
- SSL certificate (strongly recommended for production)

### Step 1: Set Up the Server

#### Update the system
```bash
sudo apt update
sudo apt upgrade -y
```

#### Install required packages
```bash
sudo apt install -y python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl
```

#### Set up PostgreSQL database
```bash
sudo -u postgres psql
```

In the PostgreSQL shell:
```sql
CREATE DATABASE tracy_lms;
CREATE USER tracy_user WITH PASSWORD 'secure_password';
ALTER ROLE tracy_user SET client_encoding TO 'utf8';
ALTER ROLE tracy_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE tracy_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE tracy_lms TO tracy_user;
\q
```

### Step 2: Clone and Configure the Application

#### Create a directory for the application
```bash
mkdir -p /var/www/tracy_lms
cd /var/www/tracy_lms
```

#### Clone the repository
```bash
git clone <repository-url> .
```

#### Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Install requirements
```bash
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

#### Create a production settings file
Create a file called `production_settings.py` in the `elearning_system` folder with appropriate production settings.

### Step 3: Configure Gunicorn

#### Create a systemd service file
```bash
sudo nano /etc/systemd/system/tracy_lms.service
```

Add the following content:
```
[Unit]
Description=Tracy LMS Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/tracy_lms
ExecStart=/var/www/tracy_lms/venv/bin/gunicorn --workers 3 --bind unix:/var/www/tracy_lms/tracy_lms.sock elearning_system.wsgi:application --env DJANGO_SETTINGS_MODULE=elearning_system.production_settings

[Install]
WantedBy=multi-user.target
```

#### Start and enable the service
```bash
sudo systemctl start tracy_lms
sudo systemctl enable tracy_lms
```

### Step 4: Configure Nginx

#### Create an Nginx server block
```bash
sudo nano /etc/nginx/sites-available/tracy_lms
```

Add the following content:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/tracy_lms/static/;
    }

    location /media/ {
        alias /var/www/tracy_lms/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/tracy_lms/tracy_lms.sock;
    }
}
```

#### Enable the server block
```bash
sudo ln -s /etc/nginx/sites-available/tracy_lms /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### Step 5: Secure with SSL (using Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts to complete the SSL setup.

## Contributing

Thank you for considering contributing to the Tracy E-Learning System!

### Code of Conduct

By participating in this project, you agree to abide by our code of conduct:

- Be respectful and inclusive in your language and actions
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards other community members

### How to Contribute

#### Reporting Bugs

If you find a bug, please create an issue with detailed information about the problem.

#### Suggesting Enhancements

When suggesting enhancements, please include a clear description and explanation of why the enhancement would be useful.

#### Pull Requests

1. Fork the repository
2. Create a new branch from `main` for your feature/fix
3. Make your changes
4. Write or update tests for your changes
5. Ensure all tests and linting pass
6. Submit a pull request to the `main` branch

### Development Setup

1. Fork and clone the repository
2. Set up a virtual environment
3. Install development dependencies
4. Set up the database
5. Create a superuser
6. Run the development server

### Testing

Run tests with:
```bash
python manage.py test
```

### Code Style

Follow Django's coding style as documented in the [Django Coding Style Guide](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/).

## License

This project is licensed under the MIT License:

MIT License

Copyright (c) 2025 Tracy's E-Learning System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
