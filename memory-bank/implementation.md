# Implementation Plan: Medical Data Hub - Base Application

This plan outlines the initial steps to build the foundational structure of the AI-Powered Patient Medical Data Hub application. Each step includes specific instructions and a validation test. **No code implementation is required in this plan; it serves as a detailed instruction set.**

**Target Audience:** AI Developers
**Goal:** Establish a runnable base application with core backend, frontend, database, and authentication setup.

---

## Phase 0: Prerequisites & Environment Setup

*   **Instruction:** Ensure local development environments have necessary tools installed with the following recommended versions:
    * **Python 3.11.x** (Better performance, improved error messages, good FastAPI compatibility)
    * **Node.js 18.x LTS** (Long-term support until April 2025, stable npm version)
    * **npm 9.x or 10.x** (comes with Node 18)
    * **React Native 0.72.x or 0.73.x** (stable versions with good community support)
    * **Xcode 14.x or 15.x** (for iOS development)
    * **Android Studio Hedgehog (2023.1.1)** with SDK 33+
    * **Google Cloud SDK 400.0.0+** (latest stable version)
    * **Docker 24.x**
*   **Validation:** Run `python --version`, `node --version`, `npm --version`, `gcloud --version`, `docker --version`, `npx react-native doctor` and confirm versions match or exceed the recommended versions above.

*   **Instruction:** Set up a new Google Cloud Platform (GCP) project. Enable necessary APIs: Cloud SQL Admin API, Cloud Run Admin API, Cloud Storage API, Cloud Vision API, Cloud Healthcare API, Vertex AI API, Cloud Tasks API, Identity Platform API (or Firebase equivalent), Cloud Armor API, Logging API, Secret Manager API, Cloud Monitoring API. Note the Project ID.
*   **Validation:** Navigate to the GCP console for the created project. Verify the listed APIs are enabled in the "APIs & Services" > "Enabled APIs & services" section.

*   **Instruction:** Set up a new Firebase project, link it to the GCP project created above. Enable Firebase Authentication (Email/Password provider with email verification required). Enable Firebase App Check to prevent API abuse. Configure Firebase Security Rules for future Firestore/Storage use. Note the Firebase project configuration details (apiKey, authDomain, etc.).
*   **Validation:** In the Firebase console, confirm the project exists, is linked to the correct GCP project (under Project Settings > Integrations), and the Email/Password sign-in provider is enabled with email verification required under Authentication > Sign-in method. Verify App Check is enabled. Retrieve the web configuration snippet.

*   **Instruction:** Initialize a Git repository for the project. Create top-level directories: `backend/` and `frontend/`. Set up `.gitignore` to exclude environment files, build artifacts, and dependency directories.
*   **Validation:** Confirm the Git repository is initialized and the `backend/` and `frontend/` directories exist at the root level using `git status` and `ls`.

*   **Instruction:** Create `package.json` and `requirements.txt` files with exact version pinning to ensure consistent development/deployment environments.
*   **Validation:** Verify these files exist and contain appropriate version constraints.

---

## Phase 1: Backend Foundation (FastAPI)

*   **Step 1.1: Initialize FastAPI Project Structure**
    *   **Instruction:** Inside the `backend/` directory, create a standard FastAPI project structure. Include directories like `app/`, `app/api/`, `app/core/`, `app/models/`, `app/schemas/`, `app/db/`, `app/middleware/`, `tests/`. Create an initial `app/main.py`.
    *   **Validation:** Verify the directory structure exists within `backend/`. The `app/main.py` file should contain minimal FastAPI app instantiation boilerplate (`app = FastAPI()`).

*   **Step 1.2: Add Basic Dependencies**
    *   **Instruction:** Create a `backend/requirements.txt` file. Add core dependencies: `fastapi`, `uvicorn[standard]`, `python-dotenv`, `pydantic`, `sqlalchemy` (for later DB interaction), `psycopg2-binary` (PostgreSQL driver), `google-cloud-logging`, `firebase-admin`, `slowapi` (for rate limiting), `pytest` (for testing), `httpx` (for HTTP client testing), `alembic` (for DB migrations).
    *   **Validation:** Create a virtual environment, install dependencies using `pip install -r requirements.txt`, and ensure the installation completes without errors.

