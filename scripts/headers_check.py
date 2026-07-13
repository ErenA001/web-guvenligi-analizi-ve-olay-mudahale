import urllib.request
import urllib.error

from config import HEADER_CHECK_TIMEOUT, SECURITY_HEADERS


def check_security_headers(url):
    """Verilen URL'ye GET istegi atar, response header'larini kontrol eder.

    Donen deger bir sozluk: {"url", "basarili", "hata", "eksik_headerlar", "mevcut_headerlar"}
    Bu fonksiyon disariya asla exception firlatmaz; tum hatalar
    yakalanip sonuc sozlugu icinde raporlanir, boylece script
    tek bir siteye ulasilamasa bile calismaya devam eder.
    """

    result = {
        "url": url,
        "basarili": False,
        "hata": None,
        "eksik_headerlar": [],
        "mevcut_headerlar": [],
    }

    request = urllib.request.Request(url, headers={"User-Agent": "SecurityHeaderChecker/1.0"})

    try:
        with urllib.request.urlopen(request, timeout=HEADER_CHECK_TIMEOUT) as response:
            response_headers = response.headers
            result["basarili"] = True

            for header_name, owasp_category in SECURITY_HEADERS:
                if header_name in response_headers:
                    result["mevcut_headerlar"].append(header_name)
                else:
                    result["eksik_headerlar"].append((header_name, owasp_category))

    except urllib.error.HTTPError as error:
        result["hata"] = "HTTP Hatasi: " + str(error.code)
    except urllib.error.URLError as error:
        result["hata"] = "Baglanti Hatasi: " + str(error.reason)
    except TimeoutError:
        result["hata"] = "Zaman Asimi (timeout)"
    except Exception as error:
        result["hata"] = "Beklenmeyen Hata: " + str(error)

    return result


def run_header_checks(target_urls):
    """Tum hedef URL'ler icin header kontrolunu calistirir.

    Sonuclari hem terminale yazdirir hem de rapor dosyasina eklenecek
    satirlarin bir listesini dondurur.
    """

    header_report_lines = []
    header_report_lines.append("## Security Headers Check")
    header_report_lines.append("")

    print("\n--- Security Headers Check ---")

    all_results = []

    for url in target_urls:
        result = check_security_headers(url)
        all_results.append(result)

        if not result["basarili"]:
            print("\nURL:", url)
            print("Durum: BASARISIZ -", result["hata"])

            header_report_lines.append("### " + url)
            header_report_lines.append("- Durum: BASARISIZ - " + result["hata"])
            header_report_lines.append("")
            continue

        print("\nURL:", url)
        print("Durum: BASARILI")
        print("Mevcut guvenlik headerlari:", len(result["mevcut_headerlar"]), "/", len(SECURITY_HEADERS))

        header_report_lines.append("### " + url)
        header_report_lines.append("- Durum: BASARILI")
        header_report_lines.append("- Mevcut guvenlik headerlari: " + str(len(result["mevcut_headerlar"])) + "/" + str(len(SECURITY_HEADERS)))

        if len(result["eksik_headerlar"]) == 0:
            print("Tum onerilen guvenlik headerlari mevcut.")
            header_report_lines.append("- Tum onerilen guvenlik headerlari mevcut.")
        else:
            print("Eksik headerlar:")
            header_report_lines.append("- Eksik headerlar:")
            for header_name, owasp_category in result["eksik_headerlar"]:
                print(" ", header_name, "-> eksik (OWASP:", owasp_category, ")")
                header_report_lines.append("  - " + header_name + " -> eksik (OWASP: " + owasp_category + ")")

        header_report_lines.append("")

    return header_report_lines, all_results
