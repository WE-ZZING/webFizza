import argparse

def get_args():
    parser = argparse.ArgumentParser(description="Enter how to read contents")
    parser.add_argument('--f', action='store_true', help="Read contents with loading file")
    parser.add_argument('--url', action='store_true', help="Read contents with loading URL")
    parser.add_argument('--u', action='store_true', help="Run url.py")
    return parser.parse_args()

# 예시: 파일과 URL을 읽어오는 함수들
def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def read_url(url):
    import requests
    response = requests.get(url)
    return response.text

