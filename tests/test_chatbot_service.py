import unittest

from services.chatbot_service import answer_log_question


TEST_DATA = [
    {
        "ip": "192.168.1.11",
        "request_count": 120,
        "incident_type": "BRUTE_FORCE",
        "severity": "CRITICAL",
        "score": 45,
        "recommendation": "IP engellenmeli (block)",
    },
    {
        "ip": "192.168.1.30",
        "request_count": 80,
        "incident_type": "UNAUTHORIZED_ACCESS",
        "severity": "CRITICAL",
        "score": 28,
        "recommendation": "Rate limiting uygulanmalı",
    },
    {
        "ip": "10.0.0.9",
        "request_count": 25,
        "incident_type": "FORBIDDEN_ACCESS",
        "severity": "HIGH",
        "score": 12,
        "recommendation": "Erişim yetkileri gözden geçirilmeli",
    },
    {
        "ip": "192.168.1.1",
        "request_count": 2,
        "incident_type": "NORMAL",
        "severity": "LOW",
        "score": 0,
        "recommendation": "Aksiyon gerekmiyor",
    },
]


class ChatbotServiceTests(unittest.TestCase):
    def test_thanks_is_warm_not_out_of_scope(self):
        answer = answer_log_question("Tamam, teşekkürler 🙏", TEST_DATA)
        self.assertIn("Rica ederim", answer)
        self.assertNotIn("kapsam", answer.casefold())

    def test_colloquial_thanks_with_friendly_address_is_warm(self):
        answer = answer_log_question("Tamam sağ olasın kral", TEST_DATA)
        self.assertIn("Eyvallah kral", answer)
        self.assertNotIn("güvenilir bir cevap veremem", answer)

    def test_confused_reaction_repairs_the_conversation(self):
        answer = answer_log_question("Ne diyon ya", TEST_DATA)
        self.assertIn("Haklısın", answer)
        self.assertIn("alakasız", answer)
        self.assertNotIn("güvenilir bir cevap veremem", answer)

    def test_multiline_message_answers_every_question_in_order(self):
        answer = answer_log_question(
            "hangi ipler riskli\n"
            "bunlara ne yapabilirim\n"
            "risksiz ipler nedir\n"
            "tamam teşekkürler",
            TEST_DATA,
        )
        self.assertIn("1) hangi ipler riskli", answer)
        self.assertIn("2) bunlara ne yapabilirim", answer)
        self.assertIn("3) risksiz ipler nedir", answer)
        self.assertIn("4) tamam teşekkürler", answer)
        self.assertIn("192.168.1.11", answer)
        self.assertIn("IP engellenmeli", answer)
        self.assertIn("192.168.1.1", answer)
        self.assertIn("Rica ederim", answer)

    def test_greeting_works_without_log_data(self):
        answer = answer_log_question("Selam", [])
        self.assertIn("Selam", answer)
        self.assertNotIn("Henüz analiz", answer)

    def test_safe_ips_are_answered_locally_and_completely(self):
        answer = answer_log_question("Risksiz IP'ler nedir?", TEST_DATA)
        self.assertIn("192.168.1.1", answer)
        self.assertNotIn("192.168.1.11\n", answer)
        self.assertIn("kesin güvenli", answer)

    def test_general_action_follow_up_lists_all_risky_rows(self):
        history = [
            {"role": "user", "content": "Hangi IP'ler riskli?"},
            {"role": "assistant", "content": "Riskli IP listesi"},
        ]
        answer = answer_log_question(
            "Bunlara ne yapabilirim?",
            TEST_DATA,
            conversation_history=history,
        )
        self.assertIn("192.168.1.11", answer)
        self.assertIn("192.168.1.30", answer)
        self.assertIn("10.0.0.9", answer)
        self.assertIn("IP engellenmeli", answer)
        self.assertIn("Rate limiting", answer)

    def test_specific_ip_follow_up_targets_that_ip(self):
        history = [
            {"role": "user", "content": "192.168.1.11 hakkında bilgi ver"},
            {"role": "assistant", "content": "192.168.1.11 BRUTE_FORCE kaydıdır"},
        ]
        answer = answer_log_question(
            "Peki buna ne yapabilirim?",
            TEST_DATA,
            conversation_history=history,
        )
        self.assertIn("192.168.1.11 için", answer)
        self.assertNotIn("192.168.1.30", answer)

    def test_reason_follow_up_uses_previous_highest_risk_context(self):
        history = [
            {"role": "user", "content": "En riskli IP hangisi?"},
            {"role": "assistant", "content": "192.168.1.11"},
        ]
        answer = answer_log_question(
            "Bu neden riskli?",
            TEST_DATA,
            conversation_history=history,
        )
        self.assertIn("192.168.1.11", answer)
        self.assertIn("tekrarlanan başarısız giriş", answer)
        self.assertNotIn("192.168.1.30", answer)

    def test_out_of_scope_response_is_polite(self):
        answer = answer_log_question("Bana yemek tarifi ver", TEST_DATA)
        self.assertIn("güvenilir bir cevap veremem", answer)
        self.assertIn("birlikte", answer)


if __name__ == "__main__":
    unittest.main()
