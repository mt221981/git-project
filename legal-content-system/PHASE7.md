# Phase 7: Deployment & Production Setup

## Overview

Phase 7 provides production-ready deployment configuration for the Legal Content System using Docker, Docker Compose, and Nginx reverse proxy.

## Features Implemented

### ✅ Docker Configuration
- **Backend Dockerfile**: Multi-stage Python 3.11 container with Gunicorn + Uvicorn workers
- **Frontend Dockerfile**: Multi-stage Node.js build with optimized Nginx serving
- **Production-ready**: Non-root users, health checks, security best practices

### ✅ Docker Compose Setup
- **Complete Stack**: PostgreSQL, Backend, Frontend, and Nginx services
- **Volume Management**: Persistent data for database, uploads, storage, and logs
- **Health Checks**: Automated health monitoring for all services
- **Environment Configuration**: Flexible configuration via .env file
- **Profiles**: Support for development, staging, and production environments

### ✅ Nginx Reverse Proxy
- **SSL/TLS Support**: HTTPS configuration with Let's Encrypt ready
- **Rate Limiting**: API and general traffic rate limiting
- **Gzip Compression**: Optimized content delivery
- **Security Headers**: Comprehensive security headers (HSTS, CSP, X-Frame-Options, etc.)
- **Static Asset Caching**: Long-term caching for static files
- **Upstream Load Balancing**: Backend and frontend upstream configuration

### ✅ Deployment Scripts
- **deploy.sh** (Linux/Mac): Automated deployment with health checks
- **deploy.bat** (Windows): Windows-compatible deployment script
- **backup.sh**: Automated backup of database and files
- **restore.sh**: Interactive restore from backups
- **Environment Support**: dev, staging, production modes

### ✅ Production Configuration
- **Environment Template**: `.env.production.example` with all required variables
- **Security Checklist**: Pre-deployment security verification
- **Secrets Management**: Secure handling of API keys and passwords
- **CORS Configuration**: Proper origin configuration for production

---

## File Structure

```
legal-content-system/
├── docker-compose.yml          # Main orchestration file
├── .env.production.example     # Environment template
├── deploy.sh                   # Linux/Mac deployment script
├── deploy.bat                  # Windows deployment script
├── backup.sh                   # Backup script
├── restore.sh                  # Restore script
├── backend/
│   ├── Dockerfile              # Backend container definition
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── Dockerfile              # Frontend container definition
│   └── nginx.conf              # Frontend Nginx config
└── nginx/
    ├── nginx.conf              # Main Nginx config
    └── conf.d/
        └── legal-system.conf   # Application server config
```

---

## Quick Start

### Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Domain Name** (for production with SSL)
- **Anthropic API Key**: Get from https://console.anthropic.com/

### 1. Configure Environment

```bash
# Copy environment template
cp .env.production.example .env

# Edit .env and set your values
nano .env  # or use any text editor
```

**Required Variables:**
```env
POSTGRES_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key-generate-with-openssl
ANTHROPIC_API_KEY=your-anthropic-api-key
CORS_ORIGINS=https://yourdomain.com
REACT_APP_API_URL=https://api.yourdomain.com
```

