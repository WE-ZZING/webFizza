import openai
import json
import tiktoken  # 정확한 토큰 계산을 위한 라이브러리 설치 필요: pip install tiktoken
import os

# OpenAI API 키 설정
openai.api_key = {}

# 정확한 토큰 계산 함수
def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# JSON 데이터를 필요한 필드만 추출
def extract_relevant_fields(data):
    relevant_data = []
    for item in data:
        # XSS_Type 필드 우선, 없으면 Attack Type 사용
        vulnerability = item.get("XSS Type", item.get("Attack Type", "N/A"))
        relevant_data.append({
            "Severity": item.get("severity", "N/A"),
            "Payload": item.get("Payload", "N/A"),
            "Vulnerability": vulnerability,
            "Form Method": item.get("Form Method", "N/A"),
            "Page Url": item.get("Page Url", "N/A"),
            "Status Code": item.get("Status Code", "N/A"),
        })
    return relevant_data

# JSON 데이터를 더 작은 청크로 분할
def split_json_by_tokens(data, model="gpt-4", max_tokens=7000):
    json_string = json.dumps(data, indent=2)
    segments = json_string.split("},")  # }, 기준으로 분할

    chunks = []
    current_chunk = []
    current_text = ""

    for segment in segments:
        if not segment.endswith("}"):
            segment += "},"

        # 새 청크가 최대 토큰 제한을 초과하는지 확인
        test_text = current_text + segment
        if count_tokens(test_text, model) > max_tokens:
            # 현재 청크 저장
            chunks.append(current_text)
            current_chunk = []
            current_text = segment
        else:
            current_chunk.append(segment)
            current_text = "".join(current_chunk)

    # 마지막 청크 추가
    if current_text:
        chunks.append(current_text)

    return chunks

# 마크다운 테이블 생성 함수
def create_markdown_table(json_chunk):
    json_data = json_chunk

    user_message = f"""
Convert the following JSON data into a Markdown table. Only provide the table structure without any additional explanations.

Here is the JSON data:

{json_data}
    """

    # 메시지 전체 길이 계산
    total_tokens = count_tokens(user_message, "gpt-4")
    if total_tokens > 8192:
        raise ValueError("청크가 여전히 너무 큽니다. 더 작은 크기로 분할이 필요합니다.")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": user_message}
        ],
        temperature=0,
        max_tokens=1000  # 응답 토큰 제한
    )

    return response.choices[0].message['content'].strip()

# 저장 경로 설정 (external_files 디렉토리)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 파일의 디렉토리
EXTERNAL_FILES_DIR = os.path.join(BASE_DIR, 'md_files')

# 디렉토리 생성 (존재하지 않으면)
if not os.path.exists(EXTERNAL_FILES_DIR):
    os.makedirs(EXTERNAL_FILES_DIR)

# JSON 파일 읽기
with open('crash_data.json', 'r') as file:
    data = json.load(file)

# 필요한 필드만 추출
filtered_data = extract_relevant_fields(data)

# JSON 데이터를 분할
json_chunks = split_json_by_tokens(filtered_data)

# 마크다운 파일 저장 경로
output_file_path = os.path.join(EXTERNAL_FILES_DIR, 'report.md')

# 모든 청크를 처리하여 마크다운 파일로 저장
with open(output_file_path, 'w', encoding='utf-8') as file:
    for i, chunk in enumerate(json_chunks):
        try:
            markdown_table = create_markdown_table(chunk)
            file.write(f"{markdown_table}\n\n")
        except ValueError as e:
            print(f"청크 {i + 1} 처리 중 오류 발생: {e}")
            continue

print(f"Markdown file has been created at: {output_file_path}")

