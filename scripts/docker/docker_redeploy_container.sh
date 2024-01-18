#!/bin/bash

# Check if a Docker Compose file path was provided
if [ $# -eq 0 ]; then
    echo "No Docker Compose file path provided."
    echo "Usage: $0 <path_to_compose_file>"
    exit 1
fi

# Function to get Docker Compose file path
get_compose_file_path() {
    echo -n "Enter the path to your Docker Compose file: "
    read COMPOSE_FILE_PATH
}

# If a Docker Compose file path was not provided, prompt for one
if [ $# -eq 0 ]; then
    get_compose_file_path
else
    COMPOSE_FILE_PATH=$1
fi

# Check if the compose file exists, if not, exit
while [ ! -f "$COMPOSE_FILE_PATH" ]; do
    echo "ERROR: Compose file $COMPOSE_FILE_PATH not found."
    exit 1
done

# Get the Container Name and Image ID from the Docker Compose configuration
read -r CONTAINER_NAME IMAGE_ID <<<$(docker compose -f $COMPOSE_FILE_PATH ps --all --format "table {{.Name}}\t{{.Image}}" | awk 'NR>1 {p>

# Check if Container Name and Image ID were found
if [ -z "$CONTAINER_NAME" ] || [ -z "$IMAGE_ID" ]; then
    echo "ERROR: Failed to retrieve container name or image ID from Docker Compose file."
    exit 1
fi

# Stop and remove the container using Docker Compose
echo "COMMAND: docker compose -f $COMPOSE_FILE_PATH down"
docker compose -f $COMPOSE_FILE_PATH down

# Redeploy the container using Docker Compose
echo "COMMAND: docker compose -f $COMPOSE_FILE_PATH up -d"
docker compose -f $COMPOSE_FILE_PATH up -d

# Try to remove the old image
echo 'COMMAND: docker rmi $IMAGE_ID'
REMOVE_OUTPUT=$(docker rmi $IMAGE_ID 2>&1)

# Check if the removal was successful or if the image is in use
if [[ $REMOVE_OUTPUT == *"unable to remove repository reference"* ]]; then
    # Extract the container ID from the error message
    CONFLICT_CONTAINER_ID=$(echo $REMOVE_OUTPUT | grep -oE 'container [0-9a-f]+' | cut -d ' ' -f 2)

    # Get the container name for the conflict container ID
    CONFLICT_CONTAINER_NAME=$(docker ps -a --format "{{.Names}}" --filter "id=$CONFLICT_CONTAINER_ID")

    echo "RESULT: Image $IMAGE_ID was not removed since it is in use by container $CONFLICT_CONTAINER_NAME"
else
    echo "RESULT: Image $IMAGE_ID removed successfully."
fi

# Optionally, prune any dangling images
echo 'COMMAND: docker image prune -f'
docker image prune -f

echo "DONE."
