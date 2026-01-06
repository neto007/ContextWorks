#!/bin/bash
set -e

echo "🚀 Iniciando Build e Deploy..."

# Build Backend
echo "📦 Building Backend..."
docker build -t security-platform-backend:latest ./backend

# Build Frontend
echo "📦 Building Frontend..."
docker build -t security-platform-frontend:latest ./frontend

# Build Tool Images (optional - only if tools were modified)
if [ "$BUILD_TOOLS" = "all" ]; then
    echo "📦 Building ALL Tool Images..."
    python3 docker/build-tool-images.py --all
elif [ -n "$BUILD_TOOLS" ]; then
    echo "📦 Building Tool Images: $BUILD_TOOLS..."
    python3 docker/build-tool-images.py --tools $BUILD_TOOLS
else
    echo "⏭️  Skipping tool image builds (set BUILD_TOOLS=all or BUILD_TOOLS='tool1 tool2' to build)"
fi

# Check if using Minikube and load images (optional)
if command -v minikube &> /dev/null; then
    echo "🔄 Loading images into Minikube..."
    minikube image load security-platform-backend:latest
    minikube image load security-platform-frontend:latest
    
    # Load tool images if they were built
    if [ -n "$BUILD_TOOLS" ]; then
        for img in $(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^security-platform-tool-"); do
            echo "  Loading $img..."
            minikube image load "$img"
        done
    fi
fi

# Check if using Kind and load images (optional)
if command -v kind &> /dev/null; then
    echo "🔄 Loading images into Kind..."
    kind load docker-image security-platform-backend:latest
    kind load docker-image security-platform-frontend:latest
    
    # Load tool images if they were built
    if [ -n "$BUILD_TOOLS" ]; then
        for img in $(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^security-platform-tool-"); do
            echo "  Loading $img..."
            kind load docker-image "$img"
        done
    fi
fi

# Apply K8s Manifests
echo "📋 Applying Manifests..."
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-postgres.yaml
kubectl apply -f k8s/02-permissions.yaml
kubectl apply -f k8s/03-backend.yaml
kubectl apply -f k8s/04-frontend.yaml
kubectl apply -f k8s/99-cloudflared.yaml

echo "✅ Deploy concluído!"
echo "Verifique os pods com: kubectl get pods -n contextworks-platform"
echo ""
echo "💡 Para buildar imagens de ferramentas:"
echo "   BUILD_TOOLS=all ./deploy.sh        # Build todas"
echo "   BUILD_TOOLS='nmap_scan' ./deploy.sh  # Build específica"
