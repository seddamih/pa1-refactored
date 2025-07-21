import React, { useState, DragEvent, ChangeEvent } from "react";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      setFile(droppedFile);
    }
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        setMessage("✅ File uploaded successfully!");
      } else {
        setMessage("❌ Upload failed.");
      }
    } catch (err) {
      console.error(err);
      setMessage("❌ Upload error.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold text-blue-600 mb-6">Upload a File</h1>

      <div
        className="w-full max-w-md p-6 border-2 border-dashed border-blue-400 bg-white rounded-lg text-center cursor-pointer hover:bg-blue-50"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <p className="text-gray-500 mb-2">Drag & drop a file here</p>
        <p className="text-gray-400">or click below</p>

        <input
          type="file"
          onChange={handleFileSelect}
          className="mt-4"
        />
      </div>

      {file && (
        <div className="mt-4 text-sm text-gray-700">
          Selected file: <strong>{file.name}</strong>
        </div>
      )}

      <button
        onClick={handleUpload}
        className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        disabled={!file}
      >
        Upload
      </button>

      {message && (
        <div className="mt-4 text-lg">{message}</div>
      )}
    </div>
  );
}

export default App;
