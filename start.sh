#!/bin/bash

echo "🚀 Starting Split App with Docker..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

#!/bin/bash

# Install Docker and Docker Compose on Debian

# Make sure the script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run this script as root or with sudo"
    exit 1
fi

# Update package list
echo "Updating package list..."
apt-get update -qq

# Install required dependencies
echo "Installing dependencies..."
apt-get install -y -qq \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
echo "Adding Docker's GPG key..."
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo "Setting up Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
echo "Installing Docker..."
apt-get update -qq
apt-get install -y -qq \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-compose-plugin

# Start and enable Docker service
echo "Starting Docker service..."
systemctl enable --now docker

# Verify installation
echo "Verifying Docker installation..."
docker --version
docker compose version

# Add current user to docker group
echo "Adding current user to docker group..."
usermod -aG docker $SUDO_USER

echo -e "\n\e[32mDocker installation complete!\e[0m"
echo "You may need to log out and back in for group changes to take effect."
echo "To verify, run: docker run hello-world"

# Step 2: Ensure Docker is running
if ! sudo systemctl is-active --quiet docker; then
    echo -e "${YELLOW}⚙️ Starting Docker...${NC}"
    sudo systemctl start docker
    sudo systemctl enable docker
    echo -e "${GREEN}✅ Docker started and enabled!${NC}"
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  docker-compose not found, trying 'docker compose'...${NC}"
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Clean up any existing containers
echo -e "${YELLOW}🧹 Cleaning up existing containers...${NC}"
$DOCKER_COMPOSE down

# Build and start the application
echo -e "${BLUE}📦 Building Docker containers...${NC}"
$DOCKER_COMPOSE build --no-cache

echo -e "${BLUE}🌟 Starting services...${NC}"
$DOCKER_COMPOSE up -d

echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"

# Wait for database to be ready
echo "Waiting for database..."
for i in {1..30}; do
    if $DOCKER_COMPOSE exec -T db pg_isready -U user -d splitapp > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Database is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for backend to be ready
echo "Waiting for backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Check if services are running
if $DOCKER_COMPOSE ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Split App is running successfully!${NC}"
    echo ""
    echo -e "${BLUE}🌐 Frontend: ${NC}http://localhost:8000"
    echo -e "${BLUE}📚 API Docs: ${NC}http://localhost:8000/api/docs"
    echo -e "${BLUE}🗄️  Database: ${NC}localhost:5432 (user: user, password: password)"
    echo ""
    echo -e "${YELLOW}📋 Useful Commands:${NC}"
    echo -e "  View logs:        ${DOCKER_COMPOSE} logs -f"
    echo -e "  Stop app:         ${DOCKER_COMPOSE} down"
    echo -e "  Restart app:      ${DOCKER_COMPOSE} restart"
    echo -e "  View status:      ${DOCKER_COMPOSE} ps"
    echo ""
    echo -e "${GREEN}🎉 Happy expense splitting!${NC}"
else
    echo -e "${RED}❌ Failed to start services. Check logs with: ${DOCKER_COMPOSE} logs${NC}"
    exit 1
fi