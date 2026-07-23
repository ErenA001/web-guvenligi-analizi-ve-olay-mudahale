import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_NAME = "deepseek-ai/deepseek-v4-pro"

SYSTEM_PROMPT = (
    "Sen eğitim amaçlı bir web güvenliği analiz asistanısın. "
    "Sana verilen incident sonucunu değiştirme. "
    "Yeni bir severity veya incident türü üretme. "
    "Yalnızca mevcut sonucu sade Türkçe ile açıkla. "
    "Kesin saldırı gerçekleştiğini iddia etme. "
    "En fazla 2-3 cümle kullan."
)


def generate_incident_explanation(incident_data):
    if not NVIDIA_API_KEY:
        return "AI açıklama servisi şu anda kullanılamıyor (API anahtarı bulunamadı)."

    if not incident_data:
        return "Açıklanacak incident verisi bulunamadı."

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Aşağıdaki incident sonucunu öğrenci seviyesinde açıkla:\n\n"
        f"IP: {incident_data.get('ip')}\n"
        f"Toplam istek: {incident_data.get('request_count')}\n"
        f"Incident türü: {incident_data.get('incident_type')}\n"
        f"Severity: {incident_data.get('severity')}\n"
        f"Risk puanı: {incident_data.get('score')}\n"
    )

    try:
        client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI servis hatası: {type(e).__name__}: {e}")
        return "Yapay zekâ servisine şu anda ulaşılamıyor. Temel güvenlik analizi sonuçları kullanılmaya devam edebilir."


if __name__ == "__main__":
    test_incident = {
        "ip": "192.168.1.25",
        "request_count": 75,
        "incident_type": "BRUTE_FORCE",
        "severity": "HIGH",
        "score": 78,
    }
    print(generate_incident_explanation(test_incident))
