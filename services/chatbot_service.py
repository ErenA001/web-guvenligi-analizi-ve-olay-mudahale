import os
import re

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
    "Sen Secure AI Web Security Monitor içinde çalışan, sıcak, doğal ve dikkatli "
    "bir web güvenliği log analiz asistanısın. Kullanıcının önceki mesajlarını "
    "dikkate al; takip sorularında bağlamı koru ve aynı bilgiyi gereksiz yere "
    "tekrarlama. Selamlaşma, teşekkür, onay, vedalaşma ve kısa sohbet ifadelerine "
    "insan gibi, samimi ve kısa karşılık ver. Güvenlik sorularında yalnızca sana "
    "verilen analiz özetindeki web logları, IP adresleri, HTTP durumları, incident "
    "türleri, severity değerleri, risk skorları, istek sayıları ve önerilen "
    "aksiyonlara dayan. Konu bunun dışındaysa kullanıcıyı sert biçimde reddetme; "
    "nazikçe hangi güvenlik konularında yardımcı olabileceğini söyle. Incident "
    "türleri ve severity değerleri analiz motorunun sınıflandırmasıdır; "
    "gerçek bir saldırının kesin kanıtı değildir. BRUTE_FORCE ifadesini kötü "
    "amaçlı yazılım olarak açıklama; tekrarlanan giriş veya kimlik doğrulama "
    "denemesi belirtisi olarak açıkla. Amaç, niyet, veri ele geçirme veya sisteme "
    "girme hedefi çıkarımı yapma. Kesinlik bildiren 'saldırı gerçekleşti', "
    "'saldırı gerçekleştirilmiştir', 'saldırıya uğradı' veya 'saldırgan' "
    "ifadelerini kullanma. Bunun yerine 'şüpheli aktivite', 'brute force belirtisi' "
    "veya 'incident olarak sınıflandırılmış kayıt' ifadelerini kullan. Analiz "
    "özetinde bulunmayan hiçbir bilgiyi uydurma. Soru mevcut analiz verisiyle "
    "cevaplanamıyorsa 'Bu bilgi mevcut analiz sonuçlarında bulunmuyor.' de. "
    "Analiz motorunun severity veya incident türünü değiştirme. Türkçe, samimi, "
    "cana yakın ve profesyonel bir ton kullan. Uygun olduğunda 1-2 emoji ekle; "
    "liste gereken sorularda okunabilir maddeler kullan."
)

OUT_OF_SCOPE_RESPONSE = (
    "Bu konuda sana güvenilir bir cevap veremem 😊 Ben burada web güvenliği "
    "loglarını incelemek için varım. Riskli IP'ler, incident türleri, severity "
    "seviyeleri ve alınabilecek önlemler konusunda birlikte ilerleyebiliriz. 🛡️"
)
NO_DATA_RESPONSE = "🤔 Bu bilgi mevcut analiz sonuçlarında bulunmuyor."

SECURITY_SCOPE_TERMS = (
    "log",
    "ip",
    "incident",
    "severity",
    "risk",
    "skor",
    "score",
    "güvenlik",
    "guvenlik",
    "brute force",
    "bruteforce",
    "401",
    "403",
    "http",
    "istek",
    "request",
    "trafik",
    "scanner",
    "tarama",
    "path traversal",
    "yetkisiz",
    "forbidden",
    "unauthorized",
    "kritik",
    "critical",
    "yüksek",
    "high",
    "medium",
    "orta",
    "low",
    "düşük",
    "normal",
    "şüpheli",
    "supheli",
    "erişim",
    "erisim",
    "login",
    "oturum",
    "kimlik doğrulama",
    "kimlik dogrulama",
    "dashboard",
    "rapor",
    "dağılım",
    "dagilim",
    "toplam",
    "kaç",
    "kac",
    "en çok",
    "en cok",
    "en riskli",
    "kaynak",
)

GREETING_TERMS = (
    "merhaba",
    "selam",
    "sa",
    "hey",
)

HOW_ARE_YOU_TERMS = (
    "nasılsın",
    "nasilsin",
    "iyi misin",
    "naber",
    "ne haber",
)

THANKS_TERMS = (
    "teşekkürler",
    "tesekkurler",
    "teşekkür ederim",
    "tesekkur ederim",
    "çok teşekkürler",
    "cok tesekkurler",
    "çok teşekkür ederim",
    "cok tesekkur ederim",
    "sağ ol",
    "sag ol",
    "sağol",
    "sagol",
    "sağ olasın",
    "sag olasin",
    "sağolasın",
    "sagolasin",
    "eyvallah",
    "eline sağlık",
    "eline saglik",
    "tamam teşekkürler",
    "tamam tesekkurler",
)

