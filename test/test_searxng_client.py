"""Tests for the SearXNG client module."""

import json
import httpx
import pytest

from app.services.searxng_client import (
    SearXNGClient,
    SearXNGResponse,
    SearXNGResult,
    SearXNGException,
    searxng_results_to_html,
    _escape_html,
)


# --- Sample response data for mocking ---

SAMPLE_RESULTS = {
    'query': 'python programming',
    'number_of_results': 1000,
    'results': [
        {
            'title': 'Python.org',
            'url': 'https://www.python.org/',
            'content': 'The official home of the Python Programming Language.',
            'engine': 'google',
            'score': 1.0,
            'category': 'general',
        },
        {
            'title': 'Python Tutorial - W3Schools',
            'url': 'https://www.w3schools.com/python/',
            'content': 'Well organized and easy to understand Web building tutorials.',
            'engine': 'google',
            'score': 0.9,
            'category': 'general',
        },
    ],
    'suggestions': ['python programming language', 'python tutorial'],
    'corrections': [],
    'answers': [],
    'infoboxes': [],
}

SAMPLE_IMAGE_RESULTS = {
    'query': 'python logo',
    'number_of_results': 500,
    'results': [
        {
            'title': 'Python Logo',
            'url': 'https://example.com/python-logo',
            'content': '',
            'engine': 'google',
            'category': 'images',
            'img_src': 'https://example.com/python-logo.png',
            'thumbnail_src': 'https://example.com/python-logo-thumb.png',
        },
    ],
    'suggestions': [],
    'corrections': [],
    'answers': [],
    'infoboxes': [],
}

SAMPLE_ERROR = {
    'error': 'search error',
}

SAMPLE_NO_RESULTS = {
    'query': 'xyznonexistenttermzzz',
    'number_of_results': 0,
    'results': [],
    'suggestions': [],
    'corrections': [],
    'answers': [],
    'infoboxes': [],
}


# --- Unit tests for SearXNGResult ---

class TestSearXNGResult:
    def test_basic_result(self):
        result = SearXNGResult(
            title='Test Title',
            url='https://example.com',
            content='Test content snippet.',
        )
        assert result.title == 'Test Title'
        assert result.url == 'https://example.com'
        assert result.content == 'Test content snippet.'
        assert result.engine == ''
        assert result.score == 0.0

    def test_image_result(self):
        result = SearXNGResult(
            title='Image Title',
            url='https://example.com/page',
            content='',
            img_src='https://example.com/image.jpg',
            thumbnail_src='https://example.com/thumb.jpg',
        )
        assert result.img_src == 'https://example.com/image.jpg'
        assert result.thumbnail_src == 'https://example.com/thumb.jpg'


# --- Unit tests for SearXNGResponse ---

class TestSearXNGResponse:
    def test_successful_response(self):
        results = [SearXNGResult(title='Test', url='https://example.com', content='')]
        response = SearXNGResponse(
            results=results,
            query='test',
            number_of_results=100,
        )
        assert response.has_results is True
        assert response.has_error is False
        assert len(response.results) == 1

    def test_error_response(self):
        response = SearXNGResponse(
            results=[],
            query='test',
            error='Connection failed',
        )
        assert response.has_results is False
        assert response.has_error is True
        assert response.error == 'Connection failed'

    def test_no_results(self):
        response = SearXNGResponse(results=[], query='test')
        assert response.has_results is False
        assert response.has_error is False


# --- Unit tests for SearXNGClient ---

