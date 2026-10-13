"""
Mock response adapter with minimal PHI pattern checks. Non-mock provider names are not implemented.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Q Fever Serology Classifier"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock mode]: No language-model inference or clinical verification was performed. Query excerpt: '{prompt[:60]}...'"


class LLMFactory:
    """Returns the mock adapter; other provider labels currently fall back to the mock."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Q Fever Serology Classifier"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        elif prov in ["ollama", "local"]:
            return MockLLM(system_name)
        elif prov in ["claude", "anthropic"]:
            return MockLLM(system_name)
        elif prov in ["openai", "gpt4"]:
            return MockLLM(system_name)
        return MockLLM(system_name)
