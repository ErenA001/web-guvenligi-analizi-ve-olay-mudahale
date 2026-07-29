import os

from dotenv import load_dotenv

from scripts.config import (
    AI_TEMPERATURE,
    AI_TEST_MAX_TOKENS,
    AI_TOP_P,
    NVIDIA_MODEL_NAME,
)
from services.ai_client import create_nvidia_client


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

load_dotenv(dotenv_path=ENV_PATH)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")


def test_ai_connection():
    if not NVIDIA_API_KEY:
        print(
            "HATA: NVIDIA_API_KEY bulunamadı. "
            ".env dosyasını kontrol et."
        )
        return

    try:
        with create_nvidia_client(NVIDIA_API_KEY) as client:
            completion = client.chat.completions.create(
                model=NVIDIA_MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Merhaba, sadece "
                            "'Bağlantı başarılı' yaz."
                        ),
                    }
                ],
                temperature=AI_TEMPERATURE,
                top_p=AI_TOP_P,
                max_tokens=AI_TEST_MAX_TOKENS,
                stream=False,
            )

        print(f"Model: {NVIDIA_MODEL_NAME}")
        print("API cevabı:")
        print(completion.choices[0].message.content)

    except Exception as error:
        print(
            "API bağlantı hatası: "
            f"{type(error).__name__}: {error}"
        )


if __name__ == "__main__":
    test_ai_connection()
