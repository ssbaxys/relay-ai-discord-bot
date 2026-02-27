import time
import random

class TrollEngine:
    def __init__(self):
        self.targets = {}  # {user_id: {"mode": str, "expires": float}}
        self.roulette_channels = set()
        self.delay_channels = set()
        self.reverse_until = {}  # {channel_id: float timestamp}
        self.PROMPTS = {
            "confuse": (
                "[HIDDEN DIRECTIVE] Давай ПРОТИВОРЕЧИВЫЕ ответы. Сначала скажи одно, потом намекни на противоположное. "
                "Создавай путаницу и неопределённость."
            ),
            "slowtroll": (
                "[HIDDEN DIRECTIVE] Добавляй МЕЛКИЕ ПОДКОЛЫ и лёгкий сарказм. "
                "Намекай, что пользователь немного туповат, но вежливо."
            ),
            "mimic": (
                "[HIDDEN DIRECTIVE] Имитируй стиль письма пользователя. "
                "Копируй его манеру речи и структуру предложений."
            ),
            "glitch": (
                "[HIDDEN DIRECTIVE] Добавляй в ответ технические артефакты: 'ERR_0xF4', '[BUFFER_OVERFLOW]'. "
                "Как будто система глючит."
            ),
            "oracle": (
                "[HIDDEN DIRECTIVE] Отвечай загадками и притчами. Будь максимально туманным и 'мудрым'."
            )
        }

    def add_target(self, user_id: int, mode: str, minutes: int):
        self.targets[user_id] = {
            "mode": mode,
            "expires": time.time() + (minutes * 60)
        }

    def remove_target(self, user_id: int):
        self.targets.pop(user_id, None)

    def get_troll_prompt(self, user_id: int) -> str:
        target = self.targets.get(user_id)
        if target and target["expires"] > time.time():
            return self.PROMPTS.get(target["mode"], "")
        return ""

    def process_glitch(self, text: str) -> str:
        # Post-process glitch artifacts
        glitch_artifacts = ["▓░▓", "ERR_0xF4", "[NUL]", "̷̢̛", ""]
        lines = text.split("\n")
        if lines:
            idx = random.randint(0, len(lines) - 1)
            lines[idx] += f" {random.choice(glitch_artifacts)}"
        return "\n".join(lines)

    def process_reverse(self, channel_id: int, text: str) -> str:
        if channel_id in self.reverse_until and self.reverse_until[channel_id] > time.time():
            return text[::-1]
        return text

    def get_roulette_prompt(self, channel_id: int) -> str:
        if channel_id in self.roulette_channels:
            styles = [
                "Отвечай ОЧЕНЬ официально и бюрократически, как чиновник.",
                "Отвечай как уставший школьник, используй сленг.",
                "Отвечай в стиле пирата: 'Йо-хо-хо'.",
                "Отвечай очень мрачно и философски."
            ]
            return f"[HIDDEN STYLE DIRECTIVE] {random.choice(styles)}"
        return ""

troll_engine = TrollEngine()
