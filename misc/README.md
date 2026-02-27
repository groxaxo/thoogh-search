# Miscellaneous Tools and Utilities

This directory contains various tools and configurations for operating and maintaining Whoogle Search.

## Configuration Examples

### nginx-2026-example.conf
Modern Nginx reverse proxy configuration following 2026 security best practices:
- TLS 1.3 only
- HSTS with preloading
- Content Security Policy (CSP)
- Rate limiting
- Security headers
- OCSP stapling
- HTTP/2 support

**Usage:**
```bash
# Copy and customize for your domain
sudo cp nginx-2026-example.conf /etc/nginx/sites-available/whoogle
sudo ln -s /etc/nginx/sites-available/whoogle /etc/nginx/sites-enabled/
# Edit the file to set your domain and SSL certificate paths
sudo nano /etc/nginx/sites-available/whoogle
sudo nginx -t
sudo systemctl reload nginx
```

## Monitoring & Maintenance

### monitor.py
Health monitoring script for Whoogle instances. Can output metrics in JSON or Prometheus format.

**Requirements:**
```bash
pip install httpx
```

**Usage:**
```bash
# Single health check (JSON format)
python3 monitor.py --url http://localhost:5000

# Prometheus metrics format
python3 monitor.py --url http://localhost:5000 --format prometheus

# Continuous monitoring (every 60 seconds)
python3 monitor.py --url http://localhost:5000 --continuous

# Monitor remote instance
python3 monitor.py --url https://search.example.com --format prometheus
```

**Integration with Prometheus:**
1. Set up a cron job or systemd service to run the monitor script
2. Configure Prometheus to scrape the metrics endpoint
3. Use Grafana to visualize the metrics

**Example systemd service:**
```ini
[Unit]
Description=Whoogle Metrics Exporter
After=network.target

[Service]
Type=simple
User=whoogle
ExecStart=/usr/bin/python3 /path/to/monitor.py --url http://localhost:5000 --format prometheus --continuous
Restart=always

[Install]
WantedBy=multi-user.target
```

## User Agent Tools

### generate_uas.py
Generates randomized Opera User Agent strings for anti-detection.

### check_google_user_agents.py
Validates User Agent strings against Google's anti-bot measures.

## Tor Configuration

### tor/
Contains Tor daemon configuration and startup scripts for anonymous searching.

## Translation Updates

### update-translations.py
Script for updating translation files.

## Platform-Specific Scripts

### heroku-regen.sh
Script for regenerating configuration on Heroku deployments (legacy).

### replit.py
Configuration helper for Replit deployments (legacy).

## Best Practices for Production

1. **Monitoring**: Use `monitor.py` with your monitoring stack
2. **Reverse Proxy**: Deploy behind Nginx using the example configuration
3. **Security**: Regularly update dependencies and scan for vulnerabilities
4. **Backups**: Back up your custom configuration and bangs
5. **Logging**: Use structured logging (JSON) for log aggregation
6. **Rate Limiting**: Implement at both Nginx and application level
7. **Health Checks**: Configure health checks in your orchestration system

## Contributing

When adding new tools to this directory:
1. Include comprehensive documentation
2. Follow the existing naming conventions
3. Make scripts executable with shebang lines
4. Include usage examples
5. Document any dependencies
