# fuzz_engine.py -> 인터럽트
import os
import subprocess
import requests
import json
from datetime import datetime
from tqdm import tqdm
import time
from seed3 import *  # Import necessary function from seed.py
from colorama import Fore, Style, init
import websocket
import websockets 
import asyncio
import threading
import sys
import signal

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
def save_crash_data(file_path, page_url, payload, response, form_method, input_name, html, attack_type, xss_type=None, sqli_vendor=None, sqli_type=None, severity=None):
    crash_data = {
        "Page Url": page_url,
        "Payload": payload,
        "Form Method": form_method,
        "Parameter": input_name,
        "Status Code": response.status_code,
        "HTML Tag": html,
        "HTML Response": response.text,
        "Attack Type": attack_type,
        "severity": "",
    }

    # XSS일 경우 xss_type 추가
    if attack_type == "XSS" and xss_type:
        crash_data["XSS Type"] = xss_type

     # SQLi일 경우 dbms, sqli_type 추가 및 severity:Medium 설정
    if attack_type == "sqli":
        if sqli_vendor and sqli_type:
            crash_data["DBMS"] = sqli_vendor
            crash_data["SQLi Type"] = sqli_type
        crash_data["severity"] = "Medium"

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
def save_retry_data_xss_sqli(file_path_xss, file_path_sqli, page_url, form_action, payload, form_method, input_name, input_type, html, attack_type, xss_type=None, sqli_vendor=None, sqli_type=None):
    retry_data = {
        "page_url": page_url,
        "form_action": form_action,
        "payload": payload,
        "form_method": form_method,
        "parameter": input_name,
        "input_type": input_type,
        "html": html,
        "attack_type": attack_type
        
    }

    if attack_type == "XSS":
        retry_data["xss_type"] = xss_type

    if attack_type == "sqli":
        retry_data["sqli_vendor"] = sqli_vendor
        retry_data["sqli_type"] = sqli_type

    if attack_type == "XSS":
        file_path = file_path_xss
    elif attack_type == "sqli":
        file_path = file_path_sqli
    else:
        return  # XSS 또는 SQLi가 아닌 경우 저장하지 않음

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
def log(ws, t, message, verbose):
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

    # WebSocket으로 로그 전송
    ws.send(json.dumps({"message": message}))

# Seed script에서 refined payloads 확인
def run_seed_script_xss_sqli(retry_file_xss, retry_file_sqli, crash_file):
    try:
        # 각각의 XSS와 SQLi에 대해 실행
        command_xss = f'python3 seed3.py {retry_file_xss} {crash_file}'
        command_sqli = f'python3 seed3.py {retry_file_sqli} {crash_file}'

        # 명령 실행 및 출력 캡처
        result_xss = subprocess.run(command_xss, shell=True, capture_output=True, text=True)
        result_sqli = subprocess.run(command_sqli, shell=True, capture_output=True, text=True)

        # 로그 출력
        print(f"XSS command: {command_xss}")
        print(f"XSS stdout: {result_xss.stdout}")
        print(f"SQLi command: {command_sqli}")
        print(f"SQLi stdout: {result_sqli.stdout}")

        # 실행 오류가 발생한 경우 stderr 로그 확인
        if result_xss.returncode != 0:
            print(f"Error in XSS seed script: {result_xss.stderr}")
        if result_sqli.returncode != 0:
            print(f"Error in SQLi seed script: {result_sqli.stderr}")

        # 페이로드 파싱 및 필터링
        refined_payloads_xss = [
            payload.strip() for payload in result_xss.stdout.splitlines() if payload.strip()
        ]
        refined_payloads_sqli = [
            payload.strip() for payload in result_sqli.stdout.splitlines() if payload.strip()
        ]

        # 중복 제거
        refined_payloads_xss = list(set(refined_payloads_xss))
        refined_payloads_sqli = list(set(refined_payloads_sqli))

        return refined_payloads_xss, refined_payloads_sqli

    except Exception as e:
        print(f"Error running seed scripts: {e}")
        return [], []

def generate_initial_payloads(input_fields):
    """기본 XSS 및 SQLi 페이로드를 생성합니다."""
    all_payloads_xss = []
    all_payloads_sqli = []

    for field in input_fields:
        if field["attack_type"] == "XSS":
            payloads = generate_basic_payloads(field["xss_type"])
            for payload in payloads:
                all_payloads_xss.append((field, payload))
        elif field["attack_type"] == "sqli":
            payloads = generate_basic_sqli_payloads(field["sqli_type"])
            for payload in payloads:
                all_payloads_sqli.append((field, payload))

    return all_payloads_xss, all_payloads_sqli

