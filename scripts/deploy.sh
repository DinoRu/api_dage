#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="meter-reading"
DEPLOYMENT="api-deployment"
IMAGE_NAME="yourdockerhub/meter-reading-api"
VERSION="${1:-latest}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Meter Reading API Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${GREEN}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl not found. Please install kubectl."
    exit 1
fi

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    print_error "Not connected to a Kubernetes cluster."
    exit 1
fi

print_info "Connected to cluster: $(kubectl config current-context)"
echo ""

# Select deployment type
echo "Select deployment type:"
echo "1) Docker Compose (Development)"
echo "2) Docker Compose (Production)"
echo "3) Kubernetes"
echo "4) Kubernetes with Helm"
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        print_info "Deploying with Docker Compose (Development)..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
        print_success "Development environment started!"
        echo ""
        print_info "API available at: http://localhost:8000"
        print_info "Docs available at: http://localhost:8000/docs"
        ;;
    
    2)
        print_info "Deploying with Docker Compose (Production)..."
        
        # Build and tag image
        print_info "Building Docker image..."
        docker build -t ${IMAGE_NAME}:${VERSION} -f docker/Dockerfile .
        
        # Push to registry
        read -p "Push to Docker registry? (y/n): " push
        if [ "$push" = "y" ]; then
            print_info "Pushing image to registry..."
            docker push ${IMAGE_NAME}:${VERSION}
            print_success "Image pushed successfully!"
        fi
        
        # Deploy
        export VERSION=${VERSION}
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        print_success "Production environment started!"
        ;;
    
    3)
        print_info "Deploying to Kubernetes..."
        
        # Create namespace
        print_info "Creating namespace..."
        kubectl apply -f kubernetes/base/namespace.yaml
        
        # Apply secrets
        print_warning "Applying secrets (ensure they are properly configured)..."
        kubectl apply -f kubernetes/base/secrets.yaml
        
        # Apply configmap
        print_info "Applying configmap..."
        kubectl apply -f kubernetes/base/configmap.yaml
        
        # Deploy PostgreSQL
        print_info "Deploying PostgreSQL..."
        kubectl apply -f kubernetes/postgres/
        sleep 10
        
        # Deploy Redis
        print_info "Deploying Redis..."
        kubectl apply -f kubernetes/redis/
        sleep 5
        
        # Deploy API
        print_info "Deploying API..."
        kubectl apply -f kubernetes/base/deployment.yaml
        kubectl apply -f kubernetes/base/service.yaml
        kubectl apply -f kubernetes/base/hpa.yaml
        
        # Deploy Ingress
        print_info "Deploying Ingress..."
        kubectl apply -f kubernetes/base/ingress.yaml
        
        # Wait for rollout
        print_info "Waiting for deployment to complete..."
        kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE} --timeout=300s
        
        print_success "Kubernetes deployment completed!"
        echo ""
        print_info "Checking pods status..."
        kubectl get pods -n ${NAMESPACE}
        ;;
    
    4)
        print_info "Deploying with Helm..."
        
        # Check if Helm is installed
        if ! command -v helm &> /dev/null; then
            print_error "Helm not found. Please install Helm."
            exit 1
        fi
        
        # Deploy with Helm
        helm upgrade --install meter-reading ./helm/meter-reading \
            --namespace ${NAMESPACE} \
            --create-namespace \
            --set image.tag=${VERSION} \
            --wait \
            --timeout 10m
        
        print_success "Helm deployment completed!"
        ;;
    
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_success "Deployment completed successfully!"
echo ""

# Show useful commands
print_info "Useful commands:"
echo "  View logs:    kubectl logs -f deployment/${DEPLOYMENT} -n ${NAMESPACE}"
echo "  Get pods:     kubectl get pods -n ${NAMESPACE}"
echo "  Get services: kubectl get svc -n ${NAMESPACE}"
echo "  Scale:        kubectl scale deployment/${DEPLOYMENT} --replicas=5 -n ${NAMESPACE}"
echo "  Describe:     kubectl describe deployment/${DEPLOYMENT} -n ${NAMESPACE}"