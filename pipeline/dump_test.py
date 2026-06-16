import requests

url = "https://inference.do-ai.run/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer doo_v1_04d736bf13990b16a51790fa3a5373adb146cfc4b57aaf72eaa4a034268cc1dc"
}

data = {
    "model": "deepseek-r1-distill-llama-70b",
    "messages": [
        {
            "role": "user",
            "content": "What is the capital of Hanoi?"
        }
    ],
    "max_tokens": 100
}

response = requests.post(url, headers=headers, json=data)
print(response.json())