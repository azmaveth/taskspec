"""
Tests for the search module.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from taskspec.search import search_web


def test_search_web_no_api_key():
    """Test search_web function when no API key is available."""
    # Patch os.getenv to return None for the API key
    with patch('os.getenv', return_value=None):
        results = search_web("test query")
        assert results == []


@patch('requests.get')
def test_search_web_success(mock_get):
    """Test search_web function with a successful API response."""
    # Mock the API key
    with patch('os.getenv', return_value='fake_api_key'):
        # Create a mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'web': {
                'results': [
                    {
                        'title': 'Test Result 1',
                        'description': 'Description 1',
                        'url': 'https://example.com/1'
                    },
                    {
                        'title': 'Test Result 2',
                        'description': 'Description 2',
                        'url': 'https://example.com/2'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Call the function
        results = search_web("test query", max_results=2)
        
        # Verify the results
        assert len(results) == 2
        assert results[0]['title'] == 'Test Result 1'
        assert results[0]['description'] == 'Description 1'
        assert results[0]['url'] == 'https://example.com/1'
        assert results[1]['title'] == 'Test Result 2'
        
        # Verify the correct URL and parameters were used
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs['headers']['X-Subscription-Token'] == 'fake_api_key'
        assert 'test query' in kwargs['params']['q']
        assert kwargs['params']['count'] == 2


@patch('requests.get')
def test_search_web_http_error(mock_get):
    """Test search_web function when the API returns an error."""
    # Mock the API key
    with patch('os.getenv', return_value='fake_api_key'):
        # Create a mock response that raises an exception
        mock_get.side_effect = Exception("HTTP Error")
        
        # Call the function
        results = search_web("test query")
        
        # Verify empty results are returned
        assert results == []


@patch('requests.get')
def test_search_web_invalid_response(mock_get):
    """Test search_web function with an invalid API response."""
    # Mock the API key
    with patch('os.getenv', return_value='fake_api_key'):
        # Create a mock response with invalid format
        mock_response = MagicMock()
        mock_response.json.return_value = {'invalid': 'response'}
        mock_get.return_value = mock_response
        
        # Call the function
        results = search_web("test query")
        
        # Verify empty results are returned when web.results is missing
        assert results == []