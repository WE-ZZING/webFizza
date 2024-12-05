import subprocess
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import random

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.processed_data_hash = None  # 이전에 처리한 데이터 해시를 저장

    def on_modified(self, event):
        if event.src_path == self.json_file_path:
            print(f"{self.json_file_path} has been modified.")
            self.process_file()

    def process_file(self):
        with open(self.json_file_path, 'r') as file:
            try:
                data = json.load(file)
                data_hash = hash(json.dumps(data, sort_keys=True))  # 새로운 데이터의 해시 생성

                # 이미 처리된 데이터는 건너뛰기
                if data_hash == self.processed_data_hash:
                    return

                # 처리하지 않은 새로운 데이터인 경우 추가로 처리
                self.processed_data_hash = data_hash
                print("Data read from JSON:", data)

                mode = data.get('mode')
                if mode == 'parsing':
                    url = data.get('url')
                    if url:
                        print(f"URL for attack: {url}")
                        try:
                            
                            attack_url(url)  # Perform URL attack
                            run_find_dbms_parse()  # Find DBMS
                            run_fuzz_engine()  # Run fuzz engine
                            run_seed()  # Generate payloads
                        finally:
                            run_selenium()  # Run validation
                            run_report_script()  # Generate the report
                            run_patch()  # Generate patches for URL
                            run_privacy()

                elif mode == 'llm':
                    file_path = data.get('file_path')
                    url = data.get('url')
                    if file_path and url:
                        print(f"File path for attack: {file_path}, URL: {url}")
                        try:
                            attack_file(file_path, url)  # Perform file attack
                            run_fuzz_engine()  # Run fuzz engine
                            run_seed()  # Generate payloads
                        finally:
                            run_selenium()  # Run validation
                            run_report_script()  # Generate the report
                            run_patch()  # Generate patches for URL
                            run_privacy()

                else:
                    print("Invalid mode provided.")

            except json.JSONDecodeError:
                print("Failed to parse JSON. Retrying...")

def attack_file(file_path, url):
    # Popen과 communicate()를 사용해 파일 경로와 URL을 자동으로 입력
    process = subprocess.Popen(['python3', 'file.py'], stdin=subprocess.PIPE, text=True)
    process.communicate(input=f"{file_path}\n{url}\n")

def attack_url(url):
    # Popen과 communicate()를 사용해 URL을 자동으로 입력
    process = subprocess.Popen(['python3', 'url.py'], stdin=subprocess.PIPE, text=True)
    process.communicate(input=f"{url}\n")

def run_find_dbms_parse():
    """Run dbms.py to find dbms.."""
    print("Finding dbms ...")
    subprocess.run(['python3', 'dbms.py'], check=True)

def run_seed():
    """Run seed.py to generate payloads."""
    print("Generating payloads using seed.py...")
    subprocess.run(['python3', 'seed.py'], check=True)

def run_fuzz_engine():
    """Run fuzz_engine.py."""
    status = {"status": "running", "session_id": random.randint(1000, 9999)}
    with open("/tmp/fuzz_status.json", "w") as status_file:
        json.dump(status, status_file)
    time.sleep(2)
    """Run fuzz_engine.py."""
    print("Running fuzz_engine.py...")
    subprocess.run(['python3', 'fuzz_engine.py'], check=True)


def run_selenium():
    """Run v_selenium.py."""
    
    print("Running validation with selenium...")
    subprocess.run(['python3', 'v_selenium.py'], check=True)
    print("Finish Validation")
    # Finish Validation 후 상태 파일 저장
    status = {"status": "validation_complete", "session_id": random.randint(1000, 9999)}
    with open("/tmp/validation_status.json", "w") as status_file:
        json.dump(status, status_file)


def run_report_script():
    """Run report.py to generate the Markdown report."""
    try:
        subprocess.run(['python3', 'report.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running report script: {e}")

def run_patch():
    """Run patch_file.py to generate patches based on crash data and code file."""
    try:
        subprocess.run(['python3', 'patch.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running patch script: {e}")
        
def run_privacy():
    """Run privacy.py to generate patches based on crash data and code file."""
    try:
        subprocess.run(['python3', 'privacy.py'], check=True)
        print("Finish to Privacy Reporting")
        status = {"status": "report_complete", "session_id": random.randint(1000, 9999)}
        with open("/tmp/report.json", "w") as status_file:
            json.dump(status, status_file)
    except subprocess.CalledProcessError as e:
        print(f"Error running patch script: {e}")


def main():
    print(" _    _        _     ______  _                  ")
    print("| |  | |      | |    |  ___|(_)                 ")
    print("| |  | |  ___ | |__  | |_    _  ____ ____  __ _ ")
    print("| |/\\| | / _ \\| '_ \\ |  _|  | ||_  /|_  / / _ |")
    print("\\  /\\  /|  __/| |_) || |    | | / /  / / | (_| |")
    print(" \\/  \\/  \\___||_.__/ \\_|    |_|/___|/___| \\__,_|")

    json_file_path = "/tmp/webfizza_input.json"
    event_handler = FileChangeHandler(json_file_path)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(json_file_path), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)  # 계속 실행 상태 유지
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()

