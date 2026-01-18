@echo off
REM Deployment script for Legal Content System (Windows)
REM Usage: deploy.bat [environment]
REM Environments: dev, staging, production

setlocal enabledelayedexpansion

REM Default environment
set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=production

echo ========================================
echo Legal Content System Deployment
echo Environment: %ENVIRONMENT%
echo ========================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please copy .env.production.example to .env and configure it.
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    exit /b 1
)

REM Main deployment flow
if "%ENVIRONMENT%"=="dev" (
    echo Starting development environment...
    docker-compose up -d postgres backend frontend
    goto :done
)

if "%ENVIRONMENT%"=="staging" (
    echo Starting staging environment...
    docker-compose up -d
    goto :done
)

if "%ENVIRONMENT%"=="production" (
    echo Deploying to production...
    echo.

    REM Pull latest images
    echo Pulling latest images...
    docker-compose pull

    REM Build services
    echo Building services...
    docker-compose build --no-cache

    REM Stop old containers
    echo Stopping old containers...
    docker-compose down

    REM Start services with nginx
    echo Starting services...
    docker-compose --profile production up -d

    REM Wait for services to be ready
    echo Waiting for services to start...
    timeout /t 10 /nobreak >nul

    REM Run migrations
    echo Running database migrations...
    docker-compose exec backend alembic upgrade head

    REM Health check
    echo Performing health check...
    curl -f http://localhost:8000/health >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Backend health check failed
        exit /b 1
    )
    echo Backend is healthy

    curl -f http://localhost:3000 >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Frontend health check failed
    ) else (
        echo Frontend is healthy
    )

    echo.
    echo ========================================
    echo Deployment completed successfully!
    echo ========================================
    echo Services:
    echo   Backend API: http://localhost:8000
    echo   Frontend: http://localhost:3000
    echo   Nginx Proxy: http://localhost:80
    echo.
    echo Useful commands:
    echo   View logs: docker-compose logs -f [service]
    echo   Stop services: docker-compose down
    echo   Restart service: docker-compose restart [service]
    goto :done
)

echo [ERROR] Unknown environment '%ENVIRONMENT%'
echo Usage: %0 [dev^|staging^|production]
exit /b 1

:done
echo.
echo Done!
endlocal
