import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any
try:
    import httpx
except ImportError:
    httpx = None
from src.config.settings import AppSettings
from src.core.local_translator import LocalOfflineTranslator

logger = logging.getLogger("AITranslator")

class AITranslator:
    """Multi-Provider AI Streaming Translator with Local Offline Draft & Fallback."""
    
    def __init__(self, settings: Optional[AppSettings] = None):
        self.settings = settings or AppSettings()
        self._client: Optional[httpx.AsyncClient] = None
        self.local_engine = LocalOfflineTranslator.get_instance()
        self._cache: Dict[Tuple[str, str, str], str] = {}
        self._max_cache_size = 500

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(max_keepalive_connections=15, max_connections=30, keepalive_expiry=60.0)
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0), limits=limits)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def sanitize_translation_output(text: str) -> str:
        """Strip AI conversational boilerplate, markdown code blocks, prefixes, and outer quotes."""
        if not text:
            return ""
        
        result = text.strip()
        
        # Remove Markdown code blocks ``` ... ```
        if result.startswith("```") and result.endswith("```"):
            lines = result.splitlines()
            if len(lines) >= 2:
                result = "\n".join(lines[1:-1]).strip()
        
        # Remove common prefixes: "Bản dịch:", "Dịch là:", "Translation:", etc.
        prefix_pattern = r'^(?:Bản dịch\s*(?:tiếng Việt)?|Dịch\s*(?:nghĩa|là)?|Translation|Vietnamese translation|Vietnamese)\s*:\s*'
        import re
        result = re.sub(prefix_pattern, '', result, flags=re.IGNORECASE).strip()
        
        # Remove surrounding outer double or single quotes if wrapping entire string
        if (result.startswith('"') and result.endswith('"') and len(result) >= 2 and result.count('"') == 2) or \
           (result.startswith("'") and result.endswith("'") and len(result) >= 2 and result.count("'") == 2):
            result = result[1:-1].strip()
            
        return result

    def build_system_prompt(self, src_lang: str = "ja", tgt_lang: str = "vi", glossary_info: str = "", local_draft: str = "") -> str:
        lang_names = {
            "ja": "Japanese (ja)",
            "en": "English (en)",
            "zh": "Chinese (zh)",
            "ko": "Korean (ko)",
            "vi": "Vietnamese (vi)"
        }
        src_name = lang_names.get(src_lang, src_lang)
        tgt_name = lang_names.get(tgt_lang, tgt_lang)
        
        custom_system_prompt = self.settings.get("system_prompt", "").strip()
        if custom_system_prompt:
            base_prompt = custom_system_prompt
        elif local_draft:
            # Token-optimized hybrid prompt (saves ~74% prompt tokens)
            base_prompt = (
                f"Bạn là chuyên gia bản địa hóa Visual Novel sang Tiếng Việt ({tgt_name}).\n"
                "Nhiệm vụ: Trau chuốt câu dịch thô (Local Draft) dưới đây thành câu thoại tiếng Việt tự nhiên, chuẩn ngữ cảnh và cảm xúc nhân vật.\n"
                "Quy tắc tuyệt đối: Chỉ xuất DUY NHẤT câu dịch tiếng Việt hoàn chỉnh, không giải thích, không thêm tiền tố hay dấu ngoặc thừa."
            )
        else:
            base_prompt = (
                f"You are a master Visual Novel and Japanese Game Localization Specialist translating from {src_name} to {tgt_name}.\n"
                "Your objective: Deliver an ultra-natural, immersive, emotionally resonant translation into Vietnamese that flows like a professional visual novel publication.\n\n"
                "### CORE LOCALIZATION GUIDELINES\n"
                "1. IMMERSIVE & NATURAL VIETNAMESE: Translate idioms, tone, and spoken nuances naturally. Never translate literally word-by-word (avoid machine translation / rough MTL style).\n"
                "2. CHARACTER PRONOUNS & TONE: Choose natural Vietnamese pronouns according to relationship context (e.g., Tôi - Cậu, Anh - Em, Tiền bối - Hậu bối, Ta - Ngươi, v.v.). Strictly follow any active Glossary rules.\n"
                "3. SPEAKER & QUOTE PRESERVATION: If a line starts with a speaker name in brackets like 【Name】 or Name:, keep or translate the name tag appropriately. Preserve dialogue quotations and Japanese punctuation dynamics ('...', '!', '?', '――').\n"
                "4. STRICT CLEAN OUTPUT:\n"
                "   - Output ONLY the translated dialogue.\n"
                "   - Do NOT output conversational filler, notes, prefixes (like 'Bản dịch:'), markdown tags, or quotation wrappers."
            )
        
        parts = [base_prompt]
        if glossary_info:
            parts.append(f"\n### ACTIVE GLOSSARY RULES\n{glossary_info}")
        
        return "\n".join(parts)

    def build_full_prompt(self, text: str, src_lang: str = "ja", tgt_lang: str = "vi", context: str = "", glossary_info: str = "", local_draft: str = "") -> str:
        if local_draft:
            # Compact hybrid prompt format to minimize input token cost
            parts = [
                f"- Thoại gốc ({src_lang}): {text}",
                f"- Bản dịch thô: {local_draft}"
            ]
            if glossary_info:
                parts.append(f"- Từ điển xưng hô: {glossary_info}")
            if context:
                parts.append(f"- Ngữ cảnh gần nhất:\n{context}")
            return "\n".join(parts)

        parts = [
            "### INPUT DATA",
            f"- Source Language: {src_lang}",
            f"- Target Language: {tgt_lang}"
        ]
        if glossary_info:
            parts.append(f"- Character Glossary: {glossary_info}")
        if context:
            parts.append(f"- Recent Dialogue History:\n{context}")
        parts.append(f"- Original Dialogue to Translate:\n{text}")
        return "\n".join(parts)

    def parse_gemini_sse_line(self, line: str) -> Optional[str]:
        line = line.strip()
        if not line.startswith("data:"):
            return None
        data_str = line[5:].strip()
        if not data_str:
            return None
        try:
            data = json.loads(data_str)
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        except Exception:
            pass
        return None

    def parse_openai_sse_line(self, line: str) -> Optional[str]:
        line = line.strip()
        if not line.startswith("data:"):
            return None
        data_str = line[5:].strip()
        if data_str == "[DONE]" or not data_str:
            return None
        try:
            data = json.loads(data_str)
            choices = data.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                return delta.get("content", "")
        except Exception:
            pass
        return None

    def parse_claude_sse_line(self, line: str) -> Optional[str]:
        line = line.strip()
        if not line.startswith("data:"):
            return None
        data_str = line[5:].strip()
        if not data_str:
            return None
        try:
            data = json.loads(data_str)
            if data.get("type") == "content_block_delta":
                return data.get("delta", {}).get("text", "")
        except Exception:
            pass
        return None

    async def translate_stream(
        self,
        text: str,
        provider: Optional[str] = None,
        src_lang: str = "ja",
        tgt_lang: str = "vi",
        context: str = "",
        glossary_info: str = "",
        bypass_fallback: bool = False
    ) -> AsyncGenerator[str, None]:
        """Stream translated chunks with Hybrid Local Draft & Cloud AI polish."""
        # 0. Check in-memory session cache (0 tokens, 0ms latency)
        cache_key = (text.strip(), src_lang, tgt_lang)
        if not bypass_fallback and cache_key in self._cache:
            yield self._cache[cache_key]
            return

        offline_only = self.settings.get("offline_only", False)
        hybrid_mode = self.settings.get("hybrid_mode", True)
        
        # 1. Generate Local Offline Draft (Argos Translate)
        local_draft = ""
        if (offline_only or hybrid_mode) and not bypass_fallback:
            try:
                local_draft = self.local_engine.translate(text, src_lang, tgt_lang)
            except Exception as e:
                logger.warning(f"Local draft generation failed: {e}")

        # If 100% Offline mode is enabled, return immediately
        if offline_only and not bypass_fallback:
            if local_draft:
                yield local_draft
            else:
                yield f"[Offline Local: Không tìm thấy gói mô hình {src_lang}->{tgt_lang}]"
            return

        provider = provider or self.settings.get("selected_provider", "gemini")
        provider_cfg = self.settings.get_provider_config(provider)
        api_key = provider_cfg.get("api_key", "").strip()
        model = provider_cfg.get("model", "")
        base_url = provider_cfg.get("base_url", "")
        
        system_prompt = self.build_system_prompt(src_lang, tgt_lang, glossary_info, local_draft=local_draft)
        user_prompt = self.build_full_prompt(text, src_lang, tgt_lang, context, glossary_info, local_draft=local_draft)
        
        if not api_key and provider != "custom":
            if not bypass_fallback and local_draft:
                yield local_draft
                return
            yield f"[Lỗi: Chưa nhập API Key cho {provider.upper()}. Vui lòng vào tab 'Nhà Cung Cấp AI' để điền key và nhấn 'Lưu Cài Đặt'.]"
            return

        if provider == "gemini" and (api_key.startswith("http://") or api_key.startswith("https://") or "gemini.google.com" in api_key):
            if not bypass_fallback and local_draft:
                yield local_draft
                return
            yield "[Lỗi API Key: Bạn đang nhập đường link web thay vì mã API Key. Vui lòng copy chuỗi ký tự API Key từ https://aistudio.google.com/app/apikey]"
            return

        try:
            client = await self.get_client()
            if provider == "gemini":
                # Gemini Streaming REST API with smart model auto-fallback
                candidate_models = [
                    model,
                    "gemini-2.5-flash",
                    "gemini-2.0-flash",
                    "gemini-1.5-flash"
                ]
                seen = set()
                unique_candidates = [m for m in candidate_models if m and not (m in seen or seen.add(m))]
                
                last_err = ""
                success = False
                for try_model in unique_candidates:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{try_model}:streamGenerateContent?alt=sse&key={api_key}"
                    payload = {
                        "system_instruction": {
                            "parts": [{"text": system_prompt}]
                        },
                        "contents": [{
                            "role": "user",
                            "parts": [{"text": user_prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 256
                        }
                    }
                    try:
                        # Short connect/read timeout per model so fallback triggers instantly
                        async with client.stream("POST", url, json=payload, headers={"Content-Type": "application/json"}, timeout=httpx.Timeout(10.0, connect=4.0)) as resp:
                            if resp.status_code == 200:
                                success = True
                                async for line in resp.aiter_lines():
                                    chunk = self.parse_gemini_sse_line(line)
                                    if chunk:
                                        yield chunk
                                break
                            else:
                                err_body = await resp.aread()
                                raw_err = err_body.decode('utf-8', errors='ignore')
                                try:
                                    err_json = json.loads(raw_err)
                                    msg = err_json.get("error", {}).get("message", raw_err)
                                except Exception:
                                    msg = raw_err
                                last_err = f"[Gemini Error {resp.status_code}: {msg}]"
                                logger.warning(f"Gemini model {try_model} returned {resp.status_code}, trying fallback...")
                    except Exception as req_err:
                        last_err = f"[Gemini {try_model} error: {req_err}]"
                        logger.warning(f"Gemini model {try_model} failed with {req_err}, trying fallback...")
                    
                if not success:
                    if not bypass_fallback and local_draft:
                        logger.info("Gemini cloud request failed, falling back to local offline draft.")
                        yield local_draft
                        return
                    if last_err:
                        yield last_err
                        return

            elif provider == "claude":
                # Anthropic Claude Streaming
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                payload = {
                    "model": model,
                    "max_tokens": 256,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                    "stream": True,
                    "temperature": 0.3
                }
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        err_body = await resp.aread()
                        raw_err = err_body.decode('utf-8', errors='ignore')
                        try:
                            err_json = json.loads(raw_err)
                            msg = err_json.get("error", {}).get("message", raw_err)
                        except Exception:
                            msg = raw_err
                        err_msg = f"[Claude Error {resp.status_code}: {msg}]"
                        if not bypass_fallback and local_draft:
                            yield local_draft
                            return
                        yield err_msg
                        return
                    async for line in resp.aiter_lines():
                        chunk = self.parse_claude_sse_line(line)
                        if chunk:
                            yield chunk

            else:
                # OpenAI Compatible (OpenAI, DeepSeek, Groq, OpenRouter, Custom)
                base = base_url.rstrip("/")
                if not base.endswith("/v1"):
                    base = f"{base}/v1" if not base.endswith("/v1") and "v1" not in base else base
                url = f"{base}/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}" if api_key else ""
                }
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": True,
                    "max_tokens": 256,
                    "temperature": 0.3
                }
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        err_body = await resp.aread()
                        raw_err = err_body.decode('utf-8', errors='ignore')
                        try:
                            err_json = json.loads(raw_err)
                            msg = err_json.get("error", {}).get("message", raw_err)
                        except Exception:
                            msg = raw_err
                        err_msg = f"[{provider.upper()} Error {resp.status_code}: {msg}]"
                        if not bypass_fallback and local_draft:
                            yield local_draft
                            return
                        yield err_msg
                        return
                    async for line in resp.aiter_lines():
                        chunk = self.parse_openai_sse_line(line)
                        if chunk:
                            yield chunk

        except Exception as e:
            logger.exception("Translation request failed")
            if self._client and self._client.is_closed:
                self._client = None
            if not bypass_fallback and local_draft:
                logger.info("Falling back to local offline draft translation.")
                yield local_draft
            else:
                yield f"[Lỗi kết nối AI ({provider}): {str(e)}]"

    async def translate_full(
        self,
        text: str,
        provider: Optional[str] = None,
        src_lang: str = "ja",
        tgt_lang: str = "vi",
        context: str = "",
        glossary_info: str = "",
        bypass_fallback: bool = False
    ) -> str:
        """Helper to get the full completed translation string."""
        accumulated = []
        async for chunk in self.translate_stream(text, provider, src_lang, tgt_lang, context, glossary_info, bypass_fallback=bypass_fallback):
            accumulated.append(chunk)
        raw_result = "".join(accumulated).strip()
        sanitized = self.sanitize_translation_output(raw_result)
        
        # Cache clean, successful translations
        if not bypass_fallback and sanitized and not sanitized.startswith("[Lỗi") and "Error" not in sanitized:
            if len(self._cache) >= self._max_cache_size:
                self._cache.pop(next(iter(self._cache)))
            self._cache[(text.strip(), src_lang, tgt_lang)] = sanitized
            
        return sanitized
