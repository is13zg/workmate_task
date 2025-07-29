import argparse
import json

import tabulate


def generate_data(res: dict):
    sorted_data = dict(sorted(res.items(), key=lambda item: item[1]['count'], reverse=True))
    print(sorted_data)
    for url, data in sorted_data.items():
        yield [url, data["count"], data["response_time"]]


def print_table_avg_response(res: dict) -> None:
    headers = ["handler", "total", "avg_response_time"]
    print(tabulate.tabulate(generate_data(res), headers=headers, tablefmt="grid"))


def parse_line(line: str, res: dict) -> None:
    info = json.loads(line)
    current_url = res.get(info["url"], dict())
    current_url["count"] = current_url.get("count", 0) + 1
    current_url["response_time"] = current_url.get("response_time", 0) + info["response_time"]
    res[info["url"]] = current_url

def processing_average(filename: str, date: str, res: dict) -> None:
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            parse_line(line, res)


def main():
    res = dict()
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Filename to processing")
    parser.add_argument("--report", help="Name of nesacary report")
    parser.add_argument("--date", help="Date of report")

    args = parser.parse_args()

    #print(args)

    processing_average("example1.log", "date_must_be_here", res)

    print_table_avg_response(res)


if __name__ == '__main__':
    main()
