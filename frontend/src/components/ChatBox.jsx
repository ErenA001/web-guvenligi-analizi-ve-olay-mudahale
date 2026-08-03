import { useEffect, useRef, useState } from "react";

const WHATSAPP_URL =
  "https://wa.me/447441900754?text=Merhaba%2C%20Secure%20AI%20projesi%20hakk%C4%B1nda%20destek%20almak%20istiyorum.";

const INITIAL_MESSAGES = [
  {
    id: "welcome",
    role: "assistant",
    text: "Selam! 👋 Ben Secure AI. Loglarını birlikte inceleyebilir, riskli IP'leri bulabilir ve her kayıt için ne yapabileceğini konuşabiliriz. Nereden başlayalım? 🛡️",
  },
];

function BotIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M9 4h6M12 2v2" />
      <rect x="4" y="6" width="16" height="13" rx="4" />
      <path d="M8 11h.01M16 11h.01M8 15c2.5 1.4 5.5 1.4 8 0" />
    </svg>
  );
}

function WhatsAppIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20.5 11.8a8.5 8.5 0 0 1-12.6 7.5L3 20.6l1.3-4.7A8.5 8.5 0 1 1 20.5 11.8Z" />
      <path d="M8.1 7.7c.2-.5.4-.5.7-.5h.5c.2 0 .4.1.5.4l.8 1.9c.1.3.1.5-.1.7l-.6.7c-.2.2-.2.4-.1.6.6 1.2 1.6 2.2 2.8 2.8.2.1.4.1.6-.1l.8-1c.2-.2.4-.3.7-.2l1.9.9c.3.1.4.3.4.5 0 .4-.2 1.3-.9 1.8-.6.5-1.5.8-2.5.5-1.5-.4-3.3-1.3-4.9-2.8-1.3-1.2-2.3-2.8-2.7-4.2-.3-.9 0-1.6.4-2Z" />
    </svg>
  );
}

function ChatBox() {
  const [open, setOpen] = useState(false);
  const [supportOpen, setSupportOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const chatEndRef = useRef(null);

  const questions = [
    "🚨 En riskli IP hangisi?",
    "🔎 Hangi IP'ler riskli?",
    "🛡️ Bunlar için ne yapabilirim?",
    "🔎 Severity dağılımı nedir?",
  ];

  useEffect(() => {
    if (open) {
      window.setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    window.setTimeout(() => {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }, 40);
  }, [messages, loading, open]);

  const MIN_TYPING_DELAY_MS = 550;

  async function sendQuestion(questionText) {
    const trimmedQuestion = questionText.trim();
    if (!trimmedQuestion || loading) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text: trimmedQuestion,
    };

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setQuestion("");
    setLoading(true);

    const requestStartedAt = Date.now();
    const conversationHistory = messages
      .slice(-10)
      .filter((message) => !message.isError)
      .map((message) => ({
        role: message.role,
        content: message.text,
      }));

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: trimmedQuestion,
          history: conversationHistory,
        }),
      });
      const result = await response.json().catch(() => ({}));

      if (response.status === 401) {
        window.location.assign("/login?next=/");
        return;
      }

      if (!response.ok) {
        throw new Error(result.answer || "Chatbot şu anda yanıt veremedi.");
      }

      const elapsed = Date.now() - requestStartedAt;
      if (elapsed < MIN_TYPING_DELAY_MS) {
        await new Promise((resolve) =>
          window.setTimeout(resolve, MIN_TYPING_DELAY_MS - elapsed)
        );
      }

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          text: result.answer || "Bu soruya uygun bir cevap alınamadı. 🤔",
        },
      ]);
    } catch (error) {
      const elapsed = Date.now() - requestStartedAt;
      if (elapsed < MIN_TYPING_DELAY_MS) {
        await new Promise((resolve) =>
          window.setTimeout(resolve, MIN_TYPING_DELAY_MS - elapsed)
        );
      }

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          text: `Bağlantıda küçük bir sorun oluştu. ⚠️ ${error.message || "Sunucuya ulaşılamadı."}`,
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
      window.setTimeout(() => inputRef.current?.focus(), 80);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendQuestion(question);
  }

  return (
    <div className="assistant-layer" id="ai-assistant">
      {supportOpen && (
        <div className="support-confirm" role="dialog" aria-label="WhatsApp yönlendirme onayı">
          <button className="support-close" type="button" onClick={() => setSupportOpen(false)} aria-label="Kapat">×</button>
          <div className="support-icon"><WhatsAppIcon /></div>
          <strong>WhatsApp desteğine geçilsin mi?</strong>
          <p>+44 7441 900754 numarası üzerinden yeni bir sohbet açılacak.</p>
          <div className="support-actions">
            <button type="button" className="support-cancel" onClick={() => setSupportOpen(false)}>Vazgeç</button>
            <a href={WHATSAPP_URL} target="_blank" rel="noreferrer" onClick={() => setSupportOpen(false)}>WhatsApp&apos;a geç</a>
          </div>
        </div>
      )}

      {open && (
        <section className="chat-widget" aria-label="AI Security Assistant">
          <header className="chat-header">
            <div className="chat-avatar"><BotIcon /><span /></div>
            <div>
              <strong>AI Security Assistant</strong>
              <span><i /> Çevrimiçi • Loglarını dinliyorum 🤖</span>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Chatbotu kapat">×</button>
          </header>

          <div className="chat-body" aria-live="polite">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.role === "user" ? "user-message" : "bot-message"} ${message.isError ? "error-message" : ""}`}
              >
                <span className="message-label">
                  {message.role === "user" ? "SEN • 💬" : "SECURE AI • 🤖"}
                </span>
                <p>{message.text}</p>
              </div>
            ))}

            {messages.length === 1 && (
              <div className="quick-questions">
                {questions.map((quickQuestion) => (
                  <button
                    key={quickQuestion}
                    type="button"
                    onClick={() => sendQuestion(quickQuestion)}
                    disabled={loading}
                  >
                    {quickQuestion}
                  </button>
                ))}
              </div>
            )}

            {loading && (
              <div className="message bot-message typing-message" aria-label="Yanıt hazırlanıyor">
                <span /><span /><span />
                <em>Birlikte bakalım...</em>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <form className="chat-form" onSubmit={handleSubmit}>
            <textarea
              ref={inputRef}
              placeholder="Mesajını yaz... Örn: Hangi IP'ler riskli? 🔎"
              value={question}
              maxLength={300}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSubmit(event);
                }
              }}
            />
            <button type="submit" disabled={loading || !question.trim()} aria-label="Soruyu gönder">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 4 17 8-17 8 3-8-3-8Z" /><path d="M7 12h14" /></svg>
            </button>
          </form>
          <div className="chat-footer">🔒 Yalnızca mevcut güvenlik analizi verilerini kullanırım.</div>
        </section>
      )}

      <div className="floating-actions">
        <button
          className="floating-button whatsapp-button"
          type="button"
          onClick={() => { setSupportOpen((value) => !value); setOpen(false); }}
          aria-label="WhatsApp desteği"
          title="WhatsApp desteği"
        >
          <WhatsAppIcon />
        </button>
        <button
          className={`floating-button assistant-button ${open ? "active" : ""}`}
          type="button"
          onClick={() => { setOpen((value) => !value); setSupportOpen(false); }}
          aria-label="AI Security Assistant"
          title="AI Security Assistant"
        >
          <span className="assistant-pulse" />
          <BotIcon />
        </button>
      </div>
    </div>
  );
}

export default ChatBox;
