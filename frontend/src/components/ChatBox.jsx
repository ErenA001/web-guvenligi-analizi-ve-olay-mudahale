import { useState } from "react";

function ChatBox() {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const questions = [
    "En riskli IP hangisi?",
    "Kritik olay var mı?",
    "En çok görülen incident türü?",
    "Severity dağılımı nedir?",
  ];

  async function sendQuestion(questionText) {
    const trimmedQuestion = questionText.trim();

    if (!trimmedQuestion || loading) {
      return;
    }

    setLoading(true);
    setAnswer("");

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: trimmedQuestion }),
      });

      const result = await response.json();

      setAnswer(result.answer || "Cevap alınamadı.");
    } catch (error) {
      setAnswer("Sunucuya bağlanılamadı. Flask çalışıyor mu kontrol edin.");
    } finally {
      setLoading(false);
    }
  }

  function handleSendClick() {
    sendQuestion(question);
  }

  function handleQuickQuestionClick(quickQuestion) {
    setQuestion(quickQuestion);
    sendQuestion(quickQuestion);
  }

  return (
    <>
      <button
        className="chat-toggle"
        onClick={() => setOpen(!open)}
      >
        🤖
      </button>

      {open && (
        <div className="chat-widget">

          <div className="chat-header">
            AI Security Assistant
          </div>


          <div className="chat-body">

            <p>
              Merhaba, analiz sonuçları hakkında
              soru sorabilirsin.
            </p>


            <div className="quick-questions">

              {questions.map((quickQuestion) => (
                <button
                  key={quickQuestion}
                  className="question-chip"
                  onClick={() => handleQuickQuestionClick(quickQuestion)}
                  disabled={loading}
                >
                  {quickQuestion}
                </button>
              ))}

            </div>


            <textarea
              placeholder="Sorunuzu yazın..."
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
            />


            <button
              className="send-button"
              onClick={handleSendClick}
              disabled={loading}
            >
              {loading ? "Yanıt bekleniyor..." : "Gönder"}
            </button>

            {answer && (
              <div className="chat-response">
                {answer}
              </div>
            )}

          </div>

        </div>
      )}
    </>
  );
}

export default ChatBox;