*   **Step 1.3: Implement Health Check Endpoint**
    *   **Instruction:** In `app/main.py` or a dedicated router (e.g., `app/api/endpoints/health.py`), define a simple GET endpoint (e.g., `/api/v1/health`) that returns a JSON response like `{"status": "ok"}`. Include this router in `main.py`.
    *   **Validation:** Run the backend locally using `uvicorn app.main:app --reload`. Access `http://127.0.0.1:8000/api/v1/health` (or the appropriate URL/port) in a browser or using `curl`. Verify the `{"status": "ok"}` JSON response is received with a 200 status code.

*   **Step 1.4: Configure Basic Logging**
    *   **Instruction:** Configure basic structured logging using `google-cloud-logging` in `app/core/logging_config.py` (or similar). Set up middleware in `app/main.py` to log incoming requests. Ensure logs are output to the console during local development. Configure detailed logging for authentication attempts and errors.
    *   **Validation:** Run the backend locally. Make a request to the health check endpoint. Verify that request details (method, path, status code) are printed to the console in a structured format (JSON).

*   **Step 1.5: Set up Security Headers Middleware**
    *   **Instruction:** Implement middleware that adds security headers to all responses (Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, etc.) in `app/middleware/security.py`. Add CORS configuration to allow only specific origins in production.
    *   **Validation:** Run the backend locally and make a request. Use browser developer tools or curl with `-v` flag to verify that security headers are present in the response.

*   **Step 1.6: Implement Rate Limiting Middleware**
    *   **Instruction:** Using the `slowapi` package, implement rate limiting middleware in `app/middleware/rate_limit.py`. Configure default limits (e.g., 60 requests per minute per IP) and more restrictive limits for specific endpoints (authentication, data submission) to be applied later.
    *   **Validation:** Run the backend locally. Make rapid repeated requests to an endpoint with rate limiting applied. Verify that after exceeding the limit, requests receive a 429 Too Many Requests response.

*   **Step 1.7: Set up Dockerfile for Backend**
    *   **Instruction:** Create a `backend/Dockerfile` that sets up a Python environment, copies the application code, installs dependencies from `requirements.txt`, and specifies the command to run the application using `uvicorn`.
    *   **Validation:** Build the Docker image using `docker build -t medical-app-backend .` from the `backend/` directory. Ensure the build completes successfully. Run the container `docker run -p 8000:8000 medical-app-backend` and test the health check endpoint via `curl http://127.0.0.1:8000/api/v1/health`. Verify the expected response.

---

## Phase 2: Database Setup (Cloud SQL)

*   **Step 2.1: Provision Cloud SQL Instance**
    *   **Instruction:** Using the GCP console or `gcloud`, provision a Cloud SQL for PostgreSQL instance. Choose appropriate settings (version 15+, region e.g., `asia-south1`, machine type - start small). Set a password for the default `postgres` user. Create an initial database (e.g., `medical_data_db`). Configure public IP access temporarily *only* for initial testing from local machine (add your IP), or configure the Cloud SQL Auth Proxy for secure local connections. Enable database audit logging.
    *   **Validation:** Confirm the Cloud SQL instance is running in the GCP console. Note the instance connection name, database name, and user password. Attempt to connect using `psql` or a GUI tool (e.g., DBeaver) either via public IP (if configured) or using the Cloud SQL Auth Proxy. Successful connection validates setup. Verify audit logging is enabled.

*   **Step 2.2: Configure Database Schema (Users Table Only)**
    *   **Instruction:** Define the SQLAlchemy model for the `users` table in `app/models/user.py` based on the `tech-stack.md` definition (`user_id`, `auth_provider_id`, `email`, `created_at`, `updated_at`). Add a `last_login` timestamp column for security monitoring. Set up Alembic for migrations and create the initial migration script.
    *   **Validation:** Connect to the database (using `psql` or GUI tool) and verify that the `users` table exists with the correct columns and types (`\d users` in `psql`).

