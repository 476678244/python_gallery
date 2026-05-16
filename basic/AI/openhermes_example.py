import requests

def interact_with_openhermes(prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "openhermes",
        "prompt": prompt
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()  # 检查请求是否成功，若不成功则抛出异常
        return response.json()
    except requests.RequestException as e:
        print(f"请求出现错误: {e}")
        return None

# 示例使用，这里让模型写一首诗
prompt = "请帮我写一首关于春天的古诗"
result = interact_with_openhermes(prompt)
if result:
    print(result)