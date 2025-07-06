import React, { useState, useRef } from 'react';

/**
 * FileUploader component for drag-and-drop or browsing PDF files.
 * onFileSelect is a callback receiving the selected File object.
 */
function FileUploader({ onFileSelect }) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  // Ref to clear input for same-file uploads
  const inputRef = useRef(null);

  // Handler to remove the selected file
  const removeFile = () => {
    setFile(null);
    if (onFileSelect) {
      onFileSelect(null);
    }
    // clear file input value so same file can be reselected
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const handleDrag = (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (event.type === 'dragenter' || event.type === 'dragover') {
      setDragActive(true);
    } else if (event.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
    if (event.dataTransfer.files && event.dataTransfer.files[0]) {
      selectFile(event.dataTransfer.files[0]);
    }
  };

  const handleChange = (event) => {
    if (event.target.files && event.target.files[0]) {
      selectFile(event.target.files[0]);
    }
  };

  const selectFile = (selected) => {
    setFile(selected);
    if (onFileSelect) {
      onFileSelect(selected);
    }
  };

  return (
    <div className="uploadContainer">
      <p>Upload your HOA bylaws :</p>
      <div
        className={`uploadArea ${dragActive ? 'dragActive' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        {!file && (
          <>
            <div className="uploadIcon">
              {/* Upload icon */}
              <svg
                width="38"
                height="38"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#4198ce"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <p>
              Drag & drop your PDF here, or <span className="uploadBrowse">Browse</span>
            </p>
          </>
        )}
        {file && (
          <div className="fileItem">
            <span className="fileName">{file.name}</span>
            <span className="fileSize">{(file.size / 1024 / 1024).toFixed(1)} MB</span>
            <button type="button" className="removeButton" onClick={removeFile}>✕</button>
          </div>
        )}
        {!file && (
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            onChange={handleChange}
            className="uploadInput"
          />
        )}
      </div>
    </div>
  );
}

export default FileUploader;