*   **Step 2.3: Implement Backend Database Connection Logic**
    *   **Instruction:** In `app/db/session.py` (or similar), implement logic to establish a database session using SQLAlchemy. Read database connection details (URL including user, password, host, dbname) securely from environment variables (use `.env` file locally, managed secrets in deployment). Implement connection pooling with appropriate limits (e.g., max 10 connections per app instance).
    *   **Validation:** Add a temporary test script or endpoint that attempts to create a database session using the implemented logic. Run it locally (ensure environment variables or `.env` file is set up, potentially using Cloud SQL Auth Proxy if not using public IP). Verify a connection can be established without errors.

*   **Step 2.4: Create Basic CRUD Endpoint for Users (Internal/Test)**
    *   **Instruction:** Implement basic CRUD (Create, Read) operations for the `users` table via a *temporary*, *internal-only* API endpoint (e.g., `/api/v1/_internal/users`). This endpoint should use the database session logic from Step 2.3. **This is for testing database connectivity via the API, not for actual user management.** Implement proper input validation and sanitization for all fields.
    *   **Validation:** Run the backend locally. Use `curl` or an API client (like Postman/Insomnia) to POST a new user record (e.g., with a test email and auth ID) to the internal endpoint. Then, perform a GET request to retrieve users and verify the newly created user is returned. Check the database directly to confirm the record exists.

---

## Phase 3: Authentication Setup (Firebase)

*   **Step 3.1: Configure Firebase Admin SDK in Backend**
    *   **Instruction:** Add the `firebase-admin` package to `backend/requirements.txt` (if not already added in Step 1.2) and reinstall dependencies. Download the service account key JSON file from your Firebase project settings (Project settings > Service accounts > Generate new private key). Store this file securely (e.g., outside the repo locally, use secrets management in deployment). Initialize the Firebase Admin SDK in the backend application, likely during startup in `app/main.py` or a dedicated config file (`app/core/firebase_config.py`), loading the credentials from the file path specified via an environment variable.
    *   **Validation:** Run the backend application locally (ensure the environment variable points to the service account key). Verify the application starts without errors related to Firebase Admin SDK initialization.

*   **Step 3.2: Implement Backend Token Verification Middleware**
    *   **Instruction:** Create a FastAPI middleware or dependency (`app/core/auth.py`) that extracts the Bearer token (Firebase ID token) from the `Authorization` header of incoming requests. Use `firebase_admin.auth.verify_id_token()` to verify the token. If valid, extract the user's Firebase UID (`auth_provider_id`) and potentially attach it to the request state or return it for use in endpoint functions. If invalid or missing, raise an `HTTPException` (401 or 403). Apply rate limiting to this middleware (10 failed attempts per minute per IP). Log all authentication failures with detailed context.
    *   **Validation:** This step is validated primarily in conjunction with Step 3.3 and subsequent frontend integration (Phase 5). Unit tests for the middleware/dependency function should be written to simulate valid/invalid tokens and expected outcomes.

*   **Step 3.3: Create Protected Endpoint**
    *   **Instruction:** Create a new simple API endpoint (e.g., `GET /api/v1/me`) that requires authentication. Apply the token verification dependency created in Step 3.2 to this endpoint. The endpoint should return basic information about the authenticated user, such as their Firebase UID obtained from the verified token. Apply a rate limit of 30 requests per minute per authenticated user.
    *   **Validation:** Run the backend locally. Attempt to access the protected endpoint *without* a valid `Authorization: Bearer <token>` header using `curl`. Verify a 401/403 error is received. Test rate limiting by making rapid requests and confirming the 429 response after exceeding limits. (Testing with a valid token requires frontend integration, Phase 5).

---

## Phase 4: Frontend Foundation (React Native)

*   **Step 4.1: Initialize React Native Project**
    *   **Instruction:** Inside the `frontend/` directory, initialize a new React Native project using the React Native CLI: `npx react-native init MedicalAppFrontend --template react-native-template-typescript`.
    *   **Validation:** Navigate into `frontend/MedicalAppFrontend`. Run the app on an emulator/simulator (`npx react-native run-ios` or `npx react-native run-android`). Verify the default React Native welcome screen appears without errors.