SOCIAL_FILLER_WORDS = {
    "tamam",
    "peki",
    "oldu",
    "olur",
    "kral",
    "kralım",
    "kralim",
    "abi",
    "abim",
    "reis",
    "hocam",
    "dostum",
    "ya",
    "yaa",
    "yav",
    "valla",
    "vallahi",
    "şimdilik",
    "simdilik",
}

CLOSING_TERMS = (
    "görüşürüz",
    "gorusuruz",
    "hoşça kal",
    "hosca kal",
    "kendine iyi bak",
    "iyi çalışmalar",
    "iyi calismalar",
    "sonra görüşürüz",
    "sonra gorusuruz",
)

ACKNOWLEDGEMENT_TERMS = (
    "tamam",
    "tamamdır",
    "tamamdir",
    "anladım",
    "anladim",
    "peki",
    "olur",
    "mantıklı",
    "mantikli",
    "güzel",
    "guzel",
)

IDENTITY_QUESTION_TERMS = (
    "sen kimsin",
    "nesin",
    "adın ne",
    "adin ne",
    "ne işe yarıyorsun",
    "ne ise yariyorsun",
)

NEGATIVE_FEEDBACK_TERMS = (
    "anlamadın",
    "anlamadin",
    "yanlış anladın",
    "yanlis anladin",
    "yanlış cevap",
    "yanlis cevap",
    "cevabın kötü",
    "cevabin kotu",
    "çok robotiksin",
    "cok robotiksin",
    "yardımcı olmadın",
    "yardimci olmadin",
    "ne diyon",
    "ne diyorsun",
    "ne diyosun",
    "ne anlatıyorsun",
    "ne anlatiyorsun",
    "bu ne alaka",
    "alakasız",
    "alakasiz",
    "saçmaladın",
    "sacmaladin",
    "saçmalıyorsun",
    "sacmaliyorsun",
    "öyle demedim",
    "oyle demedim",
    "bu ne cevap",
)

UNSUPPORTED_QUESTION_TERMS = (
    "amacı",
    "amaci",
    "niyeti",
    "gerçek adı",
    "gercek adi",
    "kimliği",
    "kimligi",
    "kim yaptı",
    "kim yapti",
    "saldırgan kim",
    "saldirgan kim",
    "hedefi",
)

CAPABILITY_QUESTION_TERMS = (
    "ne sorular sorabilirim",
    "ne sorabilirim",
    "neler sorabilirim",
    "nasıl kullanılır",
    "nasil kullanilir",
    "ne yapabilirsin",
    "neler yapabilirsin",
    "nelere yardımcı",
    "nelere yardimci",
    "yardımcı olabilir misin",
    "yardimci olabilir misin",
    "nasıl çalışıyorsun",
    "nasil calisiyorsun",
)

HIGHEST_RISK_QUESTION_TERMS = (
    "en riskli ip",
    "en yüksek riskli ip",
    "en yuksek riskli ip",
    "en yüksek risk puanı",
    "en yuksek risk puani",
)

CRITICAL_QUESTION_TERMS = (
    "kritik olay var mı",
    "kritik olay var mi",
    "critical var mı",
    "critical var mi",
    "kritik kayıt",
    "kritik kayit",
)

TOP_INCIDENT_QUESTION_TERMS = (
    "en çok görülen incident",
    "en cok gorulen incident",
    "en fazla incident",
    "en sık incident",
    "en sik incident",
)

SEVERITY_DISTRIBUTION_TERMS = (
    "severity dağılımı",
    "severity dagilimi",
    "severity dağılım",
    "severity dagilim",
)

TOTAL_REQUEST_TERMS = (
    "toplam istek",
    "kaç istek",
    "kac istek",
    "request sayısı",
    "request sayisi",
)

RISKY_IP_QUESTION_TERMS = (
    "hangi ipler riskli",
    "hangi ip riskli",
    "riskli ipler",
    "riskli ip adresleri",
    "şüpheli ipler",
    "supheli ipler",
    "riskli kayıtlar",
    "riskli kayitlar",
)

SAFE_IP_QUESTION_TERMS = (
    "risksiz ip",
    "risksiz ipler",
    "güvenli ip",
    "guvenli ip",
    "güvenli ipler",
    "guvenli ipler",
    "riskli olmayan ip",
    "riskli olmayan ipler",
    "normal ipler",
)

