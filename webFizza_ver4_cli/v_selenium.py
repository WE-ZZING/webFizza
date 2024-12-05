#v_selenium.py
import os
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import json
from colorama import Fore, Style, init
import logging

# Colorama 초기화
init(autoreset=True)

# 현재 디렉터리 경로
current_directory = os.getcwd()

# Firefox Beta 다운로드 URL
firefox_beta_url = "https://download-installer.cdn.mozilla.net/pub/firefox/releases/130.0b9/linux-x86_64/en-US/firefox-130.0b9.tar.bz2"
firefox_beta_dir = os.path.join(current_directory, "firefox_beta")

# Firefox Beta가 이미 다운로드되지 않은 경우 다운로드
if not os.path.exists(firefox_beta_dir):
    os.makedirs(firefox_beta_dir)
    
    # Firefox Beta 다운로드
    subprocess.run([
        "wget", "-O", os.path.join(current_directory, "firefox_beta.tar.bz2"), firefox_beta_url
    ], check=True)
    
    # 다운로드된 파일 압축 해제
    subprocess.run([
        "tar", "-xjf", os.path.join(current_directory, "firefox_beta.tar.bz2"), "-C", firefox_beta_dir
    ], check=True)

# JSON 파일 불러오기
with open('crash_data.json', 'r') as file:
    crash_data = json.load(file)

# 헤드리스 모드로 실행 (실제 브라우저 창이 뜨지 않음)
options = Options()
#options.add_argument('--no-sandbox')
#options.add_argument('--disable-dev-shm-usage')
#options.headless = True

# Firefox Beta 실행 파일 경로 설정
options.binary_location = os.path.join(firefox_beta_dir, "firefox", "firefox")

# Geckodriver 서비스 설정
service = Service(executable_path=os.path.join(current_directory, "geckodriver"))  # 현재 디렉터리에 있는 Geckodriver 지정

# Firefox 드라이버 생성
driver = webdriver.Firefox(service=service, options=options)

# 오탐지를 제거하기 위한 리스트 생성
entries_to_remove = []

