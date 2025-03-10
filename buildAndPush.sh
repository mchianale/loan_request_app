#!/bin/bash
echo "--------------------------------------------------"
echo "🔨 Building and pushing Docker images for all services"
echo "--------------------------------------------------"

# Define services and Dockerfiles
declare -A services=(
    ["user-backend-service"]="./userBackEnd/Dockerfile.userBackEnd"
    ["credit-check-app-service"]="./creditCheckApp/Dockerfile.creditCheckApp"
    ["property-check-app-service"]="./propertyCheckApp/Dockerfile.propertyCheckApp"
    ["decision-app-service"]="./decisionApp/Dockerfile.decisionApp"
    ["loan-notification-service"]="./loanNotificationApp/Dockerfile.loanNotificationApp"
    ["celery-app"]="./celeryApp/Dockerfile.celeryApp"
    ["logstash"]="./logstash/Dockerfile.logstash"
)

DOCKER_HUB_USERNAME="mchianale"

# Loop through services
for service in "${!services[@]}"; do
    DOCKERFILE="${services[$service]}"
    IMAGE_NAME="$DOCKER_HUB_USERNAME/$service:latest"

    echo "🔨 Building the Docker image for $service..."
    docker build -f $DOCKERFILE -t $IMAGE_NAME .

    echo "📤 Pushing the Docker image to Docker Hub..."
    docker push $IMAGE_NAME

    echo "✅ Done: $service"
    echo "--------------------------------------------------"
done

echo "🎉 All images have been built and pushed successfully!"