class TestSearXNGClient:
    def _mock_transport(self, response_data, status_code=200):
        """Create a mock transport that returns the given response."""
        return httpx.MockTransport(
            lambda request: httpx.Response(
                status_code,
                json=response_data,
            )
        )

    def test_successful_search(self):
        transport = self._mock_transport(SAMPLE_RESULTS)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        )
        response = client.search('python programming')
        assert response.has_results is True
        assert response.has_error is False
        assert len(response.results) == 2
        assert response.results[0].title == 'Python.org'
        assert response.results[0].url == 'https://www.python.org/'
        assert response.results[0].engine == 'google'
        assert response.number_of_results == 1000
        assert len(response.suggestions) == 2
        client.close()

    def test_search_with_error_response(self):
        transport = self._mock_transport(SAMPLE_ERROR)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        )
        response = client.search('test')
        assert response.has_error is True
        assert 'search error' in response.error
        client.close()

    def test_search_no_results(self):
        transport = self._mock_transport(SAMPLE_NO_RESULTS)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        )
        response = client.search('xyznonexistenttermzzz')
        assert response.has_error is False
        assert response.has_results is False
        assert response.number_of_results == 0
        client.close()

    def test_search_http_error(self):
        transport = self._mock_transport({'error': 'Server error'}, status_code=500)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        )
        response = client.search('test')
        assert response.has_error is True
        assert '500' in response.error
        client.close()

    def test_search_timeout(self):
        def timeout_handler(request):
            raise httpx.ReadTimeout('Connection timed out')

        transport = httpx.MockTransport(timeout_handler)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        )
        response = client.search('test')
        assert response.has_error is True
        assert 'timed out' in response.error
        client.close()

    def test_search_connection_error(self):
        def error_handler(request):
            raise httpx.ConnectError('Connection refused')

        transport = httpx.MockTransport(error_handler)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        )
        response = client.search('test')
        assert response.has_error is True
        assert 'connect' in response.error.lower() or 'Failed' in response.error
        client.close()

    def test_url_normalization(self):
        transport = self._mock_transport(SAMPLE_NO_RESULTS)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com/',
            http_client=mock_client,
        )
        # URL should be normalized (no trailing slash)
        assert client.instance_url == 'https://searx.example.com'
        client.close()

    def test_context_manager(self):
        transport = self._mock_transport(SAMPLE_RESULTS)
        mock_client = httpx.Client(transport=transport)
        with SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        ) as client:
            response = client.search('test')
            assert response.has_results is True

    def test_search_with_language(self):
        """Verify that language parameter is passed correctly."""
        captured_requests = []

        def capture_handler(request):
            captured_requests.append(request)
            return httpx.Response(200, json=SAMPLE_NO_RESULTS)

        transport = httpx.MockTransport(capture_handler)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        )
        client.search('test', language='lang_en')
        assert len(captured_requests) == 1
        assert 'language=en' in str(captured_requests[0].url)
        client.close()

    def test_search_with_safesearch(self):
        """Verify safesearch parameter is passed correctly."""
        captured_requests = []

        def capture_handler(request):
            captured_requests.append(request)
            return httpx.Response(200, json=SAMPLE_NO_RESULTS)

        transport = httpx.MockTransport(capture_handler)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        )
        client.search('test', safesearch=2)
        assert len(captured_requests) == 1
        assert 'safesearch=2' in str(captured_requests[0].url)
        client.close()

    def test_search_with_time_range(self):
        """Verify time_range parameter is passed correctly."""
        captured_requests = []

        def capture_handler(request):
            captured_requests.append(request)
            return httpx.Response(200, json=SAMPLE_NO_RESULTS)

        transport = httpx.MockTransport(capture_handler)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        )
        client.search('test', time_range='week')
        assert len(captured_requests) == 1
        assert 'time_range=week' in str(captured_requests[0].url)
        client.close()

    def test_search_with_image_category(self):
        """Verify image search uses correct category."""
        transport = self._mock_transport(SAMPLE_IMAGE_RESULTS)
        mock_client = httpx.Client(transport=transport)
        client = SearXNGClient(
            instance_url='https://searx.example.com',
            http_client=mock_client,
        )
        response = client.search('python logo', categories='images')
        assert response.has_results is True
        assert response.results[0].img_src == 'https://example.com/python-logo.png'
        client.close()


# --- Unit tests for HTML conversion ---

class TestSearXNGResultsToHtml:
    def test_results_to_html(self):
        results = [
            SearXNGResult(
                title='Python.org',
                url='https://www.python.org/',
                content='The official Python site.',
                engine='google',
            ),
        ]
        response = SearXNGResponse(
            results=results,
            query='python',
            number_of_results=100,
        )
        html = searxng_results_to_html(response, 'python')
        assert 'Python.org' in html
        assert 'https://www.python.org/' in html
        assert 'The official Python site.' in html
        assert 'id="main"' in html
        assert 'data-searxng' in html

    def test_error_to_html(self):
        response = SearXNGResponse(
            results=[],
            query='test',
            error='Connection failed',
        )
        html = searxng_results_to_html(response, 'test')
        assert 'SearXNG Error' in html
        assert 'Connection failed' in html

    def test_no_results_to_html(self):
        response = SearXNGResponse(results=[], query='xyzzzz')
        html = searxng_results_to_html(response, 'xyzzzz')
        assert 'No results found' in html
        assert 'xyzzzz' in html

    def test_suggestions_in_html(self):
        response = SearXNGResponse(
            results=[
                SearXNGResult(
                    title='Result',
                    url='https://example.com',
                    content='Content',
                ),
            ],
            query='test',
            suggestions=['suggestion1', 'suggestion2'],
        )
        html = searxng_results_to_html(response, 'test')
        assert 'suggestion1' in html
        assert 'suggestion2' in html


# --- Unit tests for helper functions ---

class TestHelpers:
    def test_escape_html(self):
        assert _escape_html('<script>') == '&lt;script&gt;'
        assert _escape_html('"test"') == '&quot;test&quot;'
        assert _escape_html("it's") == "it&#39;s"
        assert _escape_html('a & b') == 'a &amp; b'
        assert _escape_html('') == ''
        assert _escape_html(None) == ''
