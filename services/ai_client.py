import httpx

from scripts.config import (
    NVIDIA_API_TIMEOUT_SECONDS,
    NVIDIA_BASE_URL,
    NVIDIA_CONNECT_TIMEOUT_SECONDS,
    NVIDIA_MAX_RETRIES,
)


def create_nvidia_client(api_key):
    # OpenAI istemcisi yalnızca AI çağrısı gerektiğinde yüklenir. Böylece
    # API anahtarı olmadan çalışan yerel dashboard ve deterministik chatbot
    # cevapları gereksiz bir bağımlılık hatası nedeniyle durmaz.
    from openai import OpenAI

    http_client = httpx.Client(
        trust_env=False,
        timeout=httpx.Timeout(
            timeout=NVIDIA_API_TIMEOUT_SECONDS,
            connect=NVIDIA_CONNECT_TIMEOUT_SECONDS,
        ),
    )

    return OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=api_key,
        timeout=NVIDIA_API_TIMEOUT_SECONDS,
        max_retries=NVIDIA_MAX_RETRIES,
        http_client=http_client,
    )
