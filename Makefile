.PHONY: stop clean dev-backend dev-frontend install restart

# Stop services on ports 8001 (backend) and 5173 (frontend)
stop:
	@echo "Stopping services..."
	-fuser -k 8001/tcp || true
	-fuser -k 5173/tcp || true
	@echo "Services stopped."

# Default target
all: install

# Install dependencies for both backend and frontend
install:
	@echo "Installing Backend dependencies..."
	cd backend && uv sync
	@echo "Installing Frontend dependencies..."
	cd frontend && npm install

# Run backend (blocking)
dev-backend:
dev-backend:
	cd backend && uv run python main.py

# Run frontend (blocking)
dev-frontend:
	cd frontend && npm run dev

# Restart helper: Stops services. 
# Usage: 
#   1. make stop
#   2. make dev-backend (in terminal 1)
#   3. make dev-frontend (in terminal 2)
restart: stop
	@echo "Services stopped. Please run 'make dev-backend' and 'make dev-frontend' in separate terminals."
