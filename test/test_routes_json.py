import json

import pytest

from app.models.endpoint import Endpoint
from app.utils import search as search_mod


def test_captcha_json_block(client, monkeypatch):
    def fake_new_query(self):
        self.query = 'test'
        return self.query

    def fake_generate(self):
        # Inject a captcha marker into HTML so route returns 503 JSON
        return '<div>div class="g-recaptcha"</div>'

    monkeypatch.setattr(search_mod.Search, 'new_search_query', fake_new_query)
    monkeypatch.setattr(search_mod.Search, 'generate_response', fake_generate)

    rv = client.get(f'/{Endpoint.search}?q=test&format=json')
    assert rv._status_code == 503
    data = json.loads(rv.data)
    assert data['blocked'] is True
    assert 'error_message' in data


def test_captcha_json_structured_fields(client, monkeypatch):
    """Verify rate-limit JSON includes structured error fields."""
    def fake_new_query(self):
        self.query = 'test'
        return self.query

    def fake_generate(self):
        return '<div>div class="g-recaptcha"</div>'

    monkeypatch.setattr(search_mod.Search, 'new_search_query', fake_new_query)
    monkeypatch.setattr(search_mod.Search, 'generate_response', fake_generate)

    rv = client.get(f'/{Endpoint.search}?q=test&format=json')
    assert rv._status_code == 503
    data = json.loads(rv.data)
    assert data['error'] is True
    assert data['error_type'] == 'rate_limit'
    assert data['recoverable'] is True
    assert isinstance(data['suggestions'], list)
    assert len(data['suggestions']) > 0


def test_json_search_result_count(client):
    """Verify JSON search results include result_count metadata."""
    rv = client.get(f'/{Endpoint.search}?q=test&format=json')
    assert rv._status_code == 200
    data = json.loads(rv.data)
    assert 'result_count' in data
    assert data['result_count'] == len(data['results'])


def test_internal_error_json(client, monkeypatch):
    """Verify internal errors return structured JSON when format=json."""
    def fake_new_query(self):
        self.query = 'test'
        return self.query

    def fake_generate(self):
        raise RuntimeError('unexpected failure')

    monkeypatch.setattr(search_mod.Search, 'new_search_query', fake_new_query)
    monkeypatch.setattr(search_mod.Search, 'generate_response', fake_generate)

    rv = client.get(f'/{Endpoint.search}?q=test&format=json')
    assert rv._status_code == 500
    data = json.loads(rv.data)
    assert data['error'] is True
    assert data['error_type'] == 'internal_error'
    assert data['recoverable'] is True
    assert isinstance(data['suggestions'], list)
    assert len(data['suggestions']) > 0

