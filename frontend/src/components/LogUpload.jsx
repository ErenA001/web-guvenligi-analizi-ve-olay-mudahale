import { useRef, useState } from "react";

function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 16V4M7 9l5-5 5 5" />
      <path d="M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4" />
    </svg>
  );
}

function LogUpload({ onUploadSuccess }) {
  const inputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [statusType, setStatusType] = useState("");

  function selectFile(file) {
    setStatusMessage("");
    setStatusType("");

    if (!file) {
      setSelectedFile(null);
      return;
    }

    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!['log', 'txt'].includes(extension)) {
      setSelectedFile(null);
      setStatusType("error");
      setStatusMessage("Yalnızca .log ve .txt dosyaları kabul edilir.");
      return;
    }

    setSelectedFile(file);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    selectFile(event.dataTransfer.files?.[0] || null);
  }

  async function handleUploadClick() {
    if (!selectedFile || uploading) return;

    setUploading(true);
    setStatusMessage("");

    const formData = new FormData();
    formData.append("log_file", selectedFile);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      const result = await response.json().catch(() => ({}));

      if (response.status === 401) {
        window.location.assign("/login?next=/");
        return;
      }

      if (!response.ok || !result.success) {
        throw new Error(result.message || "Yükleme başarısız oldu.");
      }

      setStatusType("success");
      setStatusMessage(result.message || "Log dosyası analiz için yüklendi.");
      setSelectedFile(null);
      if (inputRef.current) inputRef.current.value = "";
      onUploadSuccess?.();
    } catch (error) {
      setStatusType("error");
      setStatusMessage(error.message || "Sunucuya bağlanılamadı.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="panel upload-box" id="log-upload" aria-labelledby="upload-title">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">LOG INGESTION</span>
          <h2 id="upload-title">Yeni Analiz Başlat</h2>
        </div>
        <span className="format-tag">LOG / TXT</span>
      </div>

      <div
        className={`drop-zone ${dragging ? "dragging" : ""} ${selectedFile ? "has-file" : ""}`}
        onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex="0"
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".log,.txt,text/plain"
          onChange={(event) => selectFile(event.target.files?.[0] || null)}
          disabled={uploading}
        />
        <span className="upload-icon"><UploadIcon /></span>
        {selectedFile ? (
          <>
            <strong>{selectedFile.name}</strong>
            <span>{(selectedFile.size / 1024).toFixed(1)} KB · Yüklemeye hazır</span>
          </>
        ) : (
          <>
            <strong>Log dosyasını buraya bırakın</strong>
            <span>veya bilgisayarınızdan seçmek için tıklayın · Maksimum 2 MB</span>
          </>
        )}
      </div>

      <button
        className="upload-button"
        type="button"
        onClick={handleUploadClick}
        disabled={!selectedFile || uploading}
      >
        {uploading ? <span className="button-spinner" /> : <UploadIcon />}
        {uploading ? "Analiz hazırlanıyor..." : "Logu Yükle ve Analiz Et"}
      </button>

      {statusMessage && (
        <div className={`upload-status ${statusType}`} role="status">
          <span>{statusType === "success" ? "✓" : "!"}</span>
          {statusMessage}
        </div>
      )}
    </section>
  );
}

export default LogUpload;
