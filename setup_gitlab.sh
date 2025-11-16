#!/bin/bash
# script for GitLab playground  15.11.13-ee.0

set -e

GITLAB_HOME="${GITLAB_HOME:-/tmp/gitlab}"
GITLAB_HOST="${GITLAB_HOST:-gitlab.example.com}"
GITLAB_URL="${GITLAB_URL:-http://localhost}"

echo "=== GitLab playground setup ==="
echo "GitLab home: $GITLAB_HOME"
echo "GitLab host: $GITLAB_HOST"
echo "GitLab URL: $GITLAB_URL"
echo ""

# Create directories if they don't exist
mkdir -p "$GITLAB_HOME"/{config,logs,data}

# Check if GitLab container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^gitlab$"; then
    echo "GitLab container already exists."
    read -p "Do you want to remove it and start fresh? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping and removing existing GitLab container..."
        docker stop gitlab 2>/dev/null || true
        docker rm gitlab 2>/dev/null || true
    else
        echo "Starting existing GitLab container..."
        docker start gitlab
        echo "GitLab should be available at $GITLAB_URL"
        echo ""
        echo "getting root password..."
        # Retry logic to get password
        MAX_RETRIES=60
        RETRY_DELAY=5
        RETRY_COUNT=0
        
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            PASSWORD_OUTPUT=$(docker exec gitlab bash -c 'cat /etc/gitlab/initial_root_password' 2>/dev/null | grep -i password)
            
            if [ $? -eq 0 ] && [ -n "$PASSWORD_OUTPUT" ]; then
                echo "=== GitLab Root Password ==="
                echo "$PASSWORD_OUTPUT"
                exit 0
            fi
            
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                echo "Password file not ready yet (attempt $RETRY_COUNT/$MAX_RETRIES). Retrying in ${RETRY_DELAY}s..."
                sleep $RETRY_DELAY
            fi
        done
        
        echo "Could not retrieve password. GitLab may still be initializing."
        exit 1
    fi
fi

echo "Start GitLab container..."
docker run --detach \
  --hostname "$GITLAB_HOST" \
  --env GITLAB_OMNIBUS_CONFIG="external_url '$GITLAB_URL'" \
  --publish 443:443 \
  --publish 80:80 \
  --publish 22:22 \
  --name gitlab \
  --restart always \
  --volume "$GITLAB_HOME/config:/etc/gitlab" \
  --volume "$GITLAB_HOME/logs:/var/log/gitlab" \
  --volume "$GITLAB_HOME/data:/var/opt/gitlab" \
  --shm-size 256m \
  gitlab/gitlab-ee:15.11.13-ee.0

echo ""
echo "GitLab container started. Waiting for initialization..."
echo "This may take 10-15 minutes depending on your machine resources."
echo ""
echo "Monitoring logs for 'gitlab Reconfigured!' message..."
echo "Press Ctrl+C to stop monitoring (GitLab will continue starting in background)"
echo ""

# Monitor logs for completion
if docker logs -f gitlab 2>&1 | grep --line-buffered -i "gitlab Reconfigured!" | head -1; then
  echo ""
  echo "=== GitLab is ready! ==="
  echo "Access GitLab at: $GITLAB_URL"
  echo ""
  echo "Getting root password..."
  
  # Retry logic to get password
  MAX_RETRIES=60
  RETRY_DELAY=5
  RETRY_COUNT=0
  
  while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    PASSWORD_OUTPUT=$(docker exec gitlab bash -c 'cat /etc/gitlab/initial_root_password' 2>/dev/null | grep -i password)
    
    if [ $? -eq 0 ] && [ -n "$PASSWORD_OUTPUT" ]; then
      echo "=== GitLab root password ==="
      echo "$PASSWORD_OUTPUT"
      echo ""
      echo "You can now create a API token at: $GITLAB_URL/-/profile/personal_access_tokens"
      exit 0
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
      echo "Password file not ready yet (attempt $RETRY_COUNT/$MAX_RETRIES). Retrying in ${RETRY_DELAY}s..."
      sleep $RETRY_DELAY
    fi
  done
  
  echo ""
  echo "Warning: couldnt get password after $MAX_RETRIES attempts."
  echo "GitLab is still be initializing. try:"
  echo "  docker exec -it gitlab bash -c 'cat /etc/gitlab/initial_root_password' | grep -i password"
else
  echo "GitLab is starting in the background. Run 'docker logs gitlab -f' until you get gitlab Reconfigured."
fi

