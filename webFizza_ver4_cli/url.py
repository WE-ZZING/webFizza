import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse, parse_qs
import time
from datetime import datetime
import tldextract
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

visited_urls = set()  # 방문한 URL을 저장하는 집합
visited_params = set()  # 방문한 URL 경로와 파라미터 조합을 저장하는 집합

def requester(url, params, headers, GET, delay, timeout):
    try:
        if GET:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
        else:
            response = requests.post(url, headers=headers, data=params, timeout=timeout)
        response.raise_for_status()
        time.sleep(delay)  # 요청 사이에 지연 추가
        return response
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

def add_scheme(url):
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = 'http://' + url
    return url

def is_duplicate_url(url):
    """URL이 중복되었는지 확인"""
    parsed_url = urlparse(url)
    base_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path  # 경로와 도메인
    query_params = parse_qs(parsed_url.query)

    # 같은 경로와 같은 파라미터가 이미 있는 경우 중복 처리
    for param, values in query_params.items():
        param_key = (base_url, param)
        if param_key in visited_params:
            logger.info(f"Skipping URL due to repeated parameter: {url}")
            return True
        visited_params.add(param_key)
    
    return False

def parse_page(url, headers, GET, delay, timeout):
    response = requester(url, {}, headers, GET, delay, timeout)
    if response is None:
        logger.error(f"Skipping URL due to request failure: {url}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    page_data = {
        'url': url,
        'forms': [],
    }

    # 폼 데이터 추출
    for form in soup.find_all('form'):
        form_data = {
            'action': urljoin(url, form.get('action')),
            'method': form.get('method', 'get'),
            'inputs': []
        }
        for input_tag in form.find_all(['input', 'textarea']):
            input_data = {
                'tag': input_tag.name,
                'name': input_tag.get('name'),
                'type': input_tag.get('type', 'text'),
                'value': input_tag.get('value', ''),
                'html': str(input_tag)
            }
            form_data['inputs'].append(input_data)
        page_data['forms'].append(form_data)

    # URL에서 쿼리 파라미터 추출
    parsed_url = urlparse(url)
    query_parameters = parse_qs(parsed_url.query)
    page_data['query_parameters'] = query_parameters

    return page_data

def crawl_site(root_url, headers, GET=True, delay=0, timeout=10):
    root_url = add_scheme(root_url)
    site_data = []
    to_crawl = [root_url]
    
    root_domain = tldextract.extract(root_url).registered_domain
    
    while to_crawl:
        url = to_crawl.pop()

        # URL이 중복되는지 확인
        if is_duplicate_url(url):
            continue

        if url in visited_urls:
            continue

        visited_urls.add(url)
        logger.info(f"Crawling URL: {url}")
        
        page_data = parse_page(url, headers, GET, delay, timeout)
        if page_data:
            site_data.append(page_data)

            # 링크 크롤링
            soup = BeautifulSoup(requester(url, {}, headers, GET, delay, timeout).content, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                parsed_full_url = urlparse(full_url)
                if tldextract.extract(parsed_full_url.netloc).registered_domain == root_domain:
                    if full_url not in visited_urls:
                        to_crawl.append(full_url)

    return site_data

def detect_input_fields(site_data):
    input_fields = []
    
    for page in site_data:
        # URL에 포함된 쿼리 파라미터를 처리
        query_params = page['query_parameters']
        for param, value in query_params.items():
            input_fields.append({
                'page_url': page['url'],
                'form_action': '',
                'form_method': 'GET',
                'input_name': param,  # URL에서 추출한 쿼리 파라미터 이름
                'input_type': 'query parameter',  # 쿼리 파라미터로 설정
                'tag': 'a',  # URL 파라미터는 a 태그로 간주
                'html': f'<a href="{page["url"]}">{param}={value[0]}</a>'  # 파라미터와 URL을 기록
            })
        
        # form에서 추출된 input 처리
        for form in page['forms']:
            for input_field in form['inputs']:
                # input_name이 null 또는 빈 값이 아닌 경우에만 처리
                if input_field['name'] and input_field['name'].lower() != "null":
                    input_fields.append({
                        'page_url': page['url'],
                        'form_action': form['action'],
                        'form_method': form['method'],
                        'input_name': input_field['name'],
                        'input_type': input_field['type'],
                        'tag': input_field['tag'],
                        'html': input_field['html']
                    })
    
    return input_fields

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    root_url = input("Enter the root URL: ")  # 사용자로부터 root URL을 입력받습니다.
    headers = {}
    site_data = crawl_site(root_url, headers)
    input_fields = detect_input_fields(site_data)
    
    # 현재 날짜 및 시각을 기반으로 파일 이름 생성
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'input_fields_{current_time}.json'
    
    save_to_json(input_fields, filename)
    logger.info(f"Saved input fields and query parameters to {filename}")
