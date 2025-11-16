# Use minimal Alpine Linux base image
FROM alpine:latest

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

# Install required Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Copy the script to the container
COPY gitlab_api.py /usr/local/bin/gitlab_api.py

# Make the script executable
RUN chmod +x /usr/local/bin/gitlab_api.py

# Set environment variables (can be overridden at runtime)
ENV GITLAB_URL=http://localhost
ENV GITLAB_TOKEN=""

# Create a simple service script that accepts keywords
COPY service.sh /usr/local/bin/service.sh
RUN chmod +x /usr/local/bin/service.sh

# Expose a port if needed (though we're using stdin/stdout)
# EXPOSE 8080

# Use the service script as entrypoint
ENTRYPOINT ["/usr/local/bin/service.sh"]

