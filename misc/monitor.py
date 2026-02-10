#!/usr/bin/env python3
"""
Health and metrics monitoring script for Whoogle Search.

This script can be used to monitor Whoogle instance health and collect
basic metrics for external monitoring systems like Prometheus, Grafana, etc.

Usage:
    python3 monitor.py --url http://localhost:5000 [--format json|prometheus]
"""

import argparse
import time
import sys
import json
try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx")
    sys.exit(1)


def check_health(base_url: str) -> dict:
    """Check the health of a Whoogle instance."""
    metrics = {
        'timestamp': int(time.time()),
        'url': base_url,
        'status': 'unknown',
        'response_time_ms': 0,
        'version_check': False,
        'search_test': False
    }
    
    try:
        # Health check
        start = time.time()
        response = httpx.get(f"{base_url}/healthz", timeout=10.0)
        metrics['response_time_ms'] = int((time.time() - start) * 1000)
        
        if response.status_code == 200:
            metrics['status'] = 'healthy'
        else:
            metrics['status'] = f'unhealthy (HTTP {response.status_code})'
        
        # Check main page loads
        response = httpx.get(base_url, timeout=10.0)
        if response.status_code == 200 and 'Whoogle' in response.text:
            metrics['version_check'] = True
        
        # Test search functionality (minimal query)
        response = httpx.post(
            f"{base_url}/search",
            data={'q': 'test'},
            timeout=15.0,
            follow_redirects=True
        )
        if response.status_code == 200:
            metrics['search_test'] = True
            
    except httpx.ConnectError:
        metrics['status'] = 'unreachable'
    except httpx.TimeoutException:
        metrics['status'] = 'timeout'
    except Exception as e:
        metrics['status'] = f'error: {str(e)}'
    
    return metrics


def format_json(metrics: dict) -> str:
    """Format metrics as JSON."""
    return json.dumps(metrics, indent=2)


def format_prometheus(metrics: dict) -> str:
    """Format metrics in Prometheus exposition format."""
    lines = [
        "# HELP whoogle_up Whether Whoogle is up and responding",
        "# TYPE whoogle_up gauge",
        f"whoogle_up{{instance=\"{metrics['url']}\"}} {1 if metrics['status'] == 'healthy' else 0}",
        "",
        "# HELP whoogle_response_time_milliseconds Response time in milliseconds",
        "# TYPE whoogle_response_time_milliseconds gauge",
        f"whoogle_response_time_milliseconds{{instance=\"{metrics['url']}\"}} {metrics['response_time_ms']}",
        "",
        "# HELP whoogle_search_test Whether search functionality is working",
        "# TYPE whoogle_search_test gauge",
        f"whoogle_search_test{{instance=\"{metrics['url']}\"}} {1 if metrics['search_test'] else 0}",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Monitor Whoogle Search instance health and metrics'
    )
    parser.add_argument(
        '--url',
        default='http://localhost:5000',
        help='Whoogle instance URL (default: http://localhost:5000)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'prometheus'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously (every 60 seconds)'
    )
    
    args = parser.parse_args()
    
    try:
        while True:
            metrics = check_health(args.url)
            
            if args.format == 'json':
                print(format_json(metrics))
            else:
                print(format_prometheus(metrics))
            
            if not args.continuous:
                break
                
            # Exit code based on health status
            if metrics['status'] != 'healthy':
                sys.exit(1)
            
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
        sys.exit(0)


if __name__ == '__main__':
    main()
