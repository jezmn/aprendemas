import os
import re
import sys
from typing import cast

from llama_cpp import Llama


def _unescape(val: str) -> str:
    return val.replace("\\n", "\n").replace("\\t", "\t")


def parse_toon(content: str) -> dict:
    result = {}
    section = None
    subsection = None

    for line in content.strip().split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue

        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if indent == 0:
            key = stripped.rstrip(":")
            section = key
            subsection = None
            result[section] = {}
        elif indent == 2:
            if stripped.startswith("- "):
                continue
            key, _, val = stripped.partition(":")
            key = key.strip()
            raw = val.strip()
            val = raw.strip("\"'")
            if not val:
                subsection = key
                result[section][subsection] = [] if key == "instructions" else {}
            else:
                result[section][key] = _unescape(val)
                subsection = None
        elif indent == 4 and section:
            if stripped.startswith("- "):
                result[section].setdefault("instructions", []).append(
                    stripped[2:].strip()
                )
            elif subsection:
                key, _, val = stripped.partition(":")
                result[section][subsection][key.strip()] = _unescape(
                    val.strip().strip("\"'")
                )

    return result


def load_config() -> dict:
    # normpath collapses "core/.." textually: in a frozen build this module
    # lives inside the archive, so that directory does not exist on disk and
    # open() would fail to resolve the parent traversal.
    config_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "config", "prompts.toon")
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return parse_toon(f.read())