*   **Step 4.2: Add Basic Dependencies**
    *   **Instruction:** Add essential libraries: navigation (`@react-navigation/native`, `@react-navigation/native-stack`), UI library (`react-native-paper` and `react-native-vector-icons`), Firebase (`@react-native-firebase/app`, `@react-native-firebase/auth`, `@react-native-firebase/app-check`), state management (`zustand`), secure storage (`react-native-keychain`), and an HTTP client (`axios`). Install pods for iOS (`cd ios && pod install`). Configure vector icons by following the library's setup instructions for each platform.
    *   **Validation:** Run `npm install` or `yarn install`. Run `cd ios && pod install`. Build and run the app again on the simulator/emulator. Verify it still builds and runs without errors after adding dependencies.

*   **Step 4.3: Configure React Native Paper Theme**
    *   **Instruction:** Set up React Native Paper by creating a `src/theme/index.ts` file. Configure a custom theme with a professional medical color palette:
        ```typescript
        import { DefaultTheme, configureFonts } from 'react-native-paper';

        const fontConfig = {
          regular: {
            fontFamily: 'sans-serif',
            fontWeight: 'normal',
          },
          medium: {
            fontFamily: 'sans-serif-medium',
            fontWeight: 'normal',
          },
          light: {
            fontFamily: 'sans-serif-light',
            fontWeight: 'normal',
          },
          thin: {
            fontFamily: 'sans-serif-thin',
            fontWeight: 'normal',
          },
        };

        export const theme = {
          ...DefaultTheme,
          colors: {
            ...DefaultTheme.colors,
            primary: '#2A6BAC',  // Calm blue - trustworthy, professional
            accent: '#45BCC9',   // Soft teal for CTAs
            background: '#F5F7FA', // Light neutral gray for backgrounds
            surface: '#FFFFFF',
            text: '#333333',     // Dark gray for better readability
            error: '#CF6679',
          },
          fonts: configureFonts(fontConfig),
        };
        ```
        Create a `src/app/AppProvider.tsx` component that wraps the application with the `Provider` from React Native Paper and apply the theme.
    *   **Validation:** Update App.tsx to use the AppProvider. Run the app and verify the custom theme is applied, checking that native elements match the configured color theme.

*   **Step 4.4: Set up Basic Navigation Structure**
    *   **Instruction:** Implement basic stack navigation using React Navigation. Define two main screens: `LoginScreen` and `HomeScreen`. Set up the navigator to initially show `LoginScreen`, and navigate to `HomeScreen` upon successful login (logic to be added later). Implement a `SplashScreen` for initial loading and authentication checks. Create placeholder components for these screens using React Native Paper components:
        * Use `Appbar` for headers
        * Use `Surface` components for screen backgrounds
        * Use `Card` components for content grouping
    *   **Validation:** Run the app. Verify the placeholder `LoginScreen` is displayed initially with React Native Paper styling. Manually trigger a navigation to `HomeScreen` (e.g., via a temporary button) and verify the placeholder `HomeScreen` is displayed with consistent styling.

*   **Step 4.5: Implement Firebase SDK Setup in Frontend**
    *   **Instruction:** Follow the `@react-native-firebase/app` setup instructions for both iOS (add `GoogleService-Info.plist`) and Android (add `google-services.json`, configure build files). Configure `@react-native-firebase/app-check` to prevent API abuse. Use reCAPTCHA for App Check in debug mode. Ensure the Firebase app initializes correctly when the React Native app starts.
    *   **Validation:** Build and run the app on both iOS and Android simulators/devices. Check the device logs or console output for any errors related to Firebase initialization. Verify App Check is properly initialized. Verify the app runs without crashing.

