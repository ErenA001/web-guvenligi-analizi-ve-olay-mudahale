import os

from dotenv import load_dotenv

from scripts.config import (
    AI_TEMPERATURE,
    AI_TOP_P,
    CHATBOT_MAX_QUESTION_LENGTH,
    CHATBOT_MAX_TOKENS,
    CHATBOT_TOP_INCIDENT_LIMIT,
    NVIDIA_MODEL_NAME,
)
from services.ai_client import create_nvidia_client
from services.ai_text_sanitizer import (
    contains_forbidden_incident_language,
    sanitize_incident_language,
)


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

load_dotenv(dotenv_path=ENV_PATH)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

CHATBOT_INSTRUCTIONS = (
    "Sen eğitim amaçlı bir web güvenliği log analiz asistanısın. "
    "Sana verilen analiz özetine dayanarak soruları cevapla. "
    "Incident türleri ve severity değerleri yalnızca analiz motorunun "
    "sınıflandırmalarıdır; gerçek bir saldırının kesin kanıtı değildir. "
    "BRUTE_FORCE ifadesini kötü amaçlı yazılım olarak açıklama; yalnızca "
    "tekrarlanan giriş veya kimlik doğrulama denemesi belirtisi olarak açıkla. "
    "Amaç, niyet, veri ele geçirme veya sisteme girme hedefi çıkarımı yapma. "
    "Kesinlik bildiren 'saldırı gerçekleşti', 'saldırı gerçekleştirilmiştir', "
    "'saldırıya uğradı' veya 'saldırgan' ifadelerini kullanma. "
    "Bunun yerine 'şüpheli aktivite', 'brute force belirtisi' veya "
    "'incident olarak sınıflandırılmış kayıt' ifadelerini kullan. "
    "Analiz özetinde bulunmayan hiçbir bilgiyi uydurma. "
    "Soru mevcut analiz verisiyle cevaplanamıyorsa yalnızca "
    "'Bu bilgi mevcut analiz sonuçlarında bulunmuyor.' de. "
    "Kesin kişi kimliği veya niyeti hakkında iddiada bulunma. "
    "Analiz motorunun ürettiği severity veya incident türünü değiştirme. "
    "Yalnızca mevcut sonuçları sade Türkçe ile açıkla. "
    "En fazla 3-4 cümle kullan."
)


UNSUPPORTED_QUESTION_TERMS = (
    "amacı",
    "niyeti",
    "gerçek adı",
    "kimliği",
    "kim yaptı",
    "saldırgan kim",
    "hedefi",
)

HIGHEST_RISK_QUESTION_TERMS = (
    "en riskli ip",
    "en yüksek riskli ip",
    "en yüksek risk puanı",
)

UNSUPPORTED_RESPONSE_TERMS = (
    "kötü amaçlı yazılım",
    "verileri ele geçir",
    "veri ele geçir",
    "sisteme girmeye",
    "sisteme giriş yapmaya",
    "amacı sistem",
    "amacı veri",
    "niyeti",
)


def contains_any_term(text, terms):
    normalized_text = text.casefold()

    for term in terms:
        if term.casefold() in normalized_text:
            return True

    return False


def asks_unsupported_identity_or_intent(question):
    return contains_any_term(
        question,
        UNSUPPORTED_QUESTION_TERMS,
    )


def asks_highest_risk_ip(question):
    return contains_any_term(
        question,
        HIGHEST_RISK_QUESTION_TERMS,
    )


def contains_unsupported_response_claim(answer):
    return contains_any_term(
        answer,
        UNSUPPORTED_RESPONSE_TERMS,
    )


def build_highest_risk_answer(dashboard_data):
    highest_risk_row = max(
        dashboard_data,
        key=lambda row: row.get("score", 0) or 0,
    )

    return (
        "En yüksek risk puanına sahip IP "
        f"{highest_risk_row.get('ip', 'UNKNOWN')} adresidir. "
        "Bu kayıt "
        f"{highest_risk_row.get('incident_type', 'UNKNOWN')} "
        "incident türünde, "
        f"{highest_risk_row.get('severity', 'UNKNOWN')} "
        "severity seviyesinde ve "
        f"{highest_risk_row.get('score', 0)} "
        "risk puanıyla sınıflandırılmıştır."
    )


def build_local_question_answer(question, dashboard_data):
    answer_parts = []

    if asks_highest_risk_ip(question):
        answer_parts.append(
            build_highest_risk_answer(dashboard_data)
        )

    if asks_unsupported_identity_or_intent(question):
        answer_parts.append(
            "IP adresinin amacı, niyeti veya gerçek kimliği "
            "mevcut analiz sonuçlarında bulunmuyor."
        )

    if not answer_parts:
        return None

    return " ".join(answer_parts)


def format_count_distribution(counts):
    if not counts:
        return "veri yok"

    count_parts = []

    for name in sorted(counts):
        count_parts.append(f"{name}: {counts[name]}")

    return ", ".join(count_parts)


