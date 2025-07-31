import argparse
import json
import tabulate
from typing import Dict, Any, Iterator, List


def generate_data(res: Dict[str, Dict[str, Any]]) -> Iterator[List[Any]]:
    sorted_data = dict(sorted(res.items(), key=lambda item: item[1]['count'], reverse=True))
    for url, data in sorted_data.items():
        avg_time = round(data["response_time"] / data["count"], 3)
        yield [url, data["count"], avg_time]


def print_table_avg_response(res: Dict[str, Dict[str, Any]]) -> None:
    headers = ["handler", "total", "avg_response_time"]
    print(tabulate.tabulate(generate_data(res), headers=headers, tablefmt="grid"))


def parse_line(line: str, res: Dict[str, Dict[str, Any]], date: str = None) -> None:
    try:
        info = json.loads(line)
        current_url = res.setdefault(info["url"], {"count": 0, "response_time": 0})
        current_url["count"] += 1
        current_url["response_time"] += info["response_time"]
    except json.JSONDecodeError:
        print(f"Failed to parse line: {line}")
    except KeyError:
        print(f"Malformed log entry: {line}")


def processing_average(filenames: List[str], date: str = None) -> Dict[str, Dict[str, Any]]:
    res = dict()
    for filename in filenames:
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                for line in file:
                    parse_line(line, res)
        except IOError as e:
            print(f"Error reading file {filename}: {e}")
    return res


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate reports from server logs")
    parser.add_argument("--file", nargs='+', required=True, help="One or more log filenames to process")
    parser.add_argument("--report", required=True, choices=["average", "sum"], help="Type of report to generate.")
    parser.add_argument("--date", help="Optional date filter for reports")

    return  parser.parse_args()

def main():
    args = parse_args()

    if args.report == "average":
        res = processing_average(args.file, args.date)
        print_table_avg_response(res)
    elif args.report == "sum":
        print("Sum report functionality not yet implemented")


if __name__ == '__main__':
    main()
