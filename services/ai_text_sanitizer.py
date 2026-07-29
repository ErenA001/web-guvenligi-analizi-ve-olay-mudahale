import re


INCIDENT_LANGUAGE_REPLACEMENTS = (
    (r"\bbrute force saldırısı\b", "brute force belirtisi"),
    (r"\bbrute force saldirisi\b", "brute force belirtisi"),
    (r"\bsaldırıya uğramış\b", "şüpheli aktivite bulunan"),
    (r"\bsaldiriya ugramis\b", "şüpheli aktivite bulunan"),
    (r"\bsaldırıya uğradı\b", "şüpheli aktivite görüldü"),
    (r"\bsaldiriya ugradi\b", "şüpheli aktivite görüldü"),
    (
        r"\bsaldırı gerçekleştirilmiştir\b",
        "şüpheli aktivite kaydı bulunmaktadır",
    ),
    (
        r"\bsaldiri gerceklestirilmistir\b",
        "şüpheli aktivite kaydı bulunmaktadır",
    ),
    (
        r"\bsaldırı gerçekleştirildi\b",
        "şüpheli aktivite kaydı görüldü",
    ),
    (
        r"\bsaldiri gerceklestirildi\b",
        "şüpheli aktivite kaydı görüldü",
    ),
    (r"\bsaldırı gerçekleşti\b", "şüpheli aktivite görüldü"),
    (r"\bsaldiri gerceklesti\b", "şüpheli aktivite görüldü"),
    (r"\bbu saldırı\b", "bu kayıt"),
    (r"\bbu saldiri\b", "bu kayıt"),
    (r"\bsaldırılar\b", "şüpheli aktiviteler"),
    (r"\bsaldirilar\b", "şüpheli aktiviteler"),
    (r"\bsaldırgan\b", "şüpheli kaynak"),
    (r"\bsaldirgan\b", "şüpheli kaynak"),
    (r"\bsaldırı\b", "şüpheli aktivite"),
    (r"\bsaldiri\b", "şüpheli aktivite"),
)

FORBIDDEN_INCIDENT_PATTERNS = (
    r"\bsaldırı\w*\b",
    r"\bsaldiri\w*\b",
    r"\bsaldırgan\w*\b",
    r"\bsaldirgan\w*\b",
)


def sanitize_incident_language(text):
    if not text:
        return text

    sanitized_text = text

    for pattern, replacement in INCIDENT_LANGUAGE_REPLACEMENTS:
        sanitized_text = re.sub(
            pattern,
            replacement,
            sanitized_text,
            flags=re.IGNORECASE,
        )

    sanitized_text = re.sub(r"\s+", " ", sanitized_text)

    return sanitized_text.strip()


def contains_forbidden_incident_language(text):
    if not text:
        return False

    for pattern in FORBIDDEN_INCIDENT_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True

    return False


if __name__ == "__main__":
    test_text = (
        "Bu IP saldırıya uğradı ve brute force saldırısı gerçekleşti. "
        "Bu saldırı yüksek riskli görünüyor."
    )

    cleaned_text = sanitize_incident_language(test_text)

    print("Temizlenmiş metin:")
    print(cleaned_text)
    print(
        "Yasaklı ifade kaldı mı:",
        contains_forbidden_incident_language(cleaned_text),
    )
