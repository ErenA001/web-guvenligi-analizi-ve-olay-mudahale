import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")

if not api_key:
    print("HATA: NVIDIA_API_KEY bulunamadi. .env dosyasini kontrol et.")
else:
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )

    try:
        completion = client.chat.completions.create(
            model="deepseek-ai/deepseek-v4-pro",
            messages=[{"role": "user", "content": "Merhaba, sadece 'Baglanti basarili' yaz."}],
            temperature=0.5,
            max_tokens=50,
        )
        print("API cevabi:")
        print(completion.choices[0].message.content)
    except Exception as error:
        print("API baglanti hatasi:", error)