# 각 엔트리를 순회하며 "Attack Type"이 "XSS"인 경우만 처리
for entry in crash_data:
    if entry.get('Attack Type') != 'XSS':
        continue  # "Attack Type"이 "XSS"가 아닌 경우 건너뜀

    try:
        page_url = entry['Page Url']  # URL 불러오기
        payload = entry['Payload']
        form_method = entry['Form Method']
        parameter = entry['Parameter']
        xss_type = entry.get('XSS Type', None)

        # 검색 페이지 로드
        driver.get(page_url)

        # Form element 찾기 및 처리
        if form_method.lower() == "post":
            try:
                form = driver.find_element(By.NAME, parameter)  # 이름으로 form 찾기
                form.clear()  # 기존 값 삭제
                form.send_keys(payload)  # form에 payload 입력
                form.submit()  # 폼 제출

                # 지연 시간 추가
                time.sleep(3)  # 알림창이 뜰 시간을 기다림

                # xss_type에 따라 처리
                if xss_type == "Reflected XSS":
                    # 제출 직후 alert가 발생하는지 확인
                    try:
                        alert = driver.switch_to.alert  # 알림창 전환
                        print(Fore.GREEN + "셀레니움 테스트 성공, 검증 완료 - Reflected XSS" + Style.RESET_ALL +
                              f"\n{page_url} | {parameter} | {payload}\n")
                        alert.accept()  # 알림창 닫기
                        entry['severity'] = 'High'
                    except:
                        print(Fore.RED + "셀레니움 테스트 실패, 이벤트 발생 X - Reflected XSS" + Style.RESET_ALL +
                              f"\n{page_url} | {parameter} | {payload}\n")
                        entry['severity'] = 'Low'
                        entry['check'] = 'y'
                elif xss_type == "Stored XSS":
                    # 리디렉션된 페이지에서 alert 확인
                    try:
                        alert = driver.switch_to.alert
                        print(Fore.GREEN + "셀레니움 테스트 성공, 검증 완료 - Stored XSS" + Style.RESET_ALL +
                              f"\n{page_url} | {parameter} | {payload}\n")
                        alert.accept()
                        entry['severity'] = 'High'
                    except:
                        # 원래의 페이지로 돌아가서 alert 확인
                        driver.back()
                        time.sleep(2)
                        try:
                            alert = driver.switch_to.alert
                            print(Fore.GREEN + "셀레니움 테스트 성공, 검증 완료 - Stored XSS" + Style.RESET_ALL +
                                  f"\n{page_url} | {parameter} | {payload}\n")
                            alert.accept()
                            entry['severity'] = 'High'
                        except:
                            print(Fore.RED + "셀레니움 테스트 실패, 이벤트 발생 X - Stored XSS" + Style.RESET_ALL +
                                  f"\n{page_url} | {parameter} | {payload}\n")
                            entry['severity'] = 'Medium'
                            # 'check' 필드에 'y' 추가
                            entry['check'] = 'y'
                else:
                    # xss_type이 없거나 다른 값일 때
                    # xss_type 필드 생성
                    # 1) 제출 직후 alert 확인
                    try:
                        alert = driver.switch_to.alert
                        print(Fore.GREEN + "셀레니움 테스트 성공, 검증 완료 - Reflected XSS" + Style.RESET_ALL +
                              f"\n{page_url} | {parameter} | {payload}\n")
                        alert.accept()
                        entry['XSS Type'] = 'Reflected XSS'
                        entry['severity'] = 'High'
                    except:
                        # 2) 리디렉션된 페이지에서 alert 확인
                        time.sleep(2)
                        try:
                            alert = driver.switch_to.alert
                            print(Fore.GREEN + "셀레니움 테스트 성공, 검증 완료 - Stored XSS" + Style.RESET_ALL +
                                  f"\n{page_url} | {parameter} | {payload}\n")
                            alert.accept()
                            entry['XSS Type'] = 'Stored XSS'
                            entry['severity'] = 'High'
                        except:
                            # 3) 원래의 페이지로 돌아가서 alert 확인
                            driver.back()
                            time.sleep(2)
                            try:
                                alert = driver.switch_to.alert
                                print(Fore.GREEN + "셀레니움 테스트 성공, 검증 완료 - Stored XSS" + Style.RESET_ALL +
                                      f"\n{page_url} | {parameter} | {payload}\n")
                                alert.accept()
                                entry['XSS Type'] = 'Stored XSS'
                                entry['severity'] = 'High'
                            except:
                                print(Fore.RED + "셀레니움 테스트 실패, 이벤트 발생 X" + Style.RESET_ALL +
                                      f"\n{page_url} | {parameter} | {payload}\n")
                                entry['XSS Type'] = 'XSS'
                                entry['severity'] = 'Low'
                            
            except Exception as e:
                print(Fore.BLUE + "셀레니움 테스트 실패 : 오탐 detect" + Style.RESET_ALL +
                      f"\n{page_url} | {parameter} | {payload}\n")
                # 오탐으로 간주하여 엔트리를 제거할 리스트에 추가
                entries_to_remove.append(entry)
        else:
            print(f"지원되지 않는 메소드: {form_method}")
            # 'severity'를 'Medium'으로 설정
            entry['severity'] = 'Medium'
            entry['check'] = 'y'
    except KeyError as e:
        print(f"키 에러 발생: {e} - 해당 엔트리: {entry}")
        entries_to_remove.append(entry)

# 드라이버 종료
driver.quit()

# 오탐지를 crash_data에서 제거 (Attack Type이 "XSS"인 항목들만 제거)
for entry in entries_to_remove:
    crash_data.remove(entry)

# 변경된 데이터를 JSON 파일에 다시 저장
with open('crash_data.json', 'w') as file:
    json.dump(crash_data, file, indent=4)

print(f"{len(entries_to_remove)}개의 오탐 엔트리가 제거되었습니다.")

# 로그 설정
log_file = "selenium_validation_logs.log"  # 로그 파일 이름
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filemode='w'  # 'w'를 설정하면 로그 파일을 덮어쓰며 기록 -> 기존 남아있던 로그 삭제 

)

log_msg = f"privacy.md"
logging.info(log_msg)  # 로그 기록