# WebSocket을 인자로 추가
def process_payloads(ws, attack_type, all_payloads, retry_file, crash_detected_fields, crash_data_file, verbose, cycle):
    """공격 유형에 따라 페이로드를 처리합니다."""
    total_requests = len(all_payloads)

    if total_requests > 0:
        log(ws, 's', f'Starting {attack_type} fuzzing cycle {cycle}', verbose)
        with tqdm(total=total_requests, desc=f"{attack_type} Fuzzing Cycle {cycle}", unit="req", leave=True) as pbar:
            retry_payloads = []
            for field, payload in all_payloads:
                response = send_request(field["page_url"], field["form_action"], field["input_name"], payload, field["form_method"], field["input_type"])
                if response:
                    log(ws, 'i', f"[{response.status_code}] [param: {field['input_name']}][payload: {payload}]", verbose)
                    if analyze_response(response, payload):
                        log(ws, 'h', f"Reflected payload: {payload}", verbose)
                        save_crash_data(crash_data_file, field["page_url"], payload, response, field["form_method"], field["input_name"], field["html"], field["attack_type"], field.get("xss_type") if attack_type == "XSS" else None)
                    else:
                        retry_payloads.append((field, payload))
                pbar.update(1)

        # Retry 데이터를 저장
        if retry_payloads:
            with open(retry_file, 'w') as f:
                json.dump([
                    {
                        "page_url": field["page_url"],
                        "form_action": field["form_action"],
                        "form_method": field["form_method"],
                        "input_name": field["input_name"],
                        "input_type": field["input_type"],
                        "html": field["html"],
                        "attack_type": field["attack_type"],
                        **({"xss_type": field.get("xss_type")} if field["attack_type"] == "XSS" else {}),
                        **(
                            {
                                "sqli_vendor": field.get("sqli_vendor"),
                                "sqli_type": field.get("sqli_type")
                            } if field["attack_type"] == "sqli" else {}
                        ),
                        "payload": payload
                    } 
                    for field, payload in retry_payloads
                ], f, indent=4)

def create_tuples_from_retry_data(retry_data, refined_payloads):
    result = []
    if isinstance(retry_data, list):
        for item in retry_data:
            if isinstance(item, dict):  
                if 'attack_type' in item and item['attack_type'] == 'XSS':
                    for payload in refined_payloads:
                        fields = {k: v for k, v in item.items() if k != 'payload'} 
                        result.append((fields, payload))  
                elif 'attack_type' in item and item['attack_type'] == 'sqli':
                    for payload in refined_payloads:
                        fields = {k: v for k, v in item.items() if k != 'payload'} 
                        result.append((fields, payload)) 
    return result

def keep_alive(ws):
    while True:
        try:
            ws.send("ping")  # WebSocket 서버로 Ping 메시지 전송
            time.sleep(10)  # 10초마다 Ping 메시지 전송
        except Exception as e:
            print("WebSocket keep-alive error:", e)
            break

# def send_log_to_websocket(message):
#     try:
#         ws = websocket.WebSocket()
#         ws.connect("ws://127.0.0.1:8000/ws/logs/")  # WebSocket 연결
#         ws.send(json.dumps({"message": message}))  # 메시지 전송
#         ws.close()  # 연결 닫기
#     except Exception as e:
#         print("WebSocket connection error:", e)

# daphne.log 파일을 실시간으로 읽으면서 'ctrl+c'를 찾는 함수
def monitor_log_file(log_file_path):
    with open(log_file_path, "r") as file:
        file.seek(0, 2) 
        while True:
            line = file.readline()
            if line:
                #print(f"Log: {line.strip()}") 
                if 'ctrl+c' in line:
                    os.kill(os.getpid(), signal.SIGINT)
            else:
                time.sleep(1)


