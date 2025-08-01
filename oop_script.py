import argparse
import json
import sys

import tabulate
from typing import Dict, Any, Iterator, List
from abc import abstractmethod, ABC
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LogEntry:
    url: str
    response_time: float
    timestamp: str
    status: int
    method: str


class LogParseError(Exception):
    pass


class FileReadError(Exception):
    pass


class LogParser:
    @staticmethod
    def parse_line(line: str) -> LogEntry:
        try:
            info = json.loads(line)
            return LogEntry(
                info["url"],
                info["response_time"],
                info.get("@timestamp", ""),
                info.get("status", 200),
                info.get("method", "GET")
            )
        except json.JSONDecodeError as e:
            raise LogParseError(f"Invalid JSON: {e}")
        except KeyError as e:
            raise LogParseError(f"Missing reqired field: {e}")


class FileReader:
    def __init__(self, parser: LogParser):
        self.parser = parser

    def read_files(self, filenames: List[str]) -> Iterator[LogEntry]:
        for filename in filenames:
            try:
                file_path = Path(filename)
                if not file_path.exists():
                    raise FileReadError(f"File {filename} not exits")

                with open(file_path, "r", encoding="utf-8") as file:
                    for line_num, line in enumerate(file, 1):
                        if not line.strip(): continue

                        try:
                            log_entry = self.parser.parse_line(line)
                            yield log_entry
                        except LogParseError as e:
                            print(f"Warning: {filename} line: {line_num}: {e}")

            except IOError as e:
                raise FileReadError(f"File {filename} reading error : {e}")


class ReportGenerator(ABC):

    @abstractmethod
    def generate(self, entries: Iterator[LogEntry]) -> str:
        pass


class ReportFactory:

    _generators: Dict[str, type] = {}

    @classmethod
    def register(cls, report_type: str):
        def decorator(generator_class):
            if not issubclass(generator_class, ReportGenerator):
                raise ValueError(f"{generator_class} must inherit from ReportGenerator")
            cls._generators[report_type] = generator_class
            return generator_class

        return decorator

    @classmethod
    def create_generator(cls, report_type: str) -> ReportGenerator:
        if report_type not in cls._generators:
            available = ", ".join(cls._generators.keys()) or "none"
            raise ValueError(f"Unknown report type: {report_type}. Available: {available}")
        return cls._generators[report_type]()



@ReportFactory.register("average")
class AverageResponseTimeReport(ReportGenerator):
    def generate(self, entries: Iterator[LogEntry]) -> str:
        report_data = {}
        for entry in entries:
            if entry.url not in report_data:
                report_data[entry.url] = {"count": 0, "total_time": 0.0}
            report_data[entry.url]["count"] += 1
            report_data[entry.url]["total_time"] += entry.response_time

        if not report_data: return "No data for generate report"

        table_data = self._make_table_data(report_data)
        headers = ["handler", "total", "avg_response_time"]
        return tabulate.tabulate(table_data, headers=headers, tablefmt="grid")

    def _make_table_data(self, report_data: Dict[str, Dict[str, Any]]) -> Iterator[List[Any]]:
        sorted_data = dict(sorted(report_data.items(), key=lambda item: item[1]['count'], reverse=True))
        for url, data in sorted_data.items():
            avg_time = round(data["total_time"] / data["count"], 3)
            yield [url, data["count"], avg_time]


class ArgumentParser:

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Generate reports from server logs"
        )

        parser.add_argument(
            "--file",
            nargs='+',
            required=True,
            help="One or more log filenames to process"
        )

        parser.add_argument(
            "--report",
            required=True,
            help="Type of report to generate (e.g., 'average')"
        )

        parser.add_argument(
            "--date",
            help="Optional date filter for reports (not implemented yet)"
        )

        return parser.parse_args()


def main():
    try:

        args = ArgumentParser.parse_arguments()
        log_parser = LogParser()
        file_reader = FileReader(log_parser)
        data = file_reader.read_files(args.file)
        report_generator = ReportFactory.create_generator(args.report)
        report = report_generator.generate(data)

        print(report)

    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
