#!/bin/bash

# RunPod Deployment Script for MediMind

echo "🚀 Deploying MediMind to RunPod..."

# Set your Docker Hub username
DOCKER_USERNAME="harshvardhan876"
IMAGE_NAME="medimind-backend"
TAG="latest"

echo "📦 Building Docker image..."
docker build -t $DOCKER_USERNAME/$IMAGE_NAME:$TAG .

echo "📤 Pushing to Docker Hub..."
docker push $DOCKER_USERNAME/$IMAGE_NAME:$TAG

echo "✅ Docker image pushed successfully!"
echo "🔗 Image URL: $DOCKER_USERNAME/$IMAGE_NAME:$TAG"
echo ""
echo "Next steps:"
echo "1. Go to RunPod dashboard"
echo "2. Create new serverless endpoint"
echo "3. Use image: $DOCKER_USERNAME/$IMAGE_NAME:$TAG"
echo "4. Configure environment variables (see runpod_setup.md)"
echo "5. Deploy and test!" 