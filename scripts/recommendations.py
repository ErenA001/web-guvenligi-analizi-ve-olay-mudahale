from config import HIGH_FORBIDDEN_THRESHOLD


def get_recommendation(incident_type):
    if incident_type == "BRUTE_FORCE":
        return "IP engellenmeli (block)"
    elif incident_type == "UNAUTHORIZED_ACCESS":
        return "Rate limiting uygulanmali"
    elif incident_type == "FORBIDDEN_ACCESS":
        return "Erisim yetkileri gozden gecirilmeli"
    elif incident_type == "PATH_TRAVERSAL_ATTEMPT":
        return "Acil inceleme gerekli, dizin disina cikma denemesi tespit edildi"
    elif incident_type == "SCANNER_ACTIVITY":
        return "IP izlenmeli, path taramasi tespit edildi (potansiyel recon)"
    elif incident_type == "SUSPICIOUS_ACTIVITY":
        return "Izlemeye devam edilmeli (monitoring)"
    else:
        return "Aksiyon gerekmiyor"


def generate_checklist(brute_force_ips, total_forbidden, high_severity_count, scanner_ips, path_traversal_ips):

    checklist_lines = []

    if len(brute_force_ips) == 0:
        checklist_lines.append("[OK] Brute force koruması: supheli aktivite yok (OWASP: Broken Authentication)")
    else:
        checklist_lines.append("[UYARI] Brute force koruması: " + str(len(brute_force_ips)) + " IP supheli (OWASP: Broken Authentication)")

    if total_forbidden >= HIGH_FORBIDDEN_THRESHOLD:
        checklist_lines.append("[UYARI] 403 sayisi normalin uzerinde: " + str(total_forbidden) + " adet (OWASP: Broken Access Control)")
    else:
        checklist_lines.append("[OK] 403 sayisi normal seviyede: " + str(total_forbidden) + " adet (OWASP: Broken Access Control)")

    if high_severity_count == 0:
        checklist_lines.append("[OK] HIGH severity IP bulunmadi (OWASP: Security Logging and Monitoring Failures)")
    else:
        checklist_lines.append("[UYARI] " + str(high_severity_count) + " adet HIGH severity IP tespit edildi (OWASP: Security Logging and Monitoring Failures)")

    if len(scanner_ips) == 0:
        checklist_lines.append("[OK] Path taramasi (scanner) suphesi yok (OWASP: Security Misconfiguration)")
    else:
        checklist_lines.append("[UYARI] " + str(len(scanner_ips)) + " IP path taramasi yapiyor olabilir (OWASP: Security Misconfiguration)")

    if len(path_traversal_ips) == 0:
        checklist_lines.append("[OK] Path traversal denemesi yok (OWASP: Broken Access Control)")
    else:
        checklist_lines.append("[UYARI] " + str(len(path_traversal_ips)) + " IP path traversal denemesi yapmis (OWASP: Broken Access Control)")

    return checklist_lines
