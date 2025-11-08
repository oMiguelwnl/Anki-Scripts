import time
from pathlib import Path
import requests
import re
import json
from typing import List, Optional
from dataclasses import dataclass, field
from glob import glob

# ======= CONFIGURAÇÕES =======
@dataclass
class Provider:
    name: str
    api_key: str
    api_url: str
    model: str
    rpm: int
    wait_seconds: int

@dataclass
class Config:
    input_pattern: str = "send*.md"  # padrão dos arquivos de entrada
    output_file: Path = Path("english_vocab.md")
    progress_file: Path = Path(".progress.json")

    providers: List[Provider] = field(default_factory=lambda: [
        Provider(
            name="groq",
            api_key="", #API KEY
            api_url="https://api.groq.com/openai/v1/chat/completions",
            model="llama-3.1-8b-instant",
            rpm=50,
            wait_seconds=65
        ),
        Provider(
            name="gemini",
            api_key="", # API KEY
            api_url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent",
            model="gemini-2.0-flash-exp",
            rpm=10,
            wait_seconds=60
        ),
        Provider(
            name="openrouter",
            api_key="", # API KEY
            api_url="https://openrouter.ai/api/v1/chat/completions",
            model="gpt-4o-mini",
            rpm=40,
            wait_seconds=70
        ),
    ])

    max_words: int = 200
    min_word_length: int = 3

config = Config()
# ====================================

