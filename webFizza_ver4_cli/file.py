# file.py

import openai
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Set your OpenAI API key
openai.api_key = {}

def find_xss_attack_vectors_and_types(code):
    # OpenAI 요청을 생성하는 함수
    prompt = (
        f"Analyze the following code to find potential XSS vulnerabilities. "
        f"Print all lines that include input fields (e.g., <input>, <textarea>, <script>, <img>, <iframe>, <a>, <body>, <div>, <span>, <form>, <button>, <select>, <option>) and any code where user input is used, handled, or rendered. "
        f"Identify each vulnerable line and specify the type of XSS (e.g., Reflected XSS, Stored XSS, DOM-Based XSS) for each line without any additional explanation or text. "
        f"For each line with a vulnerability, provide the details in JSON format with the following keys: "
        f"'form_method', 'input_name', 'input_type', 'tag', 'events', 'html', 'xss_type'. "
        f"The 'events' key should be an array of event attributes (e.g., ['onfocus', 'onclick']). "
        f"Here is the code to analyze:\n\n"
        f"{code}\n\nVulnerable lines and types in JSON format:"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in code security analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
            temperature=0.3
        )

        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def find_sqli_attack_vectors_and_types(code):
    # SQL Injection을 찾는 OpenAI 요청을 생성하는 함수
    prompt = (
        f"Analyze the following HTML code to find elements that are potentially vulnerable to SQL Injection."
        f"Extract the parameters that are passed to the server via POST or GET requests."
        f"Also, extract the query parameters in links within the `a` tags which used with href."
        f"For each parameter or link that could potentially be vulnerable to SQL Injection, provide the details in JSON format with the following keys: "
        f"'form_method', 'input_name', 'input_type', 'tag', 'html', 'sqli_type'."
        f"Here is the HTML code to analyze:\n\n"
        f"{code}\n\n"
        f"Provide the output only in JSON format. I don't need any additional explanation or text."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in code security analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
            temperature=0.3
        )

        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def save_to_json(data, filename):
    """Save JSON data to a file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Results saved to {filename}")
    except IOError as e:
        print(f"Error saving file: {e}")

def save_input_to_txt(file, base_url, code_file_txt, base_url_txt):
    """Save user inputs to separate .txt files."""
    try:
        with open(code_file_txt, 'w', encoding='utf-8') as f:
            f.write(f"{file}\n")
    except IOError as e:
        print(f"Error saving file: {e}")

    try:
        with open(base_url_txt, 'w', encoding='utf-8') as f:
            f.write(f"{base_url}\n")
    except IOError as e:
        print(f"Error saving file: {e}")

def modify_json(data, page_url, form_action, attack_type):
    for item in data:
        item['page_url'] = page_url
        item['form_action'] = form_action
        item['attack_type'] = attack_type  # Add the type of attack

        # Add 'sqli_vendor' only if attack_type is 'sqli'
        if attack_type == "sqli":
            item['sqli_vendor'] = "MySQL"  # or set to a specific vendor if known
            
            # If input_type is 'query', modify it to 'query parameter'
            if item.get("input_type") == "query":
                item["input_type"] = "query parameter"
    return data

def extract_form_action(code, base_url):
    """Extract the action attribute values from all <form> tags in the HTML code."""
    soup = BeautifulSoup(code, 'html.parser')
    forms = soup.find_all('form')
    form_actions = [urljoin(base_url, form.get('action', '')) for form in forms]
    return form_actions

def main():
    # Get user input
    file = input("Enter the path to the code file: ").strip()
    base_url = input("Enter the base URL for the page: ").strip()

    # Define filenames for saving user inputs
    code_file_txt = "code_file.txt"
    base_url_txt = "base_url.txt"

    # Save user inputs to separate .txt files
    save_input_to_txt(file, base_url, code_file_txt, base_url_txt)
    
    try:
        with open(file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        print(f"Loaded file: {file}")

        # Extract form action values
        form_actions = extract_form_action(code, base_url)
        if not form_actions:
            form_actions = [base_url]  # Default to base_url if no action is found

        # Process each form action separately
        combined_results = []
        for form_action in form_actions:

            # Get results from OpenAI for XSS
            xss_results = find_xss_attack_vectors_and_types(code)

            # Get results from OpenAI for SQL Injection
            sqli_results = find_sqli_attack_vectors_and_types(code)

            # Try to parse XSS results into JSON
            try:
                xss_results_json = json.loads(xss_results)
                # Modify results with additional information
                xss_modified_results = modify_json(xss_results_json, base_url, form_action, "XSS")
                combined_results.extend(xss_modified_results)
            except json.JSONDecodeError:
                print("Failed to parse XSS results into JSON format. The response might not be valid JSON.")

            # Try to parse SQL Injection results into JSON
            try:
                sqli_results_json = json.loads(sqli_results)
                # Modify results with additional information
                sqli_modified_results = modify_json(sqli_results_json, base_url, form_action, "sqli")
                combined_results.extend(sqli_modified_results)
            except json.JSONDecodeError:
                print("Failed to parse SQL Injection results into JSON format. The response might not be valid JSON.")

        # Get the current time for the filename
        output_file = f"input_fields_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Save combined results to a file
        if combined_results:
            save_to_json(combined_results, output_file)
        else:
            print("No valid JSON results to save.")
    
    except FileNotFoundError:
        print(f"File not found. Please enter a valid file path.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()