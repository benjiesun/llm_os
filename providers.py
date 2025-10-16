# providers.py
import os, json, time
import requests
import torch

class BaseProvider:
    def chat(self, messages, max_new_tokens=512, temperature=0.7):
        raise NotImplementedError

class LocalHFProvider(BaseProvider):
    def __init__(self, tokenizer, model, device, extract_fn):
        self.tok = tokenizer
        self.model = model
        self.device = device
        self.extract = extract_fn

    def chat(self, messages, max_new_tokens=512, temperature=0.7):
        from contextlib import nullcontext
        ctx = torch.no_grad() if torch else nullcontext()
        with ctx:
            text = self.tok.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
            )
            inputs = self.tok(text, return_tensors="pt").to(self.device)
            out = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=(temperature>0),
                temperature=temperature if temperature>0 else 0.0,
                pad_token_id=self.tok.eos_token_id,
            )
            decoded = self.tok.decode(out[0], skip_special_tokens=True)
            return self.extract(decoded)

class OpenAICompatAPIProvider(BaseProvider):
    """
    兼容 OpenAI Chat Completions 的任何在线服务：
    - 官方 OpenAI： https://api.openai.com/v1
    - 自建 vLLM (--openai-api) ：http://<host>:<port>/v1
    - 其他聚合平台（多数都兼容）
    """
    def __init__(self):
        self.base = os.getenv("API_BASE", "").rstrip("/")
        self.key  = os.getenv("API_KEY", "")
        self.model = os.getenv("API_MODEL", "gpt-4o-mini")
        self.timeout = float(os.getenv("API_TIMEOUT", "30"))
        assert self.base and self.key, "API_BASE 或 API_KEY 未配置"

    def chat(self, messages, max_new_tokens=512, temperature=0.7):
        url = f"{self.base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": max(0.0, float(temperature)),
            "max_tokens": int(max_new_tokens),
            # "stream": False,  # 如需流式，改 True 并按 SSE 解析
        }

        # 简单重试
        for attempt in range(3):
            try:
                r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=self.timeout)
                if r.status_code == 200:
                    data = r.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    err = r.text[:500]
                    if 400 <= r.status_code < 500:
                        # 客户端错误不再重试
                        return f"❌ API 错误 {r.status_code}: {err}"
                    time.sleep(1.5 * (attempt + 1))
            except requests.RequestException as e:
                if attempt == 2:
                    return f"⚠️ API 请求异常：{e}"
                time.sleep(1.5 * (attempt + 1))
        return "⚠️ API 未返回有效结果"