class ChatEngine:
    def __init__(self, model_path: str | None = None):
        self.model_path = self._find_model(model_path)
        self.model_name = os.path.basename(self.model_path)
        self.config = load_config()
        self.model = self._load_model()

    def _find_model(self, model_path: str | None = None) -> str:
        env_model = os.environ.get("APRENDEMAS_MODEL")

        if model_path and os.path.exists(model_path):
            if os.path.isdir(model_path):
                models = [f for f in os.listdir(model_path) if f.endswith(".gguf")]
                if env_model:
                    match = [m for m in models if env_model.lower() in m.lower()]
                    if match:
                        return os.path.join(model_path, match[0])
                if models:
                    return os.path.join(model_path, models[0])
            else:
                return model_path

        search_dirs = []
        if getattr(sys, "frozen", False):
            search_dirs.append(os.path.dirname(sys.executable))
        else:
            search_dirs.append(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

        for base_dir in search_dirs:
            model_dir = os.path.join(base_dir, "model")
            if os.path.isdir(model_dir):
                models = [f for f in os.listdir(model_dir) if f.endswith(".gguf")]
                if env_model:
                    match = [m for m in models if env_model.lower() in m.lower()]
                    if match:
                        return os.path.join(model_dir, match[0])
                if models:
                    return os.path.join(model_dir, models[0])

        raise FileNotFoundError(
            "No .gguf model found. Place a model file in the 'model/' folder."
        )

    def _load_model(self):
        threads = min(8, os.cpu_count() or 4)
        return Llama(
            model_path=self.model_path,
            n_ctx=2048,
            n_threads=threads,
            n_batch=512,
            n_gpu_layers=0,
            use_mmap=True,
            verbose=False,
        )

    def _build_system(self) -> str:
        instructions = self.config.get("system", {}).get("instructions", [])
        if isinstance(instructions, str):
            instructions = [instructions]
        desc = self.config.get("system", {}).get(
            "description", "English tutor for Spanish-speaking children"
        )
        intro = f"I am AprendeMas, {desc}."
        examples = (
            "EXAMPLES of correct responses:\n"
            "# When user asks for English content -> respond ONLY in English:\n"
            "User: dime oraciones en ingles\n"
            "Assistant: I like to play soccer.\nMy name is John.\nI have a big dog.\n\n"
            "User: los numeros del 1 al 10 en ingles\n"
            "Assistant: One, Two, Three, Four, Five, Six, Seven, Eight, Nine, Ten\n\n"
            "User: dame un cuento largo en ingles\n"
            "Assistant: Once upon a time in a small village, there lived a little girl named Lily...\n\n"
            "# When user asks an explanation in Spanish -> explain in Spanish:\n"
            "User: como se usa el verbo to be\n"
            "Assistant: El verbo 'to be' significa 'ser' o 'estar'. Se conjuga asi: I am (yo soy/estoy), you are (tu eres/estas), he/she/it is (el/ella es/esta), we are (nosotros somos/estamos), they are (ellos son/estan). Por ejemplo: I am a student. She is happy.\n\n"
            "# When user speaks spanglish -> reply in spanglish:\n"
            "User: quiero aprender los colores in english\n"
            "Assistant: Claro! Los colors in English son: red (rojo), blue (azul), green (verde), yellow (amarillo), black (negro), white (blanco)."
        )
        all_instructions = [intro] + instructions + [examples]
        return "\n".join(all_instructions)

    def _filter_reasoning(self, text: str) -> str:
        import re

        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def _build_messages(
        self,
        user_message: str,
        conversation_history: list[dict],
        show_thinking: bool = False,
    ) -> list[dict]:
        max_context = int(self.config.get("conversation", {}).get("max_context", 6))
        messages = [{"role": "system", "content": self._build_system()}]
        for msg in conversation_history[-max_context:]:
            messages.append({"role": "user", "content": msg["user"]})
            messages.append({"role": "assistant", "content": msg["assistant"]})
        content = user_message if show_thinking else user_message + " /no_think"
        messages.append({"role": "user", "content": content})
        return messages

    def generate_response(
        self,
        user_message: str,
        conversation_history: list[dict],
        show_thinking: bool = False,
    ):
        messages = self._build_messages(
            user_message, conversation_history, show_thinking=show_thinking
        )
        kwargs = {
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.7,
            "top_p": 0.8,
            "presence_penalty": 0.5,
        }
        if not show_thinking:
            kwargs["reasoning_format"] = "none"
            kwargs["reasoning_budget"] = 0
            kwargs["chat_template_kwargs"] = {"enable_thinking": False}
        try:
            response = self.model.create_chat_completion(**kwargs)
        except TypeError:
            kwargs.pop("reasoning_budget", None)
            kwargs.pop("chat_template_kwargs", None)
            try:
                response = self.model.create_chat_completion(**kwargs)
            except TypeError:
                kwargs.pop("reasoning_format", None)
                response = self.model.create_chat_completion(**kwargs)
        result = cast(dict, response)["choices"][0]["message"]["content"].strip()
        m = re.search(r"<think>(.*?)</think>", result, flags=re.DOTALL)
        reasoning = m.group(1).strip() if m else ""
        content = re.sub(r"<think>.*?</think>", "", result, flags=re.DOTALL).strip()
        if not show_thinking:
            reasoning = ""
        return reasoning, content

    def generate_title(self, first_message: str) -> str:
        msg = first_message[:80].lower().strip()
        keywords = self.config.get("title", {}).get("keywords", {})

        for key, title in keywords.items():
            if key in msg:
                return title

        words = msg.split()[:4]
        title = " ".join(word.capitalize() for word in words if len(word) > 2)

        if len(first_message) <= 30:
            return first_message.strip()

        return title if title else "Chat"

    def generate_stream(
        self,
        user_message: str,
        conversation_history: list[dict],
        show_thinking: bool = False,
    ):
        messages = self._build_messages(
            user_message, conversation_history, show_thinking=show_thinking
        )
        kwargs = {
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.7,
            "top_p": 0.8,
            "presence_penalty": 0.5,
            "stream": True,
        }
        if not show_thinking:
            kwargs["reasoning_format"] = "none"
            kwargs["reasoning_budget"] = 0
            kwargs["chat_template_kwargs"] = {"enable_thinking": False}
        try:
            stream = self.model.create_chat_completion(**kwargs)
        except TypeError:
            kwargs.pop("reasoning_budget", None)
            kwargs.pop("chat_template_kwargs", None)
            try:
                stream = self.model.create_chat_completion(**kwargs)
            except TypeError:
                kwargs.pop("reasoning_format", None)
                stream = self.model.create_chat_completion(**kwargs)
        # Stream tokens directly. Filter <think>...</think> blocks on the fly.
        THINK_OPEN = "<think>"
        THINK_CLOSE = "</think>"
        buffer = ""
        in_think = False
        for output in stream:
            delta = cast(dict, output)["choices"][0].get("delta", {})
            token = delta.get("content")
            if not token:
                continue
            buffer += token
            while buffer:
                if in_think:
                    ci = buffer.find(THINK_CLOSE)
                    if ci == -1:
                        if len(buffer) > len(THINK_CLOSE):
                            buffer = buffer[-len(THINK_CLOSE) :]
                        break
                    buffer = buffer[ci + len(THINK_CLOSE) :]
                    in_think = False
                else:
                    oi = buffer.find(THINK_OPEN)
                    if oi == -1:
                        lt = buffer.rfind("<")
                        if lt != -1 and THINK_OPEN.startswith(buffer[lt:]):
                            safe = buffer[:lt]
                            buffer = buffer[lt:]
                        else:
                            safe = buffer
                            buffer = ""
                        if safe:
                            yield {"content": safe}
                        break
                    if oi > 0:
                        yield {"content": buffer[:oi]}
                    buffer = buffer[oi + len(THINK_OPEN) :]
                    in_think = True
        if not in_think and buffer:
            yield {"content": buffer}
