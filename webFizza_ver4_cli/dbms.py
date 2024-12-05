import re
import json
import requests
from urllib.parse import urlparse, parse_qs, urlencode
import os
import glob

# SQL 오류 메시지 패턴
sql_errors = {
    "MySQL": (r"SQL syntax.*MySQL", r"Warning.*mysql_.*", r"MySQL Query fail.*", r"SQL syntax.*MariaDB server"),
    "PostgreSQL": (r"PostgreSQL.*ERROR", r"Warning.*\Wpg_.*", r"Warning.*PostgreSQL"),
    "Microsoft SQL Server": (r"OLE DB.* SQL Server", r"(\W|\A)SQL Server.*Driver", r"Warning.*odbc_.*", r"Warning.*mssql_", r"Msg \d+, Level \d+, State \d+", r"Unclosed quotation mark after the character string", r"Microsoft OLE DB Provider for ODBC Drivers"),
    "Microsoft Access": (r"Microsoft Access Driver", r"Access Database Engine", r"Microsoft JET Database Engine", r".*Syntax error.*query expression"),
    "Oracle": (r"\bORA-[0-9][0-9][0-9][0-9]", r"Oracle error", r"Warning.*oci_.*", "Microsoft OLE DB Provider for Oracle"),
    "IBM DB2": (r"CLI Driver.*DB2", r"DB2 SQL error"),
    "SQLite": (r"SQLite/JDBCDriver", r"System.Data.SQLite.SQLiteException"),
    "Informix": (r"Warning.*ibase_.*", r"com.informix.jdbc"),
    "Sybase": (r"Warning.*sybase.*", r"Sybase message")
}

# SQL 오류 체크 함수
def check_sql_errors(html):
    """SQL 오류 메시지가 있는지 확인하고, 발견된 경우 DBMS를 반환"""
    for db, errors in sql_errors.items():
        for error in errors:
            if re.search(error, html):
                return True, db
    return False, None

# 웹 페이지 HTML 가져오기 (GET 또는 POST 요청)
def get_html(url, params=None, method='GET'):
    """URL에 요청을 보내 HTML을 가져옴"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    try:
        if method == 'POST':
            response = requests.post(url, data=params, headers=headers, timeout=10)
        else:
            response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None

# SQL Injection 탐지 함수
def detect_sqli(input_fields):
    """SQL Injection 탐지 및 결과 업데이트"""
    payloads = ("';", '"')

    for field in input_fields:
        url = field.get("page_url")
        if not url:
            continue

        input_type = field.get("input_type")
        input_name = field.get("input_name")

        parsed_url = url.split("?")[0]  # URL에서 쿼리 부분 제거
        queries = parse_qs(urlparse(url).query)

        if input_type == "query parameter" and input_name:  # URL 파라미터일 경우
            for payload in payloads:
                # 쿼리 파라미터를 처리
                if input_name in queries:
                    # 파라미터 값 뒤에 페이로드 추가
                    queries[input_name] = [payload]
                    test_url = parsed_url + "?" + urlencode(queries, doseq=True)
                    print(f"Testing URL: {test_url}")
                    source = get_html(test_url)

                    if source:
                        # SQL 오류 메시지 탐지
                        vulnerable, db = check_sql_errors(source)
                        if vulnerable and db:
                            print(f"DBMS Detected: {db}")
                            print(f"SQLi Vulnerability Detected on: {test_url}")
                            field["attack_type"] = "sqli"
                            field["sqli_vendor"] = db
                            field["sqli_type"] = ""
                            break
                        else:
                            print(f"Tested {test_url}: No SQLi vulnerability detected, classified as XSS.")
                            field["attack_type"] = "XSS"
                            field["xss_type"] = ""
                    else:
                        print(f"Tested {test_url}: No response, classified as XSS.")
                        field["attack_type"] = "XSS"
                        field["xss_type"] = ""

        elif input_name:  # URL 파라미터가 아닌 경우 (폼 필드일 경우)
            for payload in payloads:
                # 폼 필드에 페이로드를 넣어서 POST 요청을 보냄
                print(f"Testing form field {input_name} with payload: {payload}")
                form_data = {input_name: payload}
                source = get_html(parsed_url, params=form_data, method='POST')

                if source:
                    # SQL 오류 메시지 탐지
                    vulnerable, db = check_sql_errors(source)
                    if vulnerable and db:
                        print(f"DBMS Detected: {db}")
                        print(f"SQLi Vulnerability Detected on form field {input_name} with payload: {payload}")
                        field["attack_type"] = "sqli"
                        field["sqli_vendor"] = db
                        field["sqli_type"] = ""
                        break
                    else:
                        print(f"Tested form field {input_name} with payload {payload}: No SQLi vulnerability detected, classified as XSS.")
                        field["attack_type"] = "XSS"
                        field["xss_type"] = ""
                else:
                    print(f"Tested form field {input_name} with payload {payload}: No response, classified as XSS.")
                    field["attack_type"] = "XSS"
                    field["xss_type"] = ""

    return input_fields

# input_fields.json 파일 로드
def load_input_fields(filename):
    """input_fields.json 파일을 로드"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# input_fields.json 파일 저장
def save_input_fields(data, filename):
    """input_fields.json 파일을 저장"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def find_latest_file_with_prefix(prefix):
    """주어진 prefix로 시작하는 가장 최근에 수정된 파일을 찾음"""
    files = glob.glob(f"{prefix}*")
    if not files:
        return None
    latest_file = max(files, key=os.path.getctime)  # 생성 시간을 기준으로 가장 최근 파일 선택
    return latest_file

if __name__ == "__main__":
    filename = find_latest_file_with_prefix('input_fields_')

    if filename:
        # input_fields.json 파일을 로드
        input_fields = load_input_fields(filename)

        # SQLi 탐지 수행
        updated_fields = detect_sqli(input_fields)

        # 결과 저장
        save_input_fields(updated_fields, filename)
        print(f"Updated {filename} with SQLi and XSS types.")
    else:
        print(f"No file found with prefix 'input_fields_'.")
