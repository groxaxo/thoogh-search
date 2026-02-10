"""SearXNG Instance API Client

This module provides a client for querying SearXNG instances to retrieve
Google search results. SearXNG is a privacy-respecting metasearch engine
that aggregates results from multiple search engines including Google.

By routing queries through a SearXNG instance, we avoid direct interaction
with Google's anti-bot measures (JavaScript requirements, CAPTCHAs, etc.)
while still obtaining Google search results.

Inspired by:
- SearXNG (https://github.com/searxng/searxng) - metasearch engine architecture
- Scrapling (https://github.com/D4Vinci/Scrapling) - anti-detection techniques
"""

import httpx
from typing import Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse, quote


# Default public SearXNG instances (used as fallbacks)
DEFAULT_SEARXNG_INSTANCES = [
    'https://search.bus-hit.me',
    'https://search.sapti.me',
    'https://searx.tiekoetter.com',
]


class SearXNGException(Exception):
    """Exception raised for SearXNG API errors"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


@dataclass
class SearXNGResult:
    """Represents a single search result from a SearXNG instance"""
    title: str
    url: str
    content: str
    engine: str = ''
    score: float = 0.0
    category: str = 'general'
    # Image-specific fields
    img_src: Optional[str] = None
    thumbnail_src: Optional[str] = None
    thumbnail: Optional[str] = None


@dataclass
class SearXNGResponse:
    """Represents a complete response from a SearXNG instance"""
    results: list
    query: str
    number_of_results: int = 0
    suggestions: list = field(default_factory=list)
    corrections: list = field(default_factory=list)
    answers: list = field(default_factory=list)
    infoboxes: list = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_error(self) -> bool:
        return self.error is not None

    @property
    def has_results(self) -> bool:
        return len(self.results) > 0


class SearXNGClient:
    """Client for querying SearXNG instances for search results.

    SearXNG provides a JSON API at /search?format=json that returns
    structured search results from multiple engines. By specifying
    engines=google, we can get Google-specific results through
    SearXNG's anti-detection infrastructure.

    Usage:
        client = SearXNGClient(instance_url='https://my-searxng.example.com')
        response = client.search('python programming')

        if response.has_error:
            print(f"Error: {response.error}")
        else:
            for result in response.results:
                print(f"{result.title}: {result.url}")
    """

    def __init__(
        self,
        instance_url: str,
        timeout: float = 15.0,
        engines: str = 'google',
        http_client: Optional[httpx.Client] = None
    ):
        """Initialize SearXNG client.

        Args:
            instance_url: Base URL of the SearXNG instance (e.g. https://searx.example.com)
            timeout: Request timeout in seconds
            engines: Comma-separated list of engines to query (default: 'google')
            http_client: Optional pre-configured httpx.Client
        """
        # Normalize URL: remove trailing slash
        self.instance_url = instance_url.rstrip('/')
        self.timeout = timeout
        self.engines = engines
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                'Accept': 'application/json',
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/127.0.0.0 Safari/537.36'
                ),
            }
        )

    def search(
        self,
        query: str,
        categories: str = 'general',
        language: str = '',
        pageno: int = 1,
        time_range: str = '',
        safesearch: int = 0,
        engines: str = ''
    ) -> SearXNGResponse:
        """Execute a search query against the SearXNG instance.

        Args:
            query: Search query string
            categories: Search categories (general, images, news, etc.)
            language: Language code (e.g. 'en', 'de', 'fr')
            pageno: Page number (1-based)
            time_range: Time range filter ('day', 'week', 'month', 'year')
            safesearch: Safe search level (0=off, 1=moderate, 2=strict)
            engines: Override engines (comma-separated). If empty, uses default.

        Returns:
            SearXNGResponse with results or error information
        """
        params = {
            'q': query,
            'format': 'json',
            'categories': categories,
            'pageno': pageno,
            'safesearch': safesearch,
        }

        # Use specified engines or fall back to instance default
        effective_engines = engines or self.engines
        if effective_engines:
            params['engines'] = effective_engines

        if language:
            # SearXNG uses language codes like 'en', 'en-US', etc.
            lang = language.replace('lang_', '')
            if lang:
                params['language'] = lang

        if time_range:
            params['time_range'] = time_range

        search_url = f'{self.instance_url}/search'

        try:
            response = self._client.get(search_url, params=params)

            if response.status_code != 200:
                return SearXNGResponse(
                    results=[],
                    query=query,
                    error=f'SearXNG returned status {response.status_code}'
                )

            data = response.json()

            # Check for error in response
            if 'error' in data and data['error']:
                error_msg = data['error'] if isinstance(data['error'], str) else str(data['error'])
                return SearXNGResponse(
                    results=[],
                    query=query,
                    error=error_msg
                )

            # Parse results
            results = []
            for item in data.get('results', []):
                results.append(SearXNGResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    content=item.get('content', ''),
                    engine=item.get('engine', ''),
                    score=float(item.get('score', 0)),
                    category=item.get('category', 'general'),
                    img_src=item.get('img_src'),
                    thumbnail_src=item.get('thumbnail_src'),
                    thumbnail=item.get('thumbnail'),
                ))

            # Parse suggestions
            suggestions = list(data.get('suggestions', []))

            # Parse corrections
            corrections = list(data.get('corrections', []))

            # Parse answers
            answers = []
            for answer in data.get('answers', []):
                if isinstance(answer, dict):
                    answers.append(answer.get('answer', str(answer)))
                else:
                    answers.append(str(answer))

            return SearXNGResponse(
                results=results,
                query=query,
                number_of_results=int(data.get('number_of_results', 0)),
                suggestions=suggestions,
                corrections=corrections,
                answers=answers,
                infoboxes=data.get('infoboxes', []),
            )

        except httpx.TimeoutException:
            return SearXNGResponse(
                results=[],
                query=query,
                error='Request to SearXNG instance timed out'
            )
        except httpx.RequestError as e:
            return SearXNGResponse(
                results=[],
                query=query,
                error=f'Failed to connect to SearXNG instance: {str(e)}'
            )
        except (ValueError, KeyError) as e:
            return SearXNGResponse(
                results=[],
                query=query,
                error=f'Invalid response from SearXNG instance: {str(e)}'
            )

    def close(self):
        """Close the HTTP client if we own it."""
        if self._owns_client:
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def searxng_results_to_html(response: SearXNGResponse, query: str) -> str:
    """Convert SearXNG API response to HTML matching Whoogle's result format.

    This generates HTML that mimics the structure expected by Whoogle's
    existing filter and result processing pipeline.

    Args:
        response: SearXNGResponse from the API
        query: Original search query

    Returns:
        HTML string formatted like Google search results
    """
    if response.has_error:
        return _error_html('SearXNG Error', response.error)

    if not response.has_results:
        return _no_results_html(query)

    # Check if this is an image search
    is_image = any(r.category == 'images' or r.img_src for r in response.results)
    if is_image:
        return _image_results_html(response, query)

    # Build HTML results matching Whoogle's expected structure
    results_html = []

    for result in response.results:
        title = _escape_html(result.title)
        content = _escape_html(result.content)
        link = result.url
        display_link = _escape_html(urlparse(link).netloc if link else '')

        result_html = f'''
        <div class="ZINbbc xpd O9g5cc uUPGi">
            <div class="kCrYT">
                <a href="{_escape_html(link)}">
                    <h3 class="BNeawe vvjwJb AP7Wnd">{title}</h3>
                    <div class="BNeawe UPmit AP7Wnd luh4tb" style="color: var(--whoogle-result-url);">{display_link}</div>
                </a>
            </div>
            <div class="kCrYT">
                <div class="BNeawe s3v9rd AP7Wnd">
                    <span class="VwiC3b">{content}</span>
                </div>
            </div>
        </div>
        '''
        results_html.append(result_html)

    # Build pagination
    pagination_html = ''
    if response.number_of_results > 10 or len(response.results) >= 10:
        # SearXNG uses pageno (1-based page numbers)
        # We need to convert to Whoogle's start parameter (0-based, 10 per page)
        pagination_html = _pagination_html(query)

    # Add suggestions if available
    suggestions_html = ''
    if response.suggestions:
        suggestion_links = []
        for suggestion in response.suggestions[:5]:
            escaped = _escape_html(suggestion)
            encoded = quote(suggestion)
            suggestion_links.append(
                f'<a href="search?q={encoded}">{escaped}</a>'
            )
        suggestions_html = (
            '<div style="padding: 10px 0;">'
            '<span style="color: #70757a;">Related searches: </span>'
            + ' &middot; '.join(suggestion_links) +
            '</div>'
        )

    return f'''
    <html>
    <body>
        <div id="main" data-searxng="true">
            <div id="cnt">
                <div id="rcnt">
                    <div id="center_col">
                        <div id="res">
                            <div id="search">
                                <div id="rso">
                                    {''.join(results_html)}
                                </div>
                            </div>
                        </div>
                        {suggestions_html}
                        {pagination_html}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''


def _image_results_html(response: SearXNGResponse, query: str) -> str:
    """Generate HTML for image search results from SearXNG.

    Args:
        response: SearXNGResponse with image results
        query: Original search query

    Returns:
        HTML string formatted for image results display
    """
    from flask import render_template

    results = []
    for result in response.results:
        image_url = result.img_src or result.url
        thumbnail_url = result.thumbnail_src or result.thumbnail or image_url
        web_page = result.url
        domain = urlparse(web_page).netloc if web_page else ''

        results.append({
            'domain': domain,
            'img_url': image_url,
            'web_page': web_page,
            'img_tbn': thumbnail_url
        })

    next_link = None
    if len(response.results) >= 10:
        next_link = f'search?q={quote(query)}&tbm=isch&start=10'

    return render_template(
        'imageresults.html',
        length=len(results),
        results=results,
        view_label="View Image",
        next_link=next_link
    )


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ''
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def _error_html(title: str, message: str) -> str:
    """Generate error HTML."""
    return f'''
    <html>
    <body>
        <div id="main">
            <div style="padding: 20px; text-align: center;">
                <h2 style="color: #d93025;">{_escape_html(title)}</h2>
                <p>{_escape_html(message)}</p>
            </div>
        </div>
    </body>
    </html>
    '''


def _no_results_html(query: str) -> str:
    """Generate no results HTML."""
    return f'''
    <html>
    <body>
        <div id="main">
            <div style="padding: 20px;">
                <p>No results found for <b>{_escape_html(query)}</b></p>
            </div>
        </div>
    </body>
    </html>
    '''


def _pagination_html(query: str) -> str:
    """Generate simple pagination link."""
    encoded_query = quote(query)
    return f'''
    <div id="foot" style="text-align: center; padding: 20px;">
        <a href="search?q={encoded_query}&start=10">Next</a>
    </div>
    '''