### 2. Deploy

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh production
```

**Windows:**
```cmd
deploy.bat production
```

### 3. Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Check logs
docker-compose logs -f

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

---

## Deployment Environments

### Development Mode

Runs only essential services (database, backend, frontend) without Nginx.

```bash
./deploy.sh dev
```

**Access:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

### Staging Mode

Full stack including all services.

```bash
./deploy.sh staging
```

### Production Mode

Full stack with Nginx reverse proxy, SSL/TLS support, and production optimizations.

```bash
./deploy.sh production
```

**Access:**
- Application: https://yourdomain.com
- API: https://yourdomain.com/api

---

## Docker Compose Services

### PostgreSQL Database

```yaml
Service: postgres
Port: 5432
Volume: postgres_data
Health Check: pg_isready
```

**Features:**
- PostgreSQL 15 Alpine
- Persistent data volume
- Automatic health monitoring
- Custom initialization scripts support

### Backend API

```yaml
Service: backend
Port: 8000
Workers: 4 (Gunicorn)
Worker Class: UvicornWorker
Timeout: 120s
```

**Features:**
- Python 3.11 with FastAPI
- Gunicorn WSGI server with Uvicorn workers
- Automatic database migrations
- Health endpoint
- Volume mounts for uploads, storage, logs

### Frontend

```yaml
Service: frontend
Port: 3000 (internal), 80 (container)
Built with: Node.js 18, Vite
Served by: Nginx Alpine
```

**Features:**
- Multi-stage optimized build
- Static file caching
- Gzip compression
- React Router support
- Health endpoint

### Nginx Reverse Proxy

```yaml
Service: nginx
Ports: 80, 443
Profile: production
```

**Features:**
- HTTP to HTTPS redirect
- SSL/TLS termination
- API rate limiting (10 req/s burst 20)
- General rate limiting (100 req/s burst 50)
- Static asset caching (1 year)
- Security headers
- Gzip compression

---

## SSL/TLS Configuration

### Using Let's Encrypt (Recommended)

1. **Install Certbot**:
```bash
sudo apt-get install certbot
```

2. **Obtain Certificate**:
```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

3. **Update .env**:
```env
DOMAIN_NAME=yourdomain.com
SSL_CERT_PATH=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

4. **Mount Certificates**:
Update `docker-compose.yml`:
```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/nginx/ssl:ro
```

5. **Deploy**:
```bash
./deploy.sh production
```

### Using Custom Certificates

1. Place certificates in `nginx/ssl/`:
```
nginx/ssl/
├── cert.pem
└── key.pem
```

2. Update `.env`:
```env
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
```

---

## Backup & Restore

### Create Backup

```bash
chmod +x backup.sh
./backup.sh
```

**Backup includes:**
- PostgreSQL database dump
- Uploaded files (uploads directory)
- Generated content (storage directory)

**Backup location:** `./backups/`

**Retention:** Last 7 days (automatic cleanup)

### Restore from Backup

```bash
chmod +x restore.sh
./restore.sh
```

Follow the interactive prompts to select a backup and restore.

---

## Monitoring & Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f nginx
```

### Service Management

```bash
# Restart a service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v

# Update and restart
docker-compose pull
docker-compose up -d
```

### Database Management

```bash
# Access PostgreSQL CLI
docker-compose exec postgres psql -U postgres -d legal_content_db

# Run migrations
docker-compose exec backend alembic upgrade head

# Create database backup manually
docker-compose exec postgres pg_dump -U postgres legal_content_db > backup.sql
```

### Performance Monitoring

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Service resource usage
docker-compose ps
```

---

## Environment Variables Reference

### Database
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_DB` | Database name | `legal_content_db` | Yes |
| `POSTGRES_USER` | Database user | `postgres` | Yes |
| `POSTGRES_PASSWORD` | Database password | - | Yes |
| `POSTGRES_PORT` | Database port | `5432` | No |

### Backend
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude API key | - | Yes |
| `SECRET_KEY` | JWT/session secret | - | Yes |
| `ENVIRONMENT` | Environment mode | `production` | No |
| `DEBUG` | Debug mode | `false` | No |
| `CORS_ORIGINS` | Allowed CORS origins | - | Yes |
| `LOG_LEVEL` | Logging level | `info` | No |
| `MAX_UPLOAD_SIZE_MB` | Max file upload size | `50` | No |

### Frontend
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8000` | Yes |
| `FRONTEND_PORT` | Frontend port | `3000` | No |

### Nginx (Production)
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DOMAIN_NAME` | Domain name | - | Yes |
| `SSL_CERT_PATH` | SSL certificate path | - | Yes |
| `SSL_KEY_PATH` | SSL private key path | - | Yes |

---

## Security Checklist

Before deploying to production, ensure:

- [ ] Changed all default passwords
- [ ] Generated secure `SECRET_KEY` (use: `openssl rand -hex 32`)
- [ ] Configured `ANTHROPIC_API_KEY`
- [ ] Updated `CORS_ORIGINS` with actual domain
- [ ] Set `DEBUG=false`
- [ ] Configured SSL/TLS certificates
- [ ] Reviewed and adjusted rate limiting rules
- [ ] Set up automated database backups
- [ ] Configured monitoring and alerting
- [ ] Tested deployment in staging environment
- [ ] Documented recovery procedures
- [ ] Set up log rotation
- [ ] Configured firewall rules

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs backend

