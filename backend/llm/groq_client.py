from groq import Groq
import os
import time

class GroqClient:
    # Leave headroom below Groq's 8000 TPM limit for estimation variance.
    MAX_REQUEST_TOKENS = 7600
    MIN_COMPLETION_TOKENS = 256

    @staticmethod
    def _estimate_prompt_tokens(messages):
        text = "\n".join(str(message.get("content", "")) for message in messages)
        # Vietnamese prose can tokenize more densely than English; /3 is conservative.
        return max(1, (len(text) + 2) // 3)

    def _safe_max_tokens(self, messages, requested):
        prompt_tokens = self._estimate_prompt_tokens(messages)
        available = self.MAX_REQUEST_TOKENS - prompt_tokens
        if available < self.MIN_COMPLETION_TOKENS:
            raise ValueError("Nội dung yêu cầu quá dài, hãy rút gọn bản phác thảo hoặc lịch sử truyện rồi thử lại.")
        return min(requested, available)

    @staticmethod
    def _is_request_too_large(error):
        message = str(error)
        return "413" in message or "rate_limit_exceeded" in message or "Request too large" in message

    @staticmethod
    def _retry_budgets(initial):
        budgets = [initial, max(256, int(initial * 0.75)), max(256, int(initial * 0.5))]
        return list(dict.fromkeys(budgets))

    def __init__(self, model_name: str = "openai/gpt-oss-120b", api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Thiếu biến môi trường GROQ_API_KEY hoặc key chuyên dụng tương ứng")
            
        self.client = Groq(api_key=self.api_key)
        self.model = model_name
    
    def chat(self, messages, temperature=0.7, max_tokens=2000, response_format=None):
        """Send message to Groq LLM"""
        safe_max_tokens = self._safe_max_tokens(messages, max_tokens)
        budgets = self._retry_budgets(safe_max_tokens)
        last_error = None
        for index, budget in enumerate(budgets):
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": budget,
            }
            if response_format:
                params["response_format"] = response_format
            try:
                response = self.client.chat.completions.create(**params)
                return response.choices[0].message.content
            except Exception as error:
                last_error = error
                if not self._is_request_too_large(error) or index == len(budgets) - 1:
                    raise
                time.sleep(0.25)
        raise last_error

    def chat_stream(self, messages, temperature=0.7, max_tokens=2000):
        """Send message to Groq LLM with streaming"""
        safe_max_tokens = self._safe_max_tokens(messages, max_tokens)
        budgets = self._retry_budgets(safe_max_tokens)
        for index, budget in enumerate(budgets):
            emitted = False
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=budget,
                    stream=True
                )
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        emitted = True
                        yield content
                return
            except Exception as error:
                if emitted or not self._is_request_too_large(error) or index == len(budgets) - 1:
                    raise
                time.sleep(0.25)
