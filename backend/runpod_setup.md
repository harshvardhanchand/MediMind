# RunPod Deployment Guide for MediMind

## 1. RunPod Serverless Setup

### Create New Endpoint
1. Login to RunPod dashboard
2. Go to "Serverless" → "Endpoints"
3. Click "New Endpoint"

### Configuration:
```
Name: medimind-api
Template: Custom
Container Image: your-dockerhub-username/medimind-backend:latest
Container Disk: 10 GB
GPU Type: L4 (24GB) - $0.48/hour
Min Workers: 0
Max Workers: 3
Idle Timeout: 5 seconds
```

### Environment Variables:
```
# Database
DATABASE_URL=your_supabase_database_url
ASYNC_DATABASE_URL=your_supabase_async_database_url

# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret

# Google Cloud
GOOGLE_CLOUD_PROJECT_ID=your_project_id
GOOGLE_CLOUD_STORAGE_BUCKET=your_bucket_name
GOOGLE_CLOUD_DOCUMENT_AI_PROCESSOR_ID=your_processor_id
GEMINI_API_KEY=your_gemini_key

# App Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## 2. Docker Image Preparation

Your existing Dockerfile should work perfectly with RunPod!

## 3. Deployment Steps

1. Build and push Docker image to Docker Hub
2. Create RunPod endpoint with the image
3. Test the endpoint
4. Update frontend to use RunPod URL

## 4. Testing

Use the RunPod endpoint URL in your frontend:
```
API_URL=https://api-xxxxx.runpod.run
``` 