# Check if port is already in use
netstat -tuln | grep 8000

# Rebuild without cache
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Database Connection Errors

```bash
# Check if database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify DATABASE_URL in .env
# Format: postgresql://user:password@postgres:5432/dbname
```

### Frontend Can't Connect to Backend

```bash
# Verify REACT_APP_API_URL in .env
# In development: http://localhost:8000
# In production: https://api.yourdomain.com

# Check CORS_ORIGINS includes frontend domain
# Rebuild frontend after changing environment variables
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Nginx 502 Bad Gateway

```bash
# Check if backend is running
docker-compose ps backend

# Check backend health
curl http://localhost:8000/health

# Check Nginx logs
docker-compose logs nginx

# Verify upstream configuration in nginx/conf.d/legal-system.conf
```

### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes

# Remove old images
docker image prune -a
```

---

## Performance Optimization

### Database

```sql
-- Add indexes for common queries (run in psql)
CREATE INDEX idx_verdicts_status ON verdicts(processing_status);
CREATE INDEX idx_articles_publish_status ON articles(publish_status);
CREATE INDEX idx_articles_wordpress_site ON articles(wordpress_site_id);
```

### Backend

- Increase Gunicorn workers for high traffic: `--workers 8`
- Adjust timeout for long-running requests: `--timeout 300`
- Enable keep-alive connections
- Use connection pooling for database

### Frontend

- Enable CDN for static assets
- Implement service worker for offline support
- Use lazy loading for routes
- Optimize images before upload

### Nginx

- Increase worker connections: `worker_connections 2048`
- Enable HTTP/2 push for critical resources
- Configure appropriate cache sizes
- Use upstream keepalive connections

---

## Scaling Considerations

### Horizontal Scaling

1. **Multiple Backend Instances**:
```yaml
backend:
  deploy:
    replicas: 3
```

2. **Load Balancer**:
Configure Nginx upstream with multiple backend servers

3. **Database Replication**:
Set up PostgreSQL streaming replication for read replicas

### Vertical Scaling

Update resource limits in `docker-compose.yml`:
```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

---

## Production Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Environment variables configured
- [ ] Database migrations prepared
- [ ] Backup created
- [ ] SSL certificates obtained
- [ ] Domain DNS configured
- [ ] Monitoring tools configured

### Deployment
- [ ] Pull latest code
- [ ] Build Docker images
- [ ] Run database migrations
- [ ] Deploy services
- [ ] Verify health checks
- [ ] Test critical workflows

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Verify all features working
- [ ] Check performance metrics
- [ ] Notify stakeholders
- [ ] Update documentation
- [ ] Tag release in Git

---

## Support & Resources

### Documentation
- Docker: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- Nginx: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/docs/

### Monitoring Tools
- **Logs**: Docker logs, journalctl
- **Metrics**: Prometheus + Grafana
- **Uptime**: UptimeRobot, Pingdom
- **APM**: New Relic, DataDog

### Getting Help
- Check logs first: `docker-compose logs -f`
- Review this documentation
- Check Docker Compose configuration
- Verify environment variables
- Test services individually

---

## Phase 7 Status

✅ **COMPLETED**

**Deliverables:**
1. ✅ Backend Dockerfile with production configuration
2. ✅ Frontend Dockerfile with multi-stage build
3. ✅ Docker Compose orchestration file
4. ✅ Nginx reverse proxy configuration
5. ✅ Deployment scripts (Linux/Mac and Windows)
6. ✅ Backup and restore scripts
7. ✅ Production environment template
8. ✅ Comprehensive documentation

**Next Steps:**
- Test deployment in staging environment
- Configure monitoring and alerting
- Set up CI/CD pipeline (optional)
- Configure automated backups
- Implement log aggregation (optional)

---

**Created**: Phase 7 - January 2026
**Status**: Production Ready 🚀
