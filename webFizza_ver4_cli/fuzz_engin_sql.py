
import os
import subprocess
import requests
import json
from datetime import datetime
from tqdm import tqdm
import time
from seed import *  # Import necessary function from seed.py
from colorama import Fore, Style, init

# Colorama 초기화
init(autoreset=True)

# 입력 필드 정보를 불러오는 함수
def load_input_fields(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

# retry_cycle 데이터를 불러오는 함수
def load_retry_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

# 페이로드를 사용하여 요청을 보내는 함수
def send_request(page_url, form_action, input_name, payload, form_method, input_type):
    try:
        if input_type == "query parameter":
            # URL 파라미터인 경우, GET 요청에 쿼리 파라미터로 전달
            response = requests.get(page_url, params={input_name: payload})
        else:
            # URL 파라미터가 아닌 경우, POST 요청으로 폼 데이터 전송
            if form_method.lower() == 'post':
                response = requests.post(form_action, data={input_name: payload})
            else:
                response = requests.get(page_url, params={input_name: payload})

        # 요청이 성공하면 Response 객체를 반환
        if isinstance(response, requests.Response):
            return response
        else:
            return None  # 만약 Response 객체가 아니면 None 반환

    except requests.exceptions.RequestException as e:
        print(f"Error occurred while sending request: {e}")
        return None  # 요청 실패 시 None을 반환

# 응답을 분석하는 함수
def analyze_response(response, payload):
    if response is None:
        return False
    return payload in response.text

# 크래시를 감지하는 함수
def detect_crash(response):
    if response is None:
        return False
    return '<script>' in response.text or response.status_code >= 500

# 크래시 데이터를 JSON 파일에 저장하는 함수
def save_crash_data(file_path, page_url, payload, response, form_method, input_name, html, attack_type, xss_type=None, sql_vendor=None, sqli_type=None):
    crash_data = {
        "Page Url": page_url,
        "Payload": payload,
        "Form Method": form_method,
        "Parameter": input_name,
        "Status Code": response.status_code,
        "HTML Tag": html,
        "HTML Response": response.text,
        "Attack Type": attack_type
    }

    # XSS일 경우 xss_type 추가
    if attack_type == "XSS" :
        crash_data["XSS Type"] = xss_type

    # SQLi일 경우 dbms, sqli_type 추가
    if attack_type == "sqli" :
        crash_data["DBMS"] = sql_vendor
        crash_data["SQLi Type"] = sqli_type

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = []

    if crash_data not in data:
        data.append(crash_data)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# 요청 실패 또는 크래시가 발생하지 않은 페이로드를 JSON 파일에 저장하는 함수
def save_retry_data(file_path, page_url, form_action, payload, form_method, input_name, input_type, html):
    retry_data = {
        "Page Url": page_url,
        "Form Action": form_action,
        "Payload": payload,
        "Form Method": form_method,
        "Parameter": input_name,
        "Input Type": input_type,
        "HTML Tag": html
    }

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = []
    data.append(retry_data)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# 가장 최근에 생성된 특정 접두어로 시작하는 파일 찾기
def find_latest_file_with_prefix(prefix):
    input_files = [f for f in os.listdir('.') if f.startswith(prefix) and f.endswith('.json')]
    if not input_files:
        return None
    return max(input_files, key=os.path.getctime)

# 로그 출력 함수
def log(t, message, verbose):
    time_str = datetime.now().strftime('%H:%M:%S')
    if verbose == 1:
        if t == 's':
            tqdm.write(f'[*] {message}')
    elif verbose > 1:
        if t == 'd':
            tqdm.write(f'[-] [{time_str}] {message}')
        elif t == 's':
            tqdm.write(f'[*] {message}')
        elif t == 'i':
            tqdm.write(Fore.GREEN + f'[I] [{time_str}] {message}' + Style.RESET_ALL)
        elif t == 'v':
            tqdm.write(Fore.BLUE + f'[H] [{time_str}] {message}' + Style.RESET_ALL)
        elif t == 'h':
            tqdm.write(Fore.RED + f'[V] [{time_str}] {message}' + Style.RESET_ALL)

# Seed script를 실행하여 refined_payloads를 생성하는 함수
def run_seed_script(retry_file, crash_file):
    command = f'python3 seed.py --retry_file {retry_file} --crash_file {crash_file}'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    refined_payloads = result.stdout.splitlines()
    refined_payloads = [payload.strip().replace('Generated payload: ', '') for payload in refined_payloads if payload.strip()]
    refined_payloads = list(set(refined_payloads))  # 중복 제거
    return refined_payloads

# 메인 함수
def main():
    # crash_data.json 초기화
    crash_data_file = "crash_data.json"
    with open(crash_data_file, "w") as f:
        json.dump([], f, indent=4)

    # 가장 최근의 input_fields 파일 찾기
    input_fields_file = find_latest_file_with_prefix('input_fields_')
    if not input_fields_file:
        print("No input fields file found.")
        return

    input_fields = load_input_fields(input_fields_file)
    retry_data_file_template = "retry_cycle{}.json"

    verbose = 2

    cycle = 1
    continue_testing = True
    crash_detected_fields = set()
    refined_payloads = []

    while continue_testing:
        retry_data_file = retry_data_file_template.format(cycle)

        if os.path.exists(retry_data_file):
            # retry_cycle 파일이 존재하면 이를 기반으로 작업
            log('s', f'Loading payloads from {retry_data_file}', verbose)
            refined_payloads = load_retry_data(retry_data_file)
        else:
            log('s', f'Starting cycle {cycle}', verbose)

            # 첫 번째 사이클에서는 기본 페이로드 사용
            if cycle == 1:
                all_payloads = []
                for field in input_fields:
                    # XSS 또는 SQLi 페이로드 생성
                    payloads = generate_basic_payloads(field["xss_type"]) if field["attack_type"] == "XSS" else generate_basic_sqli_payloads(field["sqli_type"])
                    for payload in payloads:
                        all_payloads.append((field, payload))
            else:
                # 두 번째 사이클 이후에는 refined_payloads 사용
                if not refined_payloads:
                    log('s', f"No refined payloads generated. Stopping test.", verbose)
                    break
                all_payloads = [(field, payload) for field in input_fields if field["input_name"] not in crash_detected_fields for payload in refined_payloads]

            total_requests = len(all_payloads)

            with tqdm(total=total_requests, desc=f"Fuzzing Cycle {cycle}", unit="req", leave=True) as pbar:
                retry_payloads = []  # 크래시가 발생하지 않은 페이로드 저장용
                for field, payload in all_payloads:
                    # Input type에 따라 요청을 보냄
                    response = send_request(field["page_url"], field["form_action"], field["input_name"], payload, field["form_method"], field["input_type"])

                    if response:
                        # response가 None이 아닌 경우에만 status_code에 접근
                        status_code = response.status_code if hasattr(response, 'status_code') else 'No Response'
                        message = f"[param: {field['input_name']}][payload: {payload}]"
                        log('i', f"[{status_code}] {message}", verbose)

                        if analyze_response(response, payload):
                            log('h', f"Reflected payload: {payload}", verbose)
                            save_crash_data(crash_data_file, field["page_url"], payload, response, field["form_method"], field["input_name"], field["html"],
                                            field["attack_type"], field.get("xss_type"), field.get("sql_vendor"), field.get("sqli_type"))
                        else:
                            # 크래시가 발생하지 않은 페이로드를 retry_payloads에 추가
                            retry_payloads.append((field, payload))
                    else:
                        log('d', f"Failed to get response for {field['input_name']} with payload: {payload}", verbose)
                        save_retry_data(retry_data_file, field["page_url"], field["form_action"], payload, field["form_method"], field["input_name"], field.get("input_type", ""), field["html"])

                    if response and detect_crash(response):
                        save_crash_data(crash_data_file, field["page_url"], payload, response, field["form_method"], field["input_name"], field["html"],
                                        field["attack_type"], field.get("xss_type"), field.get("sql_vendor"), field.get("sqli_type"))
                        log('v', f"[{status_code}] Crash detected with payload: {payload} on field: {field['input_name']}", verbose)
                        crash_detected_fields.add(field["input_name"])

                    pbar.update(1)
                    time.sleep(0.1)

            # 크래시가 발생하지 않은 페이로드를 retry_cycle 파일에 저장
            if retry_payloads:
                retry_data_to_save = [
                    {
                        "page_url": field["page_url"],
                        "form_action": field["form_action"],
                        "form_method": field["form_method"],
                        "input_name": field["input_name"],
                        "input_type": field["input_type"],
                        "html": field["html"],
                        "attack_type": field["attack_type"],
                        "xss_type": field.get("xss_type"),
                        "sql_vendor": field.get("sql_vendor"),
                        "sqli_type": field.get("sqli_type"),
                        "payload": payload
                    } for field, payload in retry_payloads
                ]
                with open(retry_data_file, 'w') as f:
                    json.dump(retry_data_to_save, f, indent=4)

            log('s', f'Cycle {cycle} complete.', verbose)

        # 다음 사이클을 위해 seed.py를 실행하여 refined_payloads 생성
        refined_payloads = run_seed_script(retry_data_file, crash_data_file)

        # retry_cycle에 저장된 페이로드로 2사이클 이후부터 실행
        cycle += 1

        # Check if there are fields left to test
        continue_testing = any(field["input_name"] not in crash_detected_fields for field in input_fields)

if __name__ == '__main__':
    main()