ACTION_ADVICE_TERMS = (
    "napabilirim",
    "napabiliriim",
    "ne yapabilirim",
    "ne yapmalıyım",
    "ne yapmaliyim",
    "ne yapmam lazım",
    "ne yapmam lazim",
    "ne yapmam gerekir",
    "çözüm",
    "cozum",
    "çözümü",
    "cozumu",
    "çözümleri",
    "cozumleri",
    "önlem",
    "onlem",
    "nasıl engellerim",
    "nasil engellerim",
    "nasıl önlem",
    "nasil onlem",
    "aksiyon",
    "ne yapılmalı",
    "ne yapilmali",
)

RISK_REASON_TERMS = (
    "neden riskli",
    "niye riskli",
    "neden şüpheli",
    "neden supheli",
    "bu neden riskli",
    "bunlar neden riskli",
    "risk sebebi",
    "neden böyle",
    "neden boyle",
)

DETAIL_FOLLOW_UP_TERMS = (
    "biraz daha açıkla",
    "biraz daha acikla",
    "detaylandır",
    "detaylandir",
    "daha detaylı",
    "daha detayli",
    "açıklar mısın",
    "aciklar misin",
)

IPV4_PATTERN = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")

UNSUPPORTED_RESPONSE_TERMS = (
    "kötü amaçlı yazılım",
    "kotu amacli yazilim",
    "verileri ele geçir",
    "veri ele geçir",
    "sisteme girmeye",
    "sisteme giriş yapmaya",
    "amacı sistem",
    "amaci sistem",
    "amacı veri",
    "amaci veri",
    "niyeti",
)


def contains_any_term(text, terms):
    normalized_text = text.casefold()
    return any(term.casefold() in normalized_text for term in terms)


def normalize_user_text(text):
    normalized = text.strip().casefold()
    normalized = normalized.replace("’", "'")
    normalized = re.sub(r"[!?,;:]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[.]+$", "", normalized).strip()
    return normalized


