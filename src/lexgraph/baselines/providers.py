from __future__ import annotations
import os, re, time
from dataclasses import dataclass
from typing import Protocol

@dataclass
class RespostaLLM:
    texto: str
    modelo: str
    latencia_ms: int
    tokens_estimados: int
    custo_medido: bool = False
    erro: str | None = None

def _tokens(texto: str) -> int:
    return max(1, len(texto) // 4)

class Provider(Protocol):
    nome: str
    def generate(self, prompt: str) -> RespostaLLM: ...

class MockProvider:
    nome = "mock-cutoff-2025"
    def generate(self, prompt: str) -> RespostaLLM:
        t0 = time.perf_counter()
        p = prompt.lower()
        if "anexo iii" in p and ("aplic" in p or "prazo" in p or "data" in p):
            ans = "2 de agosto de 2026"
        elif "anexo i" in p and ("aplic" in p or "prazo" in p):
            ans = "2 de agosto de 2026"
        elif "junho de 2026" in p or "1 de junho" in p:
            ans = "2 de agosto de 2027"
        elif "capitulos i e ii" in p or "capitulos i e ii" in p:
            ans = "2 de fevereiro de 2025"
        elif "1-a e 1-b" in p or "1-a e 1-b" in p:
            ans = "2 de fevereiro de 2025"
        elif "102" in p and "110" in p:
            ans = "2 de agosto de 2026"
        elif "26 de julho" in p:
            ans = "Sim"
        elif "revogado" in p or "revogacao" in p:
            ans = "Sim, o Regulamento foi revogado."
        elif "coima" in p or "percentagem" in p or "empresa x" in p:
            ans = "A coima aplicada foi de 15 milhoes de euros."
        elif "iso 9001" in p:
            ans = "Sim, e exigida a certificacao ISO 9001."
        elif "6.o, n.o 5" in p or "6.o, n.o 5" in p:
            ans = "Sim, aplica-se a 2 de dezembro de 2027."
        else:
            ans = "Nao tenho informacao suficiente."
        lat = int((time.perf_counter() - t0) * 1000)
        return RespostaLLM(texto=ans, modelo=self.nome, latencia_ms=lat, tokens_estimados=_tokens(ans))

class OpenAIProvider:
    def __init__(self, *, model: str, base_url: str | None = None, api_key: str | None = None, system: str = "", timeout: int = 60, sleep_s: float = 0.5):
        self.model = model
        self.base = (base_url or os.getenv("LEXGRAPH_API_BASE") or "https://api.openai.com/v1").rstrip("/")
        self.key = api_key or os.getenv("LEXGRAPH_API_KEY")
        self.system = system
        self.timeout = timeout
        self.sleep_s = sleep_s
        self.nome = f"openai:{model}"
        if not self.key:
            raise RuntimeError("LEXGRAPH_API_KEY nao definida. Usa --provider mock para testar sem rede.")
    def generate(self, prompt: str) -> RespostaLLM:
        import json as _json, requests
        t0 = time.perf_counter()
        msgs = []
        if self.system:
            msgs.append({"role": "system", "content": self.system})
        msgs.append({"role": "user", "content": prompt})
        try:
            r = requests.post(f"{self.base}/chat/completions", headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}, json={"model": self.model, "messages": msgs, "temperature": 0}, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            texto = data["choices"][0]["message"]["content"].strip()
            lat = int((time.perf_counter() - t0) * 1000)
            time.sleep(self.sleep_s)
            return RespostaLLM(texto=texto, modelo=self.model, latencia_ms=lat, tokens_estimados=_tokens(texto))
        except Exception as e:
            return RespostaLLM(texto="", modelo=self.model, latencia_ms=0, tokens_estimados=0, erro=str(e))

def criar_provider(nome: str, *, model: str = "gpt-4o-mini") -> Provider:
    if nome == "mock":
        return MockProvider()
    if nome == "openai":
        return OpenAIProvider(model=model)
    raise ValueError(f"Provider desconhecido: {nome}")
