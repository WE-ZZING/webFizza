import os
import json
import openai
import tiktoken

# OpenAI API 키 설정
openai.api_key = {}  # API 키 입력

# 외부 파일 저장 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXTERNAL_FILES_DIR = os.path.join(BASE_DIR, 'md_files')

if not os.path.exists(EXTERNAL_FILES_DIR):
    os.makedirs(EXTERNAL_FILES_DIR)

# 토큰 계산 함수
def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# JSON 데이터를 분할하는 함수
def split_json_by_tokens(data, model="gpt-4", max_tokens=7000):
    json_string = json.dumps(data, indent=2)
    lines = json_string.splitlines()

    chunks = []
    current_chunk = []
    current_tokens = 0

    for line in lines:
        line_tokens = count_tokens(line, model)
        if current_tokens + line_tokens > max_tokens:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_tokens = line_tokens
        else:
            current_chunk.append(line)
            current_tokens += line_tokens

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

# 테이블 파싱 함수
def extract_markdown_table(content):
    """응답에서 Markdown 테이블 부분만 추출"""
    table_start = content.find("|")
    if table_start == -1:
        raise ValueError("응답에 Markdown 테이블이 없습니다.")
    return content[table_start:].strip()

# MD 파일 생성 함수
def create_markdown_table(chunk):
    user_message = f"""
JSON 데이터를 분석하여 개인정보 보호법 위반 항목을 한국어로 작성해 주세요. 
위반 항목의 경우, 공격 이름만 작성합니다. (ex. XSS)
위반 조항의 경우, '개인정보보호법 제x조'로만 작성해야 합니다. (x는 상수)
결과는 **오직 아래 형식의 Markdown 테이블**로만 제공해주세요 (테이블 이외의 텍스트를 추가하지 마세요):

[ violation | policy | details | recommendation ]

다음은 JSON 데이터입니다:

{chunk}
    """

    total_tokens = count_tokens(user_message, "gpt-4")
    if total_tokens > 8192:
        raise ValueError("청크가 여전히 너무 큽니다. 더 작은 크기로 분할하세요.")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": (
                "You are a helpful assistant. Always respond strictly in the format of a Markdown table as instructed. "
                "Do not include any text before or after the table."
            )},
            {"role": "user", "content": user_message}
        ],
        temperature=0,
        max_tokens=1000
    )

    raw_content = response.choices[0].message['content'].strip()
    return extract_markdown_table(raw_content)

# JSON 파일 읽기
with open('crash_data.json', 'r') as file:
    data = json.load(file)

# JSON 데이터를 분할
json_chunks = split_json_by_tokens(data)

# 마크다운 파일 저장 경로
output_file_path = os.path.join(EXTERNAL_FILES_DIR, 'privacy.md')

# 모든 청크를 처리하여 마크다운 파일로 저장
with open(output_file_path, 'w', encoding='utf-8') as file:
    for i, chunk in enumerate(json_chunks):
        try:
            markdown_table = create_markdown_table(chunk)
            file.write(f"{markdown_table}\n\n")
        except ValueError as e:
            print(f"청크 {i + 1} 처리 중 오류 발생: {e}")
            continue

print(f"Markdown 파일이 생성되었습니다: {output_file_path}")