*   **Step 4.6: Create Login/Registration Screen UI**
    *   **Instruction:** Build the UI for the `LoginScreen` using React Native Paper components:
        * Use `Surface` as a container
        * Use `Title` and `Paragraph` for headings and text
        * Use `TextInput` components with appropriate keyboard types and autocomplete attributes for email/password
        * Use `Button` components for actions, with the primary color for main actions
        * Use `HelperText` for validation messages
        * Include a "Forgot Password" text button
        * Add a subtle medical-themed illustration or logo at the top (optional)
        * Implement form validation with proper error messaging:
          * Email format validation
          * Password strength requirements (min 8 chars, requires mix of letters, numbers)
        * Create a separate screen or modal for registration with similar styling
    *   **Validation:** Run the app. Verify the `LoginScreen` displays email/password inputs and buttons with React Native Paper styling. Test input validation by entering invalid data and checking for appropriate validation messages using HelperText components.

*   **Step 4.7: Implement Secure Storage Utilities**
    *   **Instruction:** Create a utility module (e.g., `src/utils/secureStorage.ts`) using `react-native-keychain` to securely store sensitive data like authentication tokens. Implement functions to save, retrieve, and clear tokens.
    *   **Validation:** Create a simple test component that uses these utilities to store and retrieve a test value. Verify the data is properly stored and retrieved using the secure storage mechanism.

*   **Step 4.8: Create Home Screen Layout**
    *   **Instruction:** Design a basic `HomeScreen` layout using React Native Paper components:
        * Use `Appbar` for the top navigation
        * Use `BottomNavigation` for main app sections (to be expanded later)
        * Use `Card` components to display user information
        * Use `ActivityIndicator` for loading states
        * Implement a responsive layout that works on different screen sizes
        * Include a clear privacy indicator (e.g., a small lock icon)
        * Use consistent spacing based on 8-point grid system
    *   **Validation:** Navigate to the HomeScreen and verify the layout displays correctly. Test on different device sizes if possible to ensure responsive behavior.

---

## Phase 5: Connecting Frontend & Backend

*   **Step 5.1: Implement Frontend API Service Layer**
    *   **Instruction:** Create a dedicated module/service in the frontend (e.g., `src/services/api.js` or `src/api/client.ts`) to handle API calls to the backend. Configure the base URL of the backend (use `localhost` or local IP for development). Use `axios` or `fetch` for making requests. Include logic to add the Firebase Auth token to the `Authorization` header for authenticated requests. Implement interceptors for handling token expiration, automatic retries with exponential backoff (max 3 retries), and global error handling.
    *   **Validation:** Write a simple function in this service layer to call the backend's public health check endpoint (`/api/v1/health`). Call this function from a temporary button or `useEffect` hook in a component. Run the frontend and backend locally. Verify the frontend successfully receives the `{"status": "ok"}` response from the backend (check console logs).

*   **Step 5.2: Implement Frontend Login/Registration Logic**
    *   **Instruction:** Implement the "Register" button logic: use `@react-native-firebase/auth`'s `createUserWithEmailAndPassword` method. Implement the "Login" button logic: use `signInWithEmailAndPassword`. Upon successful login/registration, retrieve the ID token using `currentUser.getIdToken()`. Store the token securely using the secure storage utility from Step 4.7. Implement proper error handling and user feedback for authentication failures. Implement logic for password reset via email. Add rate limiting for login attempts (e.g., after 5 failed attempts, force a 30-second wait). Navigate to the `HomeScreen` upon successful login.
    *   **Validation:** Run the app. Use the Register button with a test email/password. Check the Firebase Authentication console to verify the user was created. Log out (clear the stored token) and use the Login button with the same credentials. Verify login succeeds and the app navigates to the `HomeScreen`. Check secure storage to confirm the ID token was stored correctly. Test failed login handling by intentionally using incorrect credentials.

*   **Step 5.3: Call Backend Health Check from Authenticated Frontend**
    *   **Instruction:** From the `HomeScreen` (which should only be accessible after login), use the API service layer (Step 5.1) to call the backend's *public* health check endpoint (`/api/v1/health`).
    *   **Validation:** Log in to the app. Once on the `HomeScreen`, verify the call to the health check endpoint succeeds and the `{"status": "ok"}` response is received (check console logs).

