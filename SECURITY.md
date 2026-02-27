# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| < 1.0   | :x:                |

Always use the latest version for the best security and features.

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these guidelines:

### Where to Report

**Please DO NOT open a public GitHub issue for security vulnerabilities.**

Instead, please report security vulnerabilities through one of these methods:

1. **GitHub Security Advisories** (Preferred)
   - Go to the [Security tab](https://github.com/benbusby/whoogle-search/security/advisories)
   - Click "Report a vulnerability"
   - Fill out the form with details

2. **Email**
   - Send details to the repository maintainers
   - Include "SECURITY" in the subject line
   - Provide as much detail as possible

### What to Include

Please include the following information:

- **Description**: Clear description of the vulnerability
- **Impact**: What an attacker could do with this vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Affected Versions**: Which versions are affected
- **Proof of Concept**: If possible, provide a PoC (without causing harm)
- **Suggested Fix**: If you have ideas on how to fix it

### Response Timeline

- **Initial Response**: Within 48 hours
- **Assessment**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium: Within 30 days
  - Low: Next regular release

### Disclosure Policy

- We follow coordinated disclosure principles
- We will work with you to understand and fix the issue
- Public disclosure will be made after a fix is available
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices for Users

### Deployment

1. **Always use HTTPS** in production environments
2. **Keep Whoogle updated** to the latest version
3. **Use strong authentication** if exposed to the internet
4. **Run behind a reverse proxy** with additional security headers
5. **Enable Tor** for maximum anonymity
6. **Monitor logs** for suspicious activity

### Docker Security

```bash
# Run with minimal privileges
docker run --user 927:927 \
  --cap-drop=ALL \
  --read-only \
  --tmpfs /tmp \
  --security-opt=no-new-privileges \
  benbusby/whoogle-search
```

### Network Security

- Use VPN or Tor for queries
- Configure DNS-over-HTTPS/TLS
- Implement rate limiting at proxy level
- Use fail2ban for brute force protection

### Configuration Security

- Never commit secrets to version control
- Use environment variables for sensitive data
- Encrypt configuration preferences
- Rotate authentication credentials regularly

## Known Security Features

### Privacy Protection

- **No logging** of search queries by default
- **No IP tracking** when properly configured
- **No cookies** from third parties
- **Content proxying** to hide your IP from external sites
- **User Agent rotation** to prevent fingerprinting

### Built-in Security

- **CSP headers** when `WHOOGLE_CSP` is set
- **Tor support** for anonymized requests
- **HTTPS enforcement** option
- **Basic authentication** built-in
- **Session encryption** for preferences

## Security Scanning

### Automated Scanning

This project uses:
- Dependabot for dependency vulnerability scanning
- CodeQL for code security analysis
- Docker image scanning for container vulnerabilities

### Manual Testing

We encourage security researchers to test Whoogle:
- Perform security audits
- Test for common web vulnerabilities
- Review code for security issues
- Report findings responsibly

## Security Updates

Security updates are released as soon as possible after discovery and verification. Users are notified through:

1. GitHub Security Advisories
2. Release notes with [SECURITY] tag
3. Docker Hub image updates

## Acknowledgments

We thank security researchers who have responsibly disclosed vulnerabilities and helped improve Whoogle's security.

## Questions?

For general security questions (not vulnerability reports), please open a regular GitHub issue or discussion.