# WebSocket 연결을 한 번만 열고 유지하기 위한 메인 함수
def main():
    ws = websocket.WebSocket()
    ws.connect("ws://127.0.0.1:8000/ws/logs/")

    keep_alive_thread = threading.Thread(target=keep_alive, args=(ws,))
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    
    log_file_path = "/home/user/webFizza_ver12/webFizza_ver8/webfizza_ver5_progressGraph/daphne.log"
    
    monitor_thread = threading.Thread(target=monitor_log_file, args=(log_file_path,))
    monitor_thread.daemon = True
    monitor_thread.start()
   
    try:
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
        retry_data_file_template_xss = "xss_retry_cycle{}.json"
        retry_data_file_template_sqli = "sqli_retry_cycle{}.json"

        verbose = 2
        cycle = 1
        continue_testing = True
        crash_detected_fields_xss = set()
        crash_detected_fields_sqli = set()
        

        while continue_testing:
                
            retry_data_file_xss = retry_data_file_template_xss.format(cycle)
            retry_data_file_sqli = retry_data_file_template_sqli.format(cycle)

            # 첫 번째 사이클: 기본 페이로드 사용
            if cycle == 1:
                log(ws, 's', f'Starting cycle {cycle}', verbose)
                all_payloads_xss, all_payloads_sqli = generate_initial_payloads(input_fields)
                total_requests_xss = len(all_payloads_xss)
                total_requests_sqli = len(all_payloads_sqli)
                # XSS Fuzzing 수행
                process_payloads(ws, "XSS", all_payloads_xss, retry_data_file_xss, crash_detected_fields_xss, crash_data_file, verbose, cycle)

                # SQLi Fuzzing 수행
                process_payloads(ws, "sqli", all_payloads_sqli, retry_data_file_sqli, crash_detected_fields_sqli, crash_data_file, verbose, cycle)

                cycle += 1
                continue_testing = any(
                    field["input_name"] not in crash_detected_fields_xss for field in input_fields if field["attack_type"] == "XSS"
                ) or any(
                    field["input_name"] not in crash_detected_fields_sqli for field in input_fields if field["attack_type"] == "sqli"
                )

                if not continue_testing:
                    log(ws, 's', "No more fields to test. Stopping.", verbose)

            # 두 번째 사이클 이후: refined_payloads 사용
            else:
                current_retry_xss = retry_data_file_template_xss.format(cycle-1)
                current_retry_sqli = retry_data_file_template_sqli.format(cycle-1)
                
                if os.path.exists(current_retry_xss) or os.path.exists(current_retry_sqli):
                    log(ws, 's', f'Loading payloads from {current_retry_xss} and {current_retry_sqli}', verbose)

                    retry_xss = load_retry_data(current_retry_xss) if os.path.exists(current_retry_xss) else []
                    retry_sqli = load_retry_data(current_retry_sqli) if os.path.exists(current_retry_sqli) else []

                    refined_payloads_xss, refined_payloads_sqli = run_seed_script_xss_sqli(current_retry_xss, current_retry_sqli, crash_data_file)
                    
                    total_requests_xss = len(refined_payloads_xss)
                    total_requests_sqli = len(refined_payloads_sqli)

                    # tuple 
                    retry_xss = create_tuples_from_retry_data(retry_xss, refined_payloads_xss)
                    retry_sqli = create_tuples_from_retry_data(retry_sqli, refined_payloads_sqli)
                    

                    # XSS Fuzzing 수행
                    process_payloads(ws, "XSS", retry_xss, retry_data_file_xss, crash_detected_fields_xss, crash_data_file, verbose, cycle)

                    # SQLi Fuzzing 수행
                    process_payloads(ws, "sqli", retry_sqli, retry_data_file_sqli, crash_detected_fields_sqli, crash_data_file, verbose, cycle)

                    cycle += 1  # 사이클 증가
                    
                    # 남은 테스트할 필드가 있는지 확인
                    continue_testing = any(
                        field["input_name"] not in crash_detected_fields_xss for field in input_fields if field["attack_type"] == "XSS"
                    ) or any(
                        field["input_name"] not in crash_detected_fields_sqli for field in input_fields if field["attack_type"] == "sqli"
                    )

                    if not continue_testing:
                        log(ws, 's', "No more fields to test. Stopping.", verbose)

                    else:
                        if not refined_payloads_sqli and refined_payloads_xss:
                            log(ws, 's', f"No refined payloads found. Stopping test.", verbose)
                            break

                    all_payloads_xss = [(field, payload) for field in input_fields if field["attack_type"] == "XSS" and field["input_name"] not in crash_detected_fields_xss for payload in refined_payloads_xss]
                    all_payloads_sqli = [(field, payload) for field in input_fields if field["attack_type"] == "sqli" and field["input_name"] not in crash_detected_fields_sqli for payload in refined_payloads_sqli]

    finally:
        ws.close()  # WebSocket 연결 종료

if __name__ == '__main__':
    main()