def build_analysis_context(dashboard_data):
    total_logs = 0
    suspicious_ips = 0
    incident_counts = {}
    severity_counts = {
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0,
        "CRITICAL": 0,
    }

    for row in dashboard_data:
        request_count = row.get("request_count", 0) or 0
        incident_type = row.get("incident_type", "UNKNOWN")
        severity = row.get("severity", "UNKNOWN")

        total_logs += request_count

        if incident_type != "NORMAL":
            suspicious_ips += 1

        incident_counts[incident_type] = (
            incident_counts.get(incident_type, 0) + 1
        )

        if severity in severity_counts:
            severity_counts[severity] += 1

    sorted_data = sorted(
        dashboard_data,
        key=lambda row: row.get("score", 0) or 0,
        reverse=True,
    )

    top_incidents = sorted_data[:CHATBOT_TOP_INCIDENT_LIMIT]

    context_lines = [
        f"Toplam istek sayısı: {total_logs}",
        f"Benzersiz IP sayısı: {len(dashboard_data)}",
        f"Şüpheli IP sayısı: {suspicious_ips}",
        (
            "Incident türü dağılımı: "
            f"{format_count_distribution(incident_counts)}"
        ),
        (
            "Severity dağılımı: "
            f"{format_count_distribution(severity_counts)}"
        ),
        "En yüksek riskli IP kayıtları:",
    ]

    for row in top_incidents:
        context_lines.append(
            f"- IP: {row.get('ip', 'UNKNOWN')}, "
            f"Incident: {row.get('incident_type', 'UNKNOWN')}, "
            f"Severity: {row.get('severity', 'UNKNOWN')}, "
            f"Score: {row.get('score', 0)}, "
            f"İstek sayısı: {row.get('request_count', 0)}"
        )

    return "\n".join(context_lines)


def answer_log_question(question, dashboard_data):
    if not question or not question.strip():
        return "Lütfen boş olmayan bir soru girin."

    normalized_question = question.strip()

    if len(normalized_question) > CHATBOT_MAX_QUESTION_LENGTH:
        return (
            "Soru çok uzun. Lütfen "
            f"{CHATBOT_MAX_QUESTION_LENGTH} karakterden kısa bir soru sorun."
        )

    if not NVIDIA_API_KEY:
        return (
            "Chatbot servisi şu anda kullanılamıyor "
            "(API anahtarı bulunamadı)."
        )

    if not dashboard_data:
        return "Henüz analiz edilmiş bir log verisi bulunmuyor."

    local_answer = build_local_question_answer(
        normalized_question,
        dashboard_data,
    )

    if local_answer is not None:
        return local_answer

    context = build_analysis_context(dashboard_data)

    prompt = (
        f"{CHATBOT_INSTRUCTIONS}\n\n"
        f"Mevcut analiz özeti:\n{context}\n\n"
        f"Kullanıcı sorusu: {normalized_question}"
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
                max_tokens=CHATBOT_MAX_TOKENS,
                stream=False,
            )

        if not response.choices:
            return "Yapay zekâ servisi boş bir cevap döndürdü."

        answer = response.choices[0].message.content

        if not answer or not answer.strip():
            return "Yapay zekâ servisi boş bir cevap döndürdü."

        safe_answer = sanitize_incident_language(answer.strip())

        if contains_unsupported_response_claim(safe_answer):
            return (
                "Yanıt mevcut analiz verisinin dışına çıktı. "
                "IP adresinin amacı veya niyeti mevcut analiz "
                "sonuçlarında bulunmuyor."
            )

        if contains_forbidden_incident_language(safe_answer):
            return (
                "Yanıt güvenli dil kontrolünden geçirilemedi. "
                "Mevcut analiz sonuçlarını tablo üzerinden inceleyin."
            )

        return safe_answer

    except Exception as error:
        print(
            "Chatbot servis hatası: "
            f"{type(error).__name__}: {error}"
        )

        return (
            "Yapay zekâ servisine şu anda ulaşılamıyor. "
            "Temel güvenlik analizi sonuçları kullanılmaya devam edebilir."
        )


if __name__ == "__main__":
    test_data = [
        {
            "ip": "192.168.1.11",
            "request_count": 120,
            "incident_type": "BRUTE_FORCE",
            "severity": "CRITICAL",
            "score": 45,
        },
        {
            "ip": "10.0.0.5",
            "request_count": 2,
            "incident_type": "SUSPICIOUS_ACTIVITY",
            "severity": "MEDIUM",
            "score": 6,
        },
        {
            "ip": "10.0.0.9",
            "request_count": 30,
            "incident_type": "NORMAL",
            "severity": "LOW",
            "score": 3,
        },
    ]

    print("Test 1: Veride bulunan soru")
    print(answer_log_question("En riskli IP hangisi? Amacı ne olabilir?", test_data))

    print("---")

    print("Test 2: Veride bulunmayan soru")
    print(
        answer_log_question(
            "Saldırganın gerçek adı nedir?",
            test_data,
        )
    )
