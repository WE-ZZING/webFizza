import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
import tldextract
from furl import furl

# 로깅 설정
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

visited_urls = set()  # 방문한 URL을 저장하는 집합

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

def parse_page(url, headers, GET, delay, timeout):
    response = requester(url, {}, headers, GET, delay, timeout)
    if response is None:
        # Try https if http fails
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
            response = requester(url, {}, headers, GET, delay, timeout)
            if response is None:
                return None
        else:
            return None

    soup = BeautifulSoup(response.content, 'html.parser')

    page_data = {
        'url': url,
        'forms': [],
    }

    for form in soup.find_all('form'):
        form_data = {
            'action': urljoin(url, form.get('action')),
            'method': form.get('method', 'get'),
            'inputs': []
        }
        for input_tag in form.find_all(['input', 'textarea']):
            input_type = input_tag.get('type', 'text')
            if input_tag.name == 'textarea' or input_type in ['text', 'email', 'password', 'search', 'tel', 'url']:
                input_data = {
                    'tag': input_tag.name,
                    'name': input_tag.get('name'),
                    'type': input_type if input_tag.name == 'input' else '',
                    'value': input_tag.get('value') if input_tag.name == 'input' else '',
                    'events': list(attr for attr in input_tag.attrs if attr.startswith('on')),  # Convert set to list
                    'html': str(input_tag)
                }
                form_data['inputs'].append(input_data)
        page_data['forms'].append(form_data)

    return page_data

def crawl_site(root_url, headers, GET=True, delay=0, timeout=10):
    root_url = add_scheme(root_url)
    site_data = []
    to_crawl = [root_url]
    to_return = []
    
    root_domain = tldextract.extract(root_url).registered_domain
    
    while to_crawl:
        url = to_crawl.pop()
        if url in visited_urls:
            continue
        visited_urls.add(url)
        logger.info(f"Crawling URL: {url}")
        page_data = parse_page(url, headers, GET, delay, timeout)
        if page_data:
            site_data.append(page_data)
            soup = BeautifulSoup(requester(url, {}, headers, GET, delay, timeout).content, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                parsed_full_url = urlparse(full_url)
                if tldextract.extract(parsed_full_url.netloc).registered_domain == root_domain:
                    if full_url not in visited_urls:
                        to_crawl.append(full_url)
            for form in page_data['forms']:
                form_action = form['action']
                if form_action not in visited_urls:  # 중복 크롤링 방지
                    parsed_action_url = urlparse(form_action)
                    parsed_root_url = urlparse(root_url)
                    if parsed_action_url.netloc != parsed_root_url.netloc:
                        to_return.append(form_action)
                    else:
                        to_crawl.append(form_action)
                        
        if not to_crawl and to_return:
            to_crawl.append(to_return.pop(0))

    return site_data

def detect_input_fields(site_data):
    input_fields = []
    
    for page in site_data:
        for form in page['forms']:
            for input_field in form['inputs']:
                input_fields.append({
                    'page_url': page['url'],
                    'form_action': form['action'],
                    'form_method': form['method'],
                    'input_name': input_field['name'],
                    'input_type': input_field['type'],
                    'tag': input_field['tag'],
                    'events': input_field['events'],
                    'html': input_field['html']
                })
    return input_fields

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # Get the root URL from the command line argument
    if len(sys.argv) > 1:
        root_url = sys.argv[1]  # This gets the URL passed from Django
    else:
        print("No URL provided!")
        sys.exit(1)

    headers = {}
    site_data = crawl_site(root_url, headers)
    input_fields = detect_input_fields(site_data)
    
    # Save the result to a JSON file
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'input_fields_{current_time}.json'
    save_to_json(input_fields, filename)

    print(f"Saved input fields to {filename}")
