import os
import json
import openai
import tiktoken

# OpenAI API 키 설정
openai.api_key = {}

# 외부 파일 저장 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 파일의 디렉토리
EXTERNAL_FILES_DIR = os.path.join(BASE_DIR, 'md_files')  # 실제 경로로 변경

# 디렉토리 확인 및 생성
if not os.path.exists(EXTERNAL_FILES_DIR):
    os.makedirs(EXTERNAL_FILES_DIR)

# 정확한 토큰 수를 계산하기 위한 함수
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
            # 현재 청크 저장
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_tokens = line_tokens
        else:
            current_chunk.append(line)
            current_tokens += line_tokens

    # 마지막 청크 추가
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

# 패치 제안 생성 함수
def suggest_patches():
    """Generate code patch suggestions based on the URL from crash_data.json."""
    
    try:
        # Load crash data
        with open('crash_data.json', "r") as f:
            crash_data = json.load(f)

        # JSON 데이터를 7000 토큰씩 청크로 나누기
        json_chunks = split_json_by_tokens(crash_data, max_tokens=7000)

    except Exception as e:
        print(f"Error loading crash data file: {e}")
        return

    # 마크다운 파일 저장 경로
    output_file_path = os.path.join(EXTERNAL_FILES_DIR, 'patch.md')

    try:
        with open(output_file_path, "w") as f:
            # 각 청크에 대해 OpenAI API 호출
            for i, chunk in enumerate(json_chunks):
                messages = [
                    {"role": "system", "content": "You are a helpful assistant skilled in secure coding and code patching."},
                    {"role": "user", "content": (
                        "Based on the provided crash data and code, suggest patches to fix vulnerabilities. "
                        "Your response should only include:\n\n"
                        "## Original Code\n"
                        "```\n{original_code}\n```\n\n"
                        "## Suggested Code\n"
                        "```\n{suggested_code}\n```\n\n"
                        f"Crash Data:\n{chunk}\n\n"
                        "Include no additional explanation or formatting."
                    )}
                ]

                try:
                    # OpenAI API 호출
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.5
                    )
                    patch_content = response.choices[0].message['content'].strip()

                    # 각 청크 결과를 파일에 추가 저장
                    f.write(f"### Patch Suggestions for Chunk {i + 1}\n")
                    f.write(f"{patch_content}\n\n")
                except Exception as e:
                    print(f"Error processing chunk {i + 1}: {e}")
                    continue

        print(f"Patch suggestions saved to {output_file_path}")
    
    except Exception as e:
        print(f"Error suggesting code patches: {e}")

# 메인 함수
def main():
    # Generate patches
    suggest_patches()

if __name__ == "__main__":
    main()

