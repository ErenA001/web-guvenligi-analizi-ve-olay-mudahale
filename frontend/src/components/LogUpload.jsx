import { useState } from "react";

function LogUpload({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [statusType, setStatusType] = useState("");

  function handleFileChange(event) {
    const file = event.target.files[0] || null;
    setSelectedFile(file);
    setStatusMessage("");
  }

  async function handleUploadClick() {
    if (!selectedFile || uploading) {
      return;
    }

    setUploading(true);
    setStatusMessage("");

    const formData = new FormData();
    formData.append("log_file", selectedFile);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        setStatusType("success");
        setStatusMessage(result.message || "Dosya yüklendi.");
        setSelectedFile(null);

        if (onUploadSuccess) {
          onUploadSuccess();
        }
      } else {
        setStatusType("error");
        setStatusMessage(result.message || "Yükleme başarısız oldu.");
      }
    } catch (error) {
      setStatusType("error");
      setStatusMessage("Sunucuya bağlanılamadı. Flask çalışıyor mu kontrol edin.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="panel upload-box">
      <h2>
        Log Dosyası Yükle
      </h2>

      <p className="description">
        Sadece .log ve .txt dosyaları kabul edilir.
      </p>

      <div className="upload-area">
        <input
          type="file"
          accept=".log,.txt"
          onChange={handleFileChange}
          disabled={uploading}
        />

        <button
          onClick={handleUploadClick}
          disabled={!selectedFile || uploading}
        >
          {uploading ? "Yükleniyor..." : "Yükle"}
        </button>
      </div>

      {statusMessage && (
        <p className={`description upload-status-${statusType}`}>
          {statusMessage}
        </p>
      )}
    </section>
  );
}

export default LogUpload;