class VocabGenerator:
    def __init__(self, config: Config):
        self.config = config
        self.processed_words = 0
        self.failed_words = []
        self.provider_index = 0
        self.last_request_time = {p.name: 0 for p in self.config.providers}
        self.provider_blocked_until = {p.name: 0 for p in self.config.providers}
        self.progress = self._load_progress()

    # ---------- Progresso ----------
    def _load_progress(self) -> dict:
        if self.config.progress_file.exists():
            try:
                return json.loads(self.config.progress_file.read_text())
            except:
                return {}
        return {}

    def _save_progress(self, file_name: str, last_word: str):
        self.progress["last_file"] = file_name
        self.progress["last_word"] = last_word
        with open(self.config.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, indent=2)

    # ---------- Extração ----------
    def extract_single_words(self, lines: List[str]) -> List[str]:
        words = []
        ignore_patterns = [r'^\d+$', r'^[^a-zA-Z]+$']
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if len(line.split()) == 1:
                w = re.sub(r'[^a-zA-Z-]', '', line).lower()
                if (w and len(w) >= self.config.min_word_length
                    and w.replace('-', '').isalpha()
                    and not any(re.match(p, w) for p in ignore_patterns)):
                    words.append(w)
        seen, unique = set(), []
        for w in words:
            if w not in seen:
                seen.add(w)
                unique.append(w)
        return unique[:self.config.max_words]

    # ---------- Controle de provedores ----------
    def _next_provider(self) -> Optional[Provider]:
        for _ in range(len(self.config.providers)):
            provider = self.config.providers[self.provider_index]
            self.provider_index = (self.provider_index + 1) % len(self.config.providers)
            if time.time() > self.provider_blocked_until[provider.name]:
                return provider
        return None

    def _wait_if_needed(self, provider: Provider):
        elapsed = time.time() - self.last_request_time[provider.name]
        delay = 60 / provider.rpm
        if elapsed < delay:
            time.sleep(delay - elapsed)

    # ---------- Prompt ----------
    def _create_prompt(self, word_cap: str) -> str:
        return f"""Create a vocabulary entry for the English word "{word_cap}":

## {word_cap}
**Signification**: [clear, concise English definition]
**Prononciation**: /IPA transcription/

**Exemple**:
- [Natural example sentence using "{word_cap}"]

Return ONLY this format, no extra text."""

    # ---------- Chamada aos provedores ----------
    def _call_provider(self, provider: Provider, prompt: str) -> Optional[str]:
        try:
            if provider.name == "groq":
                headers = {"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json"}
                data = {"model": provider.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3}
                resp = requests.post(provider.api_url, headers=headers, json=data, timeout=30)
                if resp.status_code == 200:
                    self.last_request_time[provider.name] = time.time()
                    return resp.json()["choices"][0]["message"]["content"]
                elif resp.status_code == 429:
                    print(f"⚠️ {provider.name} atingiu limite — alternando para outro provedor.")
                    self.provider_blocked_until[provider.name] = time.time() + provider.wait_seconds
                    return None
                else:
                    raise Exception(resp.text)

            elif provider.name == "gemini":
                url = f"{provider.api_url}?key={provider.api_key}"
                data = {"contents": [{"parts": [{"text": prompt}]}]}
                resp = requests.post(url, json=data, timeout=30)
                if resp.status_code == 200:
                    self.last_request_time[provider.name] = time.time()
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                elif resp.status_code == 429:
                    print(f"⚠️ {provider.name} atingiu limite — alternando para outro provedor.")
                    self.provider_blocked_until[provider.name] = time.time() + provider.wait_seconds
                    return None
                else:
                    raise Exception(resp.text)

            elif provider.name == "openrouter":
                headers = {"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json"}
                data = {"model": provider.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3}
                resp = requests.post(provider.api_url, headers=headers, json=data, timeout=30)
                if resp.status_code == 200:
                    self.last_request_time[provider.name] = time.time()
                    return resp.json()["choices"][0]["message"]["content"]
                elif resp.status_code == 429:
                    print(f"⚠️ {provider.name} atingiu limite — alternando para outro provedor.")
                    self.provider_blocked_until[provider.name] = time.time() + provider.wait_seconds
                    return None
                else:
                    raise Exception(resp.text)

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Erro de rede com {provider.name}: {e}")
            return None

    # ---------- Geração ----------
    def generate_vocab_entry(self, word: str, file_name: str) -> Optional[str]:
        word_cap = word.capitalize()
        prompt = self._create_prompt(word_cap)
        tries = 0
        max_tries = len(self.config.providers) * 2

        while tries < max_tries:
            provider = self._next_provider()
            if not provider:
                wait_time = min(max(0, self.provider_blocked_until[p.name] - time.time())
                                for p in self.config.providers)
                print(f"⏳ Todos os provedores bloqueados, aguardando {int(wait_time)}s...")
                time.sleep(wait_time + 1)
                continue

            try:
                self._wait_if_needed(provider)
                print(f"→ ({provider.name}) {word_cap}", end=" ")
                result = self._call_provider(provider, prompt)
                if result:
                    self._save_progress(file_name, word)
                    self.processed_words += 1
                    return result.strip() + "\n\n---\n\n"
                else:
                    tries += 1
            except Exception as e:
                print(f"⚠️ Erro com {provider.name}: {e}")
                tries += 1
                time.sleep(3)

        self.failed_words.append(word)
        return f"## {word_cap}\n**Signification**: [Definition missing]\n**Prononciation**: /.../\n\n**Exemple**:\n- Example with {word_cap}.\n\n---\n\n"

    # ---------- Execução principal ----------
    def run(self):
        start_time = time.time()
        files = sorted(glob(self.config.input_pattern))
        if not files:
            print(f"❌ Nenhum arquivo encontrado com padrão '{self.config.input_pattern}'.")
            return

        total_files = len(files)
        last_file = self.progress.get("last_file")
        last_word = self.progress.get("last_word")
        started = False

        for index, input_file in enumerate(files, 1):
            file_path = Path(input_file)
            lines = file_path.read_text(encoding="utf-8").splitlines()
            words = self.extract_single_words(lines)
            if not words:
                continue

            if last_file and file_path.name != last_file and not started:
                print(f"⏭️ Pulando {file_path.name} (já processado).")
                continue
            elif file_path.name == last_file and not started:
                started = True
                if last_word in words:
                    start_index = words.index(last_word) + 1
                    print(f"▶️ Retomando '{file_path.name}' a partir de '{last_word}'")
                else:
                    start_index = 0
            else:
                start_index = 0
                started = True

            words_to_process = words[start_index:]
            total_words = len(words_to_process)
            print(f"\n📘 ({index}/{total_files}) Processando arquivo: {file_path.name} ({total_words} palavras restantes)\n")

            if index == 1 and start_index == 0:
                with open(self.config.output_file, "w", encoding="utf-8") as f:
                    f.write("# English Vocabulary\n\n---\n\n")

            for word in words_to_process:
                entry = self.generate_vocab_entry(word, file_path.name)
                if entry:
                    with open(self.config.output_file, "a", encoding="utf-8") as f:
                        f.write(entry)
                    print("✅")
                else:
                    print("⏭️ ")

        # ---------- Resumo final ----------
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)
        hours, mins = divmod(mins, 60)
        duration = f"{hours}h {mins}m {secs}s" if hours else f"{mins}m {secs}s"

        print("\n✅ Finalizado!")
        print(f"📄 Salvo em: {self.config.output_file}")
        print(f"📂 Arquivos processados: {total_files}")
        print(f"📝 Palavras geradas com sucesso: {self.processed_words}")
        if self.failed_words:
            print(f"⚠️ Falhas: {len(self.failed_words)} → {self.failed_words}")
        print(f"⏱️ Tempo total: {duration}")


def main():
    VocabGenerator(config).run()


if __name__ == "__main__":
    main()
