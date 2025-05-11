# Medical Data Hub - Frontend

This is the React Native frontend for the Medical Data Hub application. It's built with Expo, React Native Paper, and Supabase authentication.

## Prerequisites

- Node.js 18.x or higher
- Expo CLI (`npm install -g expo-cli`)
- Xcode for iOS development
- Android Studio for Android development

## Getting Started

1. Clone the repository
2. Navigate to the frontend directory
3. Install dependencies:
   ```bash
   npm install
   ```
4. Create a `.env` file in the frontend directory with the following variables:
   ```
   SUPABASE_URL=your-supabase-url
   SUPABASE_ANON_KEY=your-supabase-anon-key
   API_URL=http://localhost:8000  # Update with your backend URL
   ```
5. Start the development server:
   ```bash
   npm start
   ```
6. Follow the instructions to run on iOS simulator, Android emulator, or physical device

## Features

- **Authentication**: Login and registration with Supabase
- **Document Management**: View, upload, and delete medical documents
- **Document Details**: View extracted data from medical documents
- **Natural Language Queries**: Query your medical data using natural language

## Project Structure

- `/src/api`: API client and utilities
- `/src/components`: Reusable React components
- `/src/config`: Configuration constants
- `/src/hooks`: Custom React hooks
- `/src/navigation`: Navigation setup
- `/src/screens`: Application screens
- `/src/services`: Service integrations (Supabase, etc.)
- `/src/theme`: Theme configuration
- `/src/utils`: Utility functions

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 