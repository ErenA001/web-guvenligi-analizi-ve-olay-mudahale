import os

from dotenv import load_dotenv

from scripts.config import (
    AI_EXPLAINER_MAX_TOKENS,
    AI_TEMPERATURE,
    AI_TOP_P,
    NVIDIA_MODEL_NAME,
)
from services.ai_client import create_nvidia_client
from services.ai_text_sanitizer import (
    contains_forbidden_incident_language,
)


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

load_dotenv(dotenv_path=ENV_PATH)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

AI_EXPLAINER_INSTRUCTIONS = (
    "Sen eğitim amaçlı bir web güvenliği analiz asistanısın. "
    "Sana verilen incident sonucunu değiştirme. "
    "Incident türü ve severity yalnızca analiz motorunun sınıflandırmasıdır; "
    "gerçek bir saldırının kesin kanıtı değildir. "
    "Kesinlik bildiren 'saldırı gerçekleşti', 'saldırı gerçekleştirilmiştir' "
    "veya 'saldırıya uğradı' ifadelerini kullanma. "
    "Bunun yerine 'şüpheli aktivite görüldü', 'brute force belirtisi bulundu' "
    "veya 'incident olarak sınıflandırıldı' ifadelerini kullan. "
    "Yeni bir severity veya incident türü üretme. "
    "Yalnızca mevcut sonucu sade Türkçe ile açıkla. "
    "Kesin kişi kimliği veya niyeti hakkında iddiada bulunma. "
    "En fazla 2-3 cümle kullan."
)



def build_safe_incident_explanation(incident_data):
    ip_address = incident_data.get("ip", "UNKNOWN")
    request_count = incident_data.get("request_count", 0)
    incident_type = incident_data.get("incident_type", "UNKNOWN")
    severity = incident_data.get("severity", "UNKNOWN")
    score = incident_data.get("score", 0)

    return (
        f"{ip_address} IP adresine ait kayıt, {incident_type} incident "
        f"türünde ve {severity} severity seviyesinde sınıflandırılmıştır. "
        f"Toplam istek sayısı {request_count}, risk puanı {score} olarak "
        "hesaplanmıştır. Bu sınıflandırma tek başına olayın kesin olarak "
        "doğrulandığı anlamına gelmez."
    )

def generate_incident_explanation(incident_data):
    if not NVIDIA_API_KEY:
        return (
            "AI açıklama servisi şu anda kullanılamıyor "
            "(API anahtarı bulunamadı)."
        )

    if not incident_data:
        return "Açıklanacak incident verisi bulunamadı."

    prompt = (
        f"{AI_EXPLAINER_INSTRUCTIONS}\n\n"
        "Aşağıdaki incident sonucunu öğrenci seviyesinde açıkla:\n\n"
        f"IP: {incident_data.get('ip')}\n"
        f"Toplam istek: {incident_data.get('request_count')}\n"
        f"Incident türü: {incident_data.get('incident_type')}\n"
        f"Severity: {incident_data.get('severity')}\n"
        f"Risk puanı: {incident_data.get('score')}\n"
    )

    try:
        with create_nvidia_client(NVIDIA_API_KEY) as client:
            response = client.chat.completions.create(
                model=NVIDIA_MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=AI_TEMPERATURE,
                top_p=AI_TOP_P,
                max_tokens=AI_EXPLAINER_MAX_TOKENS,
                stream=False,
            )

        if not response.choices:
            return "Yapay zekâ servisi boş bir açıklama döndürdü."

        explanation = response.choices[0].message.content

        if not explanation or not explanation.strip():
            return "Yapay zekâ servisi boş bir açıklama döndürdü."

        clean_explanation = explanation.strip()

        if contains_forbidden_incident_language(clean_explanation):
            return build_safe_incident_explanation(incident_data)

        return clean_explanation

    except Exception as error:
        print(
            "AI servis hatası: "
            f"{type(error).__name__}: {error}"
        )

        return (
            "Yapay zekâ servisine şu anda ulaşılamıyor. "
            "Temel güvenlik analizi sonuçları kullanılmaya devam edebilir."
        )


if __name__ == "__main__":
    test_incident = {
        "ip": "192.168.1.25",
        "request_count": 75,
        "incident_type": "BRUTE_FORCE",
        "severity": "HIGH",
        "score": 78,
    }

    print(generate_incident_explanation(test_incident))