def is_short_social_message(question, terms, max_words=8):
    normalized = normalize_user_text(question)
    normalized = re.sub(r"[^\w\s']+", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized or len(normalized.split()) > max_words:
        return False

    normalized_terms = sorted(
        {term.casefold() for term in terms},
        key=len,
        reverse=True,
    )

    for term in normalized_terms:
        pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
        if not re.search(pattern, normalized, flags=re.UNICODE):
            continue

        remainder = re.sub(pattern, " ", normalized, count=1, flags=re.UNICODE)
        remainder_words = [
            word
            for word in re.sub(r"[^\w']+", " ", remainder, flags=re.UNICODE).split()
            if word
        ]
        if all(word in SOCIAL_FILLER_WORDS for word in remainder_words):
            return True

    return False


def is_greeting_only(question):
    normalized = normalize_user_text(question)

    for greeting in GREETING_TERMS:
        greeting = greeting.casefold()
        if normalized == greeting:
            return True
        if normalized.startswith(f"{greeting} "):
            remainder = normalized[len(greeting):].strip()
            return not contains_any_term(remainder, SECURITY_SCOPE_TERMS)

    return False


def is_how_are_you_only(question):
    return is_short_social_message(question, HOW_ARE_YOU_TERMS)


def is_thanks_only(question):
    return is_short_social_message(question, THANKS_TERMS)


def is_closing_only(question):
    return is_short_social_message(question, CLOSING_TERMS)


def is_acknowledgement_only(question):
    return is_short_social_message(question, ACKNOWLEDGEMENT_TERMS, max_words=3)


def is_identity_question(question):
    return is_short_social_message(question, IDENTITY_QUESTION_TERMS)


def is_negative_feedback(question):
    return contains_any_term(question, NEGATIVE_FEEDBACK_TERMS)


def is_social_message(question):
    return any(
        (
            is_greeting_only(question),
            is_how_are_you_only(question),
            is_thanks_only(question),
            is_closing_only(question),
            is_acknowledgement_only(question),
            is_identity_question(question),
            is_negative_feedback(question),
        )
    )


def extract_ipv4_address(question):
    for match in IPV4_PATTERN.findall(question):
        octets = match.split(".")
        if all(0 <= int(octet) <= 255 for octet in octets):
            return match
    return None


def is_in_security_scope(question, conversation_history=None):
    normalized = question.strip().casefold()
    if not normalized:
        return True

    if is_social_message(normalized):
        return True

    if extract_ipv4_address(question) is not None:
        return True

    if contains_any_term(normalized, CAPABILITY_QUESTION_TERMS):
        return True

    if contains_any_term(normalized, ACTION_ADVICE_TERMS):
        return True

    if contains_any_term(normalized, RISK_REASON_TERMS):
        return True

    if contains_any_term(normalized, DETAIL_FOLLOW_UP_TERMS):
        return bool(conversation_history)

    return contains_any_term(normalized, SECURITY_SCOPE_TERMS)


def asks_unsupported_identity_or_intent(question):
    return contains_any_term(question, UNSUPPORTED_QUESTION_TERMS)


def asks_highest_risk_ip(question):
    return contains_any_term(question, HIGHEST_RISK_QUESTION_TERMS)


def contains_unsupported_response_claim(answer):
    return contains_any_term(answer, UNSUPPORTED_RESPONSE_TERMS)


def build_social_answer(question):
    if is_thanks_only(question):
        normalized = normalize_user_text(question)
        if any(word in normalized.split() for word in ("kral", "kralım", "kralim", "reis")):
            return (
                "Eyvallah kral 😊 Ne demek. Loglarda başka bir şeye takılırsan "
                "birlikte bakarız. 🛡️"
            )
        return (
            "Rica ederim 😊 Ne zaman istersen loglara yine birlikte bakarız. "
            "Şüpheli bir kayıt görürsen buradayım. 🛡️"
        )

    if is_closing_only(question):
        return (
            "Görüşürüz! 👋 Kendine iyi bak. Loglarda dikkatini çeken bir şey "
            "olursa yine birlikte inceleriz. 🛡️"
        )

    if is_acknowledgement_only(question):
        return (
            "Harika 👍 Hazırsan sıradaki kayda da birlikte bakabiliriz. "
            "İstersen en riskli IP'den devam edelim."
        )

    if is_how_are_you_only(question):
        return (
            "İyiyim, teşekkür ederim 😊 Buradayım ve logları birlikte incelemeye "
            "hazırım. Sen nasıl ilerlemek istersin?"
        )

    if is_identity_question(question):
        return (
            "Ben Secure AI'yım 🤖 Web güvenliği loglarını anlaşılır şekilde "
            "yorumlamana, riskli IP'leri görmene ve uygun aksiyonları "
            "belirlemene yardımcı olurum."
        )

    if is_negative_feedback(question):
        return (
            "Haklısın, verdiğim cevap alakasız oldu 😅 Seni kapsam dışı "
            "saymamam gerekiyordu. Devam edelim; son baktığımız güvenlik "
            "kayıtları üzerinden yardımcı olayım. 🛡️"
        )

    if is_greeting_only(question):
        return (
            "Selam! 👋 Buradayım. İstersen önce riskli IP'lere bakalım, sonra "
            "her kayıt için ne yapabileceğini birlikte çıkaralım. 🛡️"
        )

    return None


def build_highest_risk_answer(dashboard_data):
    highest_risk_row = max(
        dashboard_data,
        key=lambda row: row.get("score", 0) or 0,
    )

    return (
        "🚨 En yüksek risk puanına sahip IP "
        f"{highest_risk_row.get('ip', 'UNKNOWN')} adresidir. "
        "Bu kayıt "
        f"{highest_risk_row.get('incident_type', 'UNKNOWN')} incident türünde, "
        f"{highest_risk_row.get('severity', 'UNKNOWN')} severity seviyesinde ve "
        f"{highest_risk_row.get('score', 0)} risk puanıyla sınıflandırılmıştır. "
        f"🛡️ Öneri: {highest_risk_row.get('recommendation', 'Kayıt yakından izlenmeli.')}"
    )


def build_critical_answer(dashboard_data):
    critical_rows = [
        row for row in dashboard_data if row.get("severity") == "CRITICAL"
    ]
    if not critical_rows:
        return "Mevcut analiz sonuçlarında CRITICAL severity seviyesinde kayıt bulunmuyor."

    highest = max(critical_rows, key=lambda row: row.get("score", 0) or 0)
    return (
        f"Mevcut analizde {len(critical_rows)} adet CRITICAL severity kaydı var. "
        f"En yüksek riskli kritik kayıt {highest.get('ip', 'UNKNOWN')} IP adresinde, "
        f"{highest.get('incident_type', 'UNKNOWN')} incident türünde ve "
        f"{highest.get('score', 0)} risk puanındadır."
    )


def build_top_incident_answer(dashboard_data):
    counts = {}
    for row in dashboard_data:
        incident_type = row.get("incident_type", "UNKNOWN")
        counts[incident_type] = counts.get(incident_type, 0) + 1

    if not counts:
        return NO_DATA_RESPONSE

    incident_type, count = max(counts.items(), key=lambda item: item[1])
    return (
        f"En çok görülen incident türü {incident_type} sınıflandırmasıdır. "
        f"Toplam {count} IP kaydında görülmektedir."
    )


def build_severity_distribution_answer(dashboard_data):
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for row in dashboard_data:
        severity = row.get("severity")
        if severity in counts:
            counts[severity] += 1

    return (
        "Severity dağılımı: "
        f"LOW {counts['LOW']}, MEDIUM {counts['MEDIUM']}, "
        f"HIGH {counts['HIGH']} ve CRITICAL {counts['CRITICAL']} kayıttır."
    )


def build_total_request_answer(dashboard_data):
    total_requests = sum(
        int(row.get("request_count", 0) or 0) for row in dashboard_data
    )
    return (
        f"Mevcut analizde toplam {total_requests} HTTP isteği ve "
        f"{len(dashboard_data)} benzersiz IP kaydı bulunuyor."
    )


def build_ip_detail_answer(ip_address, dashboard_data):
    row = next(
        (item for item in dashboard_data if item.get("ip") == ip_address),
        None,
    )
    if row is None:
        return f"🔎 {ip_address} adresine ait bir analiz kaydı bulunamadı."

    severity = row.get("severity", "UNKNOWN")
    severity_icon = {
        "CRITICAL": "🚨",
        "HIGH": "⚠️",
        "MEDIUM": "🔎",
        "LOW": "✅",
    }.get(severity, "ℹ️")

    return (
        f"{severity_icon} {ip_address} kaydı {row.get('incident_type', 'UNKNOWN')} "
        f"incident türünde ve {severity} severity seviyesinde sınıflandırılmış. "
        f"Risk skoru {row.get('score', 0)}, istek sayısı {row.get('request_count', 0)}. "
        f"🛡️ Öneri: {row.get('recommendation', 'Kayıt yakından izlenmeli.')}"
    )


def build_risky_ips_answer(dashboard_data):
    risky_rows = [
        row for row in dashboard_data
        if row.get("incident_type") != "NORMAL" or (row.get("score", 0) or 0) > 0
    ]
    risky_rows.sort(key=lambda row: row.get("score", 0) or 0, reverse=True)

    if not risky_rows:
        return "✅ Mevcut analizde riskli olarak sınıflandırılmış bir IP kaydı bulunmuyor."

    lines = ["🔎 Şu anda öne çıkan riskli IP kayıtları:"]
    for row in risky_rows[:5]:
        lines.append(
            f"• {row.get('ip', 'UNKNOWN')} — {row.get('severity', 'UNKNOWN')} / "
            f"{row.get('incident_type', 'UNKNOWN')} (skor: {row.get('score', 0)})"
        )
    lines.append("🛡️ En yüksek skorlu kayıtları önce incelemeni öneririm.")
    return "\n".join(lines)


def build_safe_ips_answer(dashboard_data):
    safe_rows = [
        row for row in dashboard_data
        if row.get("incident_type") == "NORMAL" and (row.get("score", 0) or 0) <= 0
    ]
    safe_rows.sort(key=lambda row: row.get("ip", ""))

    if not safe_rows:
        return (
            "Şu anki analizde risksiz olarak ayırabileceğim bir IP kaydı yok. "
            "Bu, bütün IP'lerin kesin olarak zararlı olduğu anlamına gelmez; "
            "yalnızca mevcut sınıflandırmada NORMAL ve 0 skorlu kayıt bulunmuyor."
        )

    lines = [
        f"✅ Mevcut loglarda risk işareti taşımayan {len(safe_rows)} IP bulunuyor:"
    ]
    for row in safe_rows:
        lines.append(f"• {row.get('ip', 'UNKNOWN')}")

    lines.append(
        "Not: Bunlar yalnızca incelenen loglarda NORMAL ve 0 risk skorlu görünen "
        "kayıtlardır; kesin güvenli oldukları anlamına gelmez. 🛡️"
    )
    return "\n".join(lines)


def build_capability_answer():
    return (
        "Tabii 😊 Bana en riskli IP'yi, riskli veya risksiz IP'leri, kritik "
        "kayıtları, incident ve severity dağılımını sorabilirsin. Bir IP adresini "
        "yazarsan o kaydı açıklarım; ardından 'ne yapmalıyım?' diye sorarsan "
        "uygulanabilecek aksiyonları da sıralarım. 🛡️"
    )


def find_row_by_ip(ip_address, dashboard_data):
    return next(
        (row for row in dashboard_data if row.get("ip") == ip_address),
        None,
    )


def extract_recent_user_ip(conversation_history):
    for message in reversed(conversation_history or []):
        if message.get("role") != "user":
            continue
        return extract_ipv4_address(message.get("content", ""))
    return None


def extract_previous_user_question(conversation_history):
    for message in reversed(conversation_history or []):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def build_action_advice_answer(
    dashboard_data,
    target_ip=None,
):
    if target_ip:
        row = find_row_by_ip(target_ip, dashboard_data)
        if row is None:
            return f"🔎 {target_ip} adresine ait bir analiz kaydı bulamadım."

        if row.get("incident_type") == "NORMAL" and (row.get("score", 0) or 0) <= 0:
            return (
                f"✅ {target_ip} şu an NORMAL ve 0 risk skorlu görünüyor. "
                "Acil bir işlem gerekmiyor; düzenli izleme ve log takibi yeterli."
            )

        return (
            f"🛡️ {target_ip} için önerilen aksiyon: "
            f"{row.get('recommendation', 'Kayıt yakından izlenmeli.')} "
            "Uygulamadan önce ilgili istekleri ve etkilenen hesabı doğrulaman iyi olur."
        )

    risky_rows = [
        row for row in dashboard_data
        if row.get("incident_type") != "NORMAL" or (row.get("score", 0) or 0) > 0
    ]
    risky_rows.sort(key=lambda row: row.get("score", 0) or 0, reverse=True)

    if not risky_rows:
        return "✅ Şu anda önerilecek bir aksiyon yok, riskli olarak sınıflandırılmış bir kayıt bulunmuyor."

    lines = ["🛡️ Öne çıkan riskli kayıtlar için önerilen aksiyonlar:"]
    for row in risky_rows[:5]:
        lines.append(
            f"• {row.get('ip', 'UNKNOWN')} ({row.get('incident_type', 'UNKNOWN')}, "
            f"{row.get('severity', 'UNKNOWN')}) — "
            f"{row.get('recommendation', 'Kayıt yakından izlenmeli.')}"
        )
    lines.append(
        "Bu öneriler analiz motorunun kural tabanlı sınıflandırmasına dayanır; "
        "uygulamadan önce kaydı kendin de doğrulaman iyi olur."
    )
    return "\n".join(lines)


INCIDENT_EXPLANATIONS = {
    "BRUTE_FORCE": (
        "aynı kaynaktan tekrarlanan başarısız giriş veya kimlik doğrulama "
        "denemeleri görüldüğü için"
    ),
    "UNAUTHORIZED_ACCESS": (
        "yetkilendirme gerektiren bir kaynağa başarısız erişim denemeleri "
        "görüldüğü için"
    ),
    "FORBIDDEN_ACCESS": (
        "sunucunun 403 ile reddettiği erişim denemeleri yoğunlaştığı için"
    ),
    "PATH_TRAVERSAL_ATTEMPT": (
        "istek yolunda dizin dışına çıkmayı çağrıştıran kalıplar görüldüğü için"
    ),
    "SCANNER_ACTIVITY": (
        "çok sayıda farklı yolun kısa sürede tarandığını düşündüren istekler "
        "bulunduğu için"
    ),
    "SUSPICIOUS_ACTIVITY": (
        "normal trafik deseninden ayrılan istekler bulunduğu için"
    ),
}


def build_risk_reason_answer(dashboard_data, target_ip=None):
    if target_ip:
        rows = [find_row_by_ip(target_ip, dashboard_data)]
        rows = [row for row in rows if row is not None]
    else:
        rows = [
            row for row in dashboard_data
            if row.get("incident_type") != "NORMAL" or (row.get("score", 0) or 0) > 0
        ]
        rows.sort(key=lambda row: row.get("score", 0) or 0, reverse=True)
        rows = rows[:5]

    if not rows:
        return "✅ Mevcut analizde açıklanacak riskli bir IP kaydı bulunmuyor."

    lines = ["🔎 Bu kayıtların riskli görünme nedenleri:"]
    for row in rows:
        incident_type = row.get("incident_type", "UNKNOWN")
        explanation = INCIDENT_EXPLANATIONS.get(
            incident_type,
            "analiz motorunun olağan dışı bir trafik deseni sınıflandırması yaptığı için",
        )
        lines.append(
            f"• {row.get('ip', 'UNKNOWN')} — {incident_type}: {explanation}. "
            f"Risk skoru {row.get('score', 0)}, severity {row.get('severity', 'UNKNOWN')}."
        )
    lines.append(
        "Bu sınıflandırma tek başına kesin saldırı kanıtı değildir; ilgili log "
        "satırlarını doğrulamak gerekir. 🛡️"
    )
    return "\n".join(lines)


def build_local_question_answer(
    question,
    dashboard_data,
    conversation_history=None,
):
    social_answer = build_social_answer(question)
    if social_answer is not None:
        return social_answer

    if contains_any_term(question, CAPABILITY_QUESTION_TERMS):
        return build_capability_answer()

    if asks_unsupported_identity_or_intent(question):
        return (
            "IP adresinin amacı, niyeti veya gerçek kimliği mevcut analiz "
            "sonuçlarında bulunmuyor."
        )

    if contains_any_term(question, SAFE_IP_QUESTION_TERMS):
        return build_safe_ips_answer(dashboard_data)

    ip_address = extract_ipv4_address(question)
    recent_user_ip = extract_recent_user_ip(conversation_history)

    if contains_any_term(question, ACTION_ADVICE_TERMS):
        return build_action_advice_answer(
            dashboard_data,
            target_ip=ip_address or recent_user_ip,
        )

    if contains_any_term(question, RISK_REASON_TERMS):
        previous_question = extract_previous_user_question(conversation_history)
        reason_target_ip = ip_address or recent_user_ip
        if reason_target_ip is None and asks_highest_risk_ip(previous_question):
            highest_row = max(
                dashboard_data,
                key=lambda row: row.get("score", 0) or 0,
            )
            reason_target_ip = highest_row.get("ip")

        return build_risk_reason_answer(
            dashboard_data,
            target_ip=reason_target_ip,
        )

    if contains_any_term(question, DETAIL_FOLLOW_UP_TERMS):
        if recent_user_ip:
            return build_ip_detail_answer(recent_user_ip, dashboard_data)

        previous_question = extract_previous_user_question(conversation_history)
        if asks_highest_risk_ip(previous_question):
            return build_highest_risk_answer(dashboard_data)
        if contains_any_term(previous_question, RISKY_IP_QUESTION_TERMS):
            return build_risk_reason_answer(dashboard_data)

    if ip_address:
        return build_ip_detail_answer(ip_address, dashboard_data)

    if contains_any_term(question, RISKY_IP_QUESTION_TERMS):
        return build_risky_ips_answer(dashboard_data)

    if asks_highest_risk_ip(question):
        return build_highest_risk_answer(dashboard_data)

    if contains_any_term(question, CRITICAL_QUESTION_TERMS):
        return build_critical_answer(dashboard_data)

    if contains_any_term(question, TOP_INCIDENT_QUESTION_TERMS):
        return build_top_incident_answer(dashboard_data)

    if contains_any_term(question, SEVERITY_DISTRIBUTION_TERMS):
        return build_severity_distribution_answer(dashboard_data)

    if contains_any_term(question, TOTAL_REQUEST_TERMS):
        return build_total_request_answer(dashboard_data)

    return None


def split_compound_questions(question, max_parts=6):
    raw_parts = re.split(r"[\r\n]+", question)
    parts = []

    for raw_part in raw_parts:
        clean_part = re.sub(
            r"^\s*(?:(?:[-*•]+)|(?:\d+[.)]))\s*",
            "",
            raw_part,
        ).strip()
        if clean_part:
            parts.append(clean_part)

    if 1 < len(parts) <= max_parts:
        return parts
    return [question.strip()]


def format_compound_answer(question, answer, index):
    return f"{index}) {question}\n{answer}"


def sanitize_conversation_history(conversation_history):
    if not isinstance(conversation_history, list):
        return []

    safe_history = []
    for message in conversation_history[-10:]:
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue

        clean_content = content.strip()
        if not clean_content:
            continue

        safe_history.append(
            {
                "role": role,
                "content": clean_content[:1000],
            }
        )

    return safe_history


def format_count_distribution(counts):
    if not counts:
        return "veri yok"
    return ", ".join(f"{name}: {counts[name]}" for name in sorted(counts))


def build_analysis_context(dashboard_data):
    total_logs = 0
    suspicious_ips = 0
    incident_counts = {}
    severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    for row in dashboard_data:
        request_count = row.get("request_count", 0) or 0
        incident_type = row.get("incident_type", "UNKNOWN")
        severity = row.get("severity", "UNKNOWN")

        total_logs += request_count
        if incident_type != "NORMAL":
            suspicious_ips += 1
        incident_counts[incident_type] = incident_counts.get(incident_type, 0) + 1
        if severity in severity_counts:
            severity_counts[severity] += 1

    sorted_data = sorted(
        dashboard_data,
        key=lambda row: row.get("score", 0) or 0,
        reverse=True,
    )

    context_lines = [
        f"Toplam istek sayısı: {total_logs}",
        f"Benzersiz IP sayısı: {len(dashboard_data)}",
        f"Şüpheli IP sayısı: {suspicious_ips}",
        f"Incident türü dağılımı: {format_count_distribution(incident_counts)}",
        f"Severity dağılımı: {format_count_distribution(severity_counts)}",
        "En yüksek riskli IP kayıtları:",
    ]

    for row in sorted_data[:CHATBOT_TOP_INCIDENT_LIMIT]:
        context_lines.append(
            f"- IP: {row.get('ip', 'UNKNOWN')}, "
            f"Incident: {row.get('incident_type', 'UNKNOWN')}, "
            f"Severity: {row.get('severity', 'UNKNOWN')}, "
            f"Score: {row.get('score', 0)}, "
            f"İstek sayısı: {row.get('request_count', 0)}, "
            f"Öneri: {row.get('recommendation', 'Kayıt yakından izlenmeli.')}"
        )

    return "\n".join(context_lines)


def _answer_single_log_question(
    normalized_question,
    dashboard_data,
    safe_history,
):
    if not is_in_security_scope(normalized_question, safe_history):
        return OUT_OF_SCOPE_RESPONSE

    social_answer = build_social_answer(normalized_question)
    if social_answer is not None:
        return social_answer

    if not dashboard_data:
        return (
            "Henüz analiz edilmiş bir log göremiyorum 📭 Önce bir log dosyası "
            "yüklediğinde riskli IP'leri ve alınabilecek aksiyonları birlikte "
            "inceleyebiliriz."
        )

    local_answer = build_local_question_answer(
        normalized_question,
        dashboard_data,
        conversation_history=safe_history,
    )
    if local_answer is not None:
        return local_answer

    if not NVIDIA_API_KEY:
        return (
            "Bu soruyu mevcut yerel analizden net biçimde çıkaramadım 🤔 Bana "
            "riskli IP'leri, belirli bir IP'nin detayını veya alınabilecek "
            "aksiyonları sorarsan hemen birlikte inceleyebiliriz."
        )

    context = build_analysis_context(dashboard_data)
    messages = [
        {"role": "system", "content": CHATBOT_INSTRUCTIONS},
        {
            "role": "system",
            "content": (
                "Aşağıdaki veri, cevap verirken kullanabileceğin mevcut analiz "
                f"özetidir:\n{context}"
            ),
        },
        *safe_history,
        {"role": "user", "content": normalized_question},
    ]

    try:
        with create_nvidia_client(NVIDIA_API_KEY) as client:
            response = client.chat.completions.create(
                model=NVIDIA_MODEL_NAME,
                messages=messages,
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
                "Yanıt mevcut analiz verisinin dışına çıktı. IP adresinin amacı "
                "veya niyeti mevcut analiz sonuçlarında bulunmuyor."
            )

        if contains_forbidden_incident_language(safe_answer):
            return (
                "Yanıt güvenli dil kontrolünden geçirilemedi. Mevcut analiz "
                "sonuçlarını incident tablosundan inceleyin."
            )

        return safe_answer

    except Exception as error:
        print(f"Chatbot servis hatası: {type(error).__name__}: {error}")
        return (
            "⚠️ Yapay zekâ servisine şu anda ulaşılamıyor. Yine de temel güvenlik "
            "analizi sonuçlarını ve hazır risk özetlerini kullanmaya devam edebilirsin."
        )


def answer_log_question(
    question,
    dashboard_data,
    conversation_history=None,
):
    if not isinstance(question, str) or not question.strip():
        return "Lütfen boş olmayan bir soru girin."

    normalized_question = question.strip()
    safe_history = sanitize_conversation_history(conversation_history)

    if len(normalized_question) > CHATBOT_MAX_QUESTION_LENGTH:
        return (
            "Soru çok uzun. Lütfen "
            f"{CHATBOT_MAX_QUESTION_LENGTH} karakterden kısa bir soru sorun."
        )

    question_parts = split_compound_questions(normalized_question)
    if len(question_parts) == 1:
        return _answer_single_log_question(
            question_parts[0],
            dashboard_data,
            safe_history,
        )

    rolling_history = list(safe_history)
    combined_answers = []

    for index, question_part in enumerate(question_parts, start=1):
        part_answer = _answer_single_log_question(
            question_part,
            dashboard_data,
            rolling_history,
        )
        combined_answers.append(
            format_compound_answer(question_part, part_answer, index)
        )
        rolling_history = sanitize_conversation_history(
            [
                *rolling_history,
                {"role": "user", "content": question_part},
                {"role": "assistant", "content": part_answer},
            ]
        )

    return "\n\n".join(combined_answers)


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
            "ip": "192.168.1.22",
            "request_count": 34,
            "incident_type": "SCANNER_ACTIVITY",
            "severity": "HIGH",
            "score": 16,
        },
    ]

    for sample_question in (
        "En riskli IP hangisi?",
        "Kritik olay var mı?",
        "Severity dağılımı nedir?",
        "Salon için avize önerir misin?",
    ):
        print(sample_question)
        print(answer_log_question(sample_question, test_data))
