# Medical Data Hub - Architecture Documentation

## Overview

The Medical Data Hub is an AI-powered patient medical data management application built using modern, secure technologies. The application is designed with a clear separation of concerns, following best practices for security, maintainability, and scalability.

## Tech Stack

* **Backend**: Python 3.11 with FastAPI
* **Authentication**: Supabase
* **Database**: PostgreSQL with SQLAlchemy ORM
* **Frontend**: React Native (Mobile)
* **Cloud Platform**: Google Cloud Platform (GCP)

## Directory Structure

```
/
├── backend/                    # Backend API codebase
│   ├── alembic/                # Database migration scripts
│   ├── app/                    # Application code
│   │   ├── api/                # API endpoints
│   │   │   ├── endpoints/      # API route handlers
│   │   ├── core/               # Core functionality
│   │   │   ├── auth.py         # Authentication logic
│   │   │   ├── config.py       # Application configuration
│   │   │   └── logging_config.py # Logging configuration
│   │   ├── db/                 # Database management
│   │   │   └── session.py      # Database session management
│   │   ├── middleware/         # Middleware components
│   │   │   ├── rate_limit.py   # Rate limiting middleware
│   │   │   └── security.py     # Security headers middleware
│   │   ├── models/             # Data models
│   │   │   └── user.py         # User data model
│   │   ├── schemas/            # Pydantic schemas
│   │   └── utils/              # Utility functions
│   ├── tests/                  # Test directory
│   │   ├── unit/               # Unit tests
│   │   ├── integration/        # Integration tests
│   │   └── security/           # Security tests
│   ├── Dockerfile              # Docker configuration for backend
│   ├── alembic.ini             # Alembic configuration
│   ├── requirements.txt        # Python dependencies
│   └── pytest.ini              # Pytest configuration
├── frontend/                   # Frontend codebase
├── memory-bank/                # Documentation and planning
└── package.json                # Root package.json
```

## Core Components

### 1. FastAPI Application (`backend/app/main.py`)

The main entry point of the backend application. It initializes the FastAPI app, configures middleware, sets up routes, and handles exception management. The application is designed to run on Python 3.11 to leverage modern language features and improved performance.

Key components:
- CORS configuration
- Security headers middleware
- Rate limiting integration
- Structured logging setup
- Exception handling
- API router registration

### 2. Authentication (`backend/app/core/auth.py`)

Handles user authentication using Supabase. It verifies JWT tokens provided in request headers and extracts user information for authorized endpoints.

Key components:
- JWT token verification with Supabase
- User identification and authorization
- Comprehensive error handling
- Security logging for authentication events

### 3. Configuration (`backend/app/core/config.py`)

Manages application configuration using environment variables with sensible defaults. Uses Pydantic Settings for validation and type safety.

Key components:
- Environment-specific settings
- Authentication configuration
- Database connection parameters
- Security settings
- API configuration

### 4. Database (`backend/app/db/session.py`)

Manages database connections and sessions using SQLAlchemy. Configured with connection pooling for optimized performance.

Key components:
- SQLAlchemy engine configuration
- Connection pooling settings
- Session management
- Base model class for ORM models

### 5. Models (`backend/app/models/`)

Contains SQLAlchemy ORM models that represent database tables. Currently includes the User model for authentication and user management.

### 6. API Endpoints (`backend/app/api/endpoints/`)

Contains route handlers organized by functionality:
- `health.py`: Health check endpoint to verify API status
- `me.py`: User information endpoint that requires authentication

### 7. Middleware (`backend/app/middleware/`)

Contains middleware components:
- `security.py`: Adds security headers to responses
- `rate_limit.py`: Implements rate limiting to prevent abuse

### 8. Testing (`backend/tests/`)

Contains test suites organized by type:
- Unit tests for individual components
- Integration tests for API endpoints
- Security tests for vulnerability checking

## Authentication Flow

1. User authenticates with Supabase (frontend)
2. Supabase issues a JWT token
3. Frontend includes the token in the Authorization header
4. Backend `verify_token` middleware validates the token
5. If valid, endpoint handler receives the decoded token data
6. User information is extracted from the token

## Security Features

1. **JWT Authentication**: Secure token-based authentication with Supabase
2. **Security Headers**: Protection against common web vulnerabilities
3. **Rate Limiting**: Prevention of abuse and DoS attacks
4. **Structured Logging**: Comprehensive logging for security events
5. **Input Validation**: Pydantic models ensure data validation
6. **Exception Handling**: Secure error responses that don't leak information
7. **Database Connection Pooling**: Secure and efficient database access

## Development Environment

The application is designed to be developed with Python 3.11 and uses modern tooling:
- Pytest for testing
- Alembic for database migrations
- Docker for containerization
- Environment variables for configuration

**Important Note**: When running commands locally, make sure to use `python3` explicitly to target Python 3.11. The project requires Python 3.11 for certain language features and library compatibility.

```bash
# Use this command to verify your Python version
python3 --version  # Should show Python 3.11.x

# Run tests with Python 3.11
python3 -m pytest backend/tests/

# Start the backend server with Python 3.11
python3 -m uvicorn app.main:app --reload
```

## Next Steps

As development progresses, this architecture will expand to include:
- Document storage and processing
- AI/ML integration for data extraction
- Advanced querying capabilities
- Enhanced security features
