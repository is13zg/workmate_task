import pytest
import json
import tempfile
from io import StringIO
from typing import Dict, Any
from unittest.mock import patch, mock_open

from script import (  # Замените `your_module` на имя вашего модуля
    generate_data,
    print_table_avg_response,
    parse_line,
    processing_average,
    main,
)

def test_generate_data():
    test_data = {
        "url1": {"count": 5, "response_time": 25},
        "url2": {"count": 10, "response_time": 30},
    }
    result = list(generate_data(test_data))
    assert len(result) == 2
    assert result[0] == ["url2", 10, 3.0]
    assert result[1] == ["url1", 5, 5.0]

def test_parse_line_invalid_json(capsys):
    res = {}
    line = "invalid_json"
    parse_line(line, res)
    captured = capsys.readouterr()
    assert "Failed to parse line" in captured.out
    assert res == {}