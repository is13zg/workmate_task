import pytest
from unittest.mock import patch, mock_open
import json
from io import StringIO
from oop_script import LogParser, LogParseError, FileReader, FileReadError, LogEntry, ArgumentParser, \
    AverageResponseTimeReport, ReportGenerator, ReportFactory, main


@pytest.fixture
def valid_line():
    return json.dumps({
        "url": "/api/specializations/...",
        "response_time": 0.016,
        "@timestamp": "2025-06-22T13:57:34+00:00",
        "status": 200,
        "method": "GET"
    })


# Тесты  LogParser
def test_log_parser_valid_line(valid_line):
    parser = LogParser()

    entry = parser.parse_line(valid_line)
    assert entry.url == "/api/specializations/..."
    assert entry.response_time == 0.016
    assert entry.timestamp == "2025-06-22T13:57:34+00:00"
    assert entry.status == 200
    assert entry.method == "GET"


def test_log_parser_missing_required_field():
    parser = LogParser()
    invalid_line = json.dumps({
        "url": "/api/specializations/...",
        "@timestamp": "2025-06-22T13:57:34+00:00",
        "status": 200,
        "method": "GET"
    })

    with pytest.raises(LogParseError):
        parser.parse_line(invalid_line)


def test_log_parser_invalid_json():
    parser = LogParser()

    with pytest.raises(LogParseError):
        parser.parse_line("no json str")


# Тесты  FileReader
def test_file_reader_nonexistent_file():
    reader = FileReader(LogParser())
    with pytest.raises(FileReadError):
        list(reader.read_files(["nonexistent.log"]))


def test_file_reader_valid_file(valid_line):
    mock_data = valid_line

    with (patch("builtins.open", mock_open(read_data=mock_data)),
          patch("pathlib.Path.exists", return_value=True)):
        reader = FileReader(LogParser())
        entries = list(reader.read_files(["filename"]))
        assert len(entries) == 1
        assert entries[0].url == "/api/specializations/..."


def test_file_reader_invalid_line():
    mock_data = "no json\n"

    with (patch("builtins.open", mock_open(read_data=mock_data)),
          patch("pathlib.Path.exists", return_value=True)):
        reader = FileReader(LogParser())
        entries = list(reader.read_files(["filename"]))
        assert len(entries) == 0


# Тесты  AverageResponseTimeReport
def test_average_report_generator():
    entries = [
        LogEntry("/test1", 0.1, "2023-01-01", 200, "GET"),
        LogEntry("/test1", 0.3, "2023-01-01", 200, "GET"),
        LogEntry("/test2", 0.5, "2023-01-01", 200, "GET"),
    ]

    generator = AverageResponseTimeReport()
    report = generator.generate(iter(entries))

    assert "/test1" in report
    assert "0.2" in report  # среднее для test1
    assert "/test2" in report
    assert "0.5" in report  # среднее для test2


def test_average_report_empty_data():
    generator = AverageResponseTimeReport()
    report = generator.generate(iter([]))
    assert "No data" in report


# Тесты  ReportFactory
def test_report_factory_registration():
    class TestReport(ReportGenerator):
        def generate(self, entries): return "test"

    ReportFactory.register("test")(TestReport)
    assert "test" in ReportFactory._generators
    assert isinstance(ReportFactory.create_generator("test"), TestReport)


def test_report_factory_unknown_type():
    with pytest.raises(ValueError):
        ReportFactory.create_generator("unknown")


# Тесты ArgumentParser
def test_argument_parser():
    parser = ArgumentParser()

    with patch("sys.argv", ["script.py", "--file", "file1.log", "file2.log", "--report", "average"]):
        args = parser.parse_arguments()
        assert args.file == ["file1.log", "file2.log"]
        assert args.report == "average"
        assert args.date is None


def test_argument_parser_missing_required():
    parser = ArgumentParser()
    with patch("sys.argv", ["script.py"]), pytest.raises(SystemExit):
        parser.parse_arguments()


# Тест интеграции основных компонентов
def test_main_integration(valid_line):
    mock_data = valid_line

    with patch("builtins.open", mock_open(read_data=mock_data)), \
            patch("pathlib.Path.exists", return_value=True), \
            patch("sys.argv", ["script.py", "--file", "dummy.log", "--report", "average"]), \
            patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        main()
        output = mock_stdout.getvalue()
        assert "/api/specializations/.." in output
        assert "0.016" in output


def test_main_error_handling():
    with patch("sys.argv", ["script.py", "--file", "nonexistent.log", "--report", "average"]), \
            patch("pathlib.Path.exists", return_value=True), \
            patch("sys.stderr", new_callable=StringIO) as mock_stderr, \
            pytest.raises(SystemExit):
        main()
        assert "Error" in mock_stderr.getvalue()