*   **Step 5.4: Call Protected Backend Endpoint from Authenticated Frontend**
    *   **Instruction:** From the `HomeScreen`, use the API service layer to call the backend's *protected* endpoint (`/api/v1/me`). Ensure the service layer correctly attaches the stored Firebase ID token to the `Authorization: Bearer <token>` header. Display the response (e.g., the user's UID) on the `HomeScreen` or log it.
    *   **Validation:** Log in to the app. Once on the `HomeScreen`, verify the call to the protected endpoint succeeds. Check the backend logs to confirm the request was received and processed by the authenticated endpoint. Verify the expected response (e.g., user UID) is logged or displayed in the frontend app. Attempting this call without logging in first should fail.

*   **Step 5.5: Implement Token Refresh Mechanism**
    *   **Instruction:** Create a mechanism to refresh the Firebase ID token before it expires (tokens typically expire after 1 hour). This could be a periodic refresh (e.g., every 50 minutes) or triggered by 401 responses. Implement this in the API service layer. 
    *   **Validation:** Simulate token expiration by manually modifying the stored token to be invalid. Attempt an API call that requires authentication and verify the token refresh mechanism activates correctly, obtaining a new valid token and retrying the failed request successfully.

---

## Phase 6: Deployment Setup (Basic Backend)

*   **Step 6.1: Configure Cloud Run Service for Backend**
    *   **Instruction:** Using the GCP console or `gcloud`, create a Cloud Run service. Configure it to build and deploy from the source code in the `backend/` directory (or from a pre-built container image pushed to Google Artifact Registry). Set necessary environment variables (Database URL, Firebase service account credentials - use Secret Manager). Ensure the service allows unauthenticated invocations for the public health check endpoint *initially* (will be locked down later). Configure CPU/memory resources (start small). Set up Cloud Armor in front of Cloud Run to add an additional layer of protection (WAF rules, rate limiting at the infrastructure level).
    *   **Validation:** Trigger a deployment. Wait for the deployment to complete successfully. Access the public URL provided by Cloud Run for the health check endpoint (`<service-url>/api/v1/health`). Verify the `{"status": "ok"}` response is received. Test that Cloud Armor protection is working by simulating a simple attack pattern and verifying it's blocked.

*   **Step 6.2: Set up Basic CI/CD for Backend Deployment**
    *   **Instruction:** Create a basic `cloudbuild.yaml` file in the `backend/` directory. Define steps to run tests, check for security vulnerabilities in dependencies, build the Docker image and deploy it to the Cloud Run service created in Step 6.1. Set up a Cloud Build trigger that automatically starts this build process on pushes to the main branch of the Git repository.
    *   **Validation:** Make a small, non-breaking change to the backend code (e.g., update the health check response slightly). Push the change to the main branch. Verify the Cloud Build trigger runs automatically, runs tests, checks for vulnerabilities, builds the image, and deploys the new revision to Cloud Run. Access the health check endpoint again and confirm the change is live.

*   **Step 6.3: Configure Monitoring and Alerting**
    *   **Instruction:** Set up basic monitoring and alerting using Google Cloud Monitoring. Configure alerts for high error rates, unusual authentication attempt patterns, and resource utilization. Set up a dashboard for visualizing API traffic, error rates, and authentication events.
    *   **Validation:** Simulate error conditions and verify that alerts are triggered appropriately. Check that the monitoring dashboard correctly displays application metrics.

---

## Phase 7: Security Review and Hardening

*   **Step 7.1: Conduct Security Configuration Review**
    *   **Instruction:** Review all security configurations implemented so far: authentication, rate limiting, secure storage, database access controls, API protection, and Cloud infrastructure security. Create a document listing all implemented security measures and any potential gaps.
    *   **Validation:** Complete a checklist of security best practices, verifying each item is addressed in the implementation.

*   **Step 7.2: Implement Security Testing**
    *   **Instruction:** Create basic security tests for the API endpoints, testing for common vulnerabilities: authentication bypass attempts, rate limit evasion, injection attacks, and insecure direct object references. Use tools like OWASP ZAP or manual testing.
    *   **Validation:** Run the security tests and verify all tested attack vectors are properly mitigated.

*   **Step 7.3: Secure Infrastructure Review**
    *   **Instruction:** Review GCP infrastructure security settings, ensuring appropriate VPC configurations, IAM permissions following the principle of least privilege, and secure connections between services.
    *   **Validation:** Create a checklist of infrastructure security best practices and verify all items are addressed.

---

## Phase 8: Testing Strategy for MVP

*   **Step 8.1: Backend Testing Setup**
    *   **Instruction:** Set up a testing environment for the FastAPI backend. Create a `tests/` directory with subdirectories `tests/unit/`, `tests/integration/`, and `tests/security/`. Add the following testing dependencies to `requirements.txt`:
        ```
        pytest==7.4.x
        httpx==0.25.x  # For async HTTP testing
        pytest-asyncio==0.21.x  # For testing async endpoints
        pytest-cov==4.1.x  # For coverage reporting
        ```
        Configure pytest in a `pytest.ini` file with appropriate settings. Set up test database fixtures and mock Firebase authentication.
    *   **Validation:** Run `pytest --version` to verify installation. Ensure a basic test passes with `pytest -xvs tests/`.

*   **Step 8.2: Backend Critical Path Tests**
    *   **Instruction:** Implement unit and integration tests for the most critical backend components:
        * **Authentication Unit Tests:** Test the token verification middleware, focusing on valid tokens, expired tokens, and invalid tokens.
        * **API Integration Tests:** Test the protected endpoints to ensure they reject unauthenticated requests and accept authenticated ones.
        * **Security Tests:** Test rate limiting functionality and validate security headers.
        * **Database Tests:** Test the user creation and retrieval functionality.
        
        Aim for 70%+ test coverage on authentication and data handling code.
    *   **Validation:** Run `pytest -xvs tests/ --cov=app` and verify coverage meets the target for critical components. Ensure all tests pass.

*   **Step 8.3: Frontend Testing Setup**
    *   **Instruction:** Set up testing for the React Native frontend. Jest should already be included with the React Native template. Add the following testing dependencies:
        ```
        @testing-library/react-native
        react-native-testing-library
        ```
        Configure Jest in `package.json` with appropriate settings, including module mappings and transformers for React Native.
    *   **Validation:** Run `npm test -- --version` to verify Jest is installed. Ensure a basic component test passes.

*   **Step 8.4: Frontend Critical Path Tests**
    *   **Instruction:** Implement tests for the most critical frontend components:
        * **Authentication Components:** Test login and registration forms, focusing on input validation, submission handling, and error states.
        * **Auth State Hook Tests:** Test the authentication state management and token handling.
        * **Secure Storage Tests:** Verify secure token storage implementation.
        * **Navigation Tests:** Test that authenticated routes are protected.
        
        Use snapshot testing for UI components to detect unintended UI changes.
    *   **Validation:** Run `npm test` and verify all tests pass. Ensure critical components have adequate test coverage.

*   **Step 8.5: CI Integration for Tests**
    *   **Instruction:** Extend the CI/CD configuration in `cloudbuild.yaml` to include running tests as part of the build and deployment process. Configure the pipeline to:
        * Run backend tests with a minimum coverage threshold of 60% for critical code
        * Run frontend tests
        * Fail the build if any security-critical tests fail
        * Generate and store test reports as build artifacts
    *   **Validation:** Push a change to trigger the CI/CD pipeline and verify tests run successfully as part of the build process. Check the build logs for test results and coverage reports.

*   **Step 8.6: End-to-End Test for Critical Flow**
    *   **Instruction:** Implement a basic end-to-end test that verifies the critical user journey:
        * User registration
        * User login
        * Authentication token management
        * Accessing a protected endpoint
        
        This can be implemented using a tool like Detox for React Native or a custom script using the backend test client and mocked frontend.
    *   **Validation:** Run the E2E test and verify the entire authentication flow works correctly from registration through to accessing protected resources.

---

This concludes the base application setup, including essential testing for an MVP. The next phases will involve implementing document upload, OCR/NLP integration, data storage, user review workflows, and querying features. 