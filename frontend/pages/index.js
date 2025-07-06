// Import React and hooks
import React, { useState, useRef, useEffect } from 'react';
import Image from 'next/image';
import FileUploader from '../components/FileUploader';

// Determine API base URL based on the environment
const API_BASE_URL =
  process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000'
    : '/api';

/**
 * Home component renders the chat interface for interacting with OpenAI Chat API.
 */
function Home() {
  // State for storing the OpenAI API key (sensitive input)
  const [apiKey, setApiKey] = useState('');
  // State for current user input
  const [input, setInput] = useState('');
  // State for message history; each message has a sender and text
  const [messages, setMessages] = useState([]);
  // Loading state to disable input while awaiting response
  const [isLoading, setIsLoading] = useState(false);
  // Ref to scroll chat to bottom when new messages appear
  const messageContainerRef = useRef(null);
  // State for selected file via drag-and-drop
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");

  useEffect(() => {
    if (!selectedFile) return;
    setUploadStatus("Indexing PDF...");
    const form = new FormData();
    form.append("file", selectedFile);
    fetch(`${API_BASE_URL}/upload`, { method: "POST", body: form })
      .then((r) => r.json())
      .then((data) =>
        setUploadStatus(`Indexed ${data.num_chunks} chunks.`)
      )
      .catch((e) =>
        setUploadStatus(`Upload failed: ${e.message}`)
      );
  }, [selectedFile]);

  // Developer message serves as the system prompt
  const developerMessage = 'You are a helpful assistant.';

  /**
   * Send message to backend and stream assistant response.
   */
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || !apiKey.trim()) return;

    const userMessage = input;
    // Add the user's message to chat history
    setMessages((prev) => [...prev, { sender: 'user', text: userMessage }]);
    setInput('');
    setIsLoading(true);

    let assistantText = '';
    try {
      // Send POST request to the chat endpoint
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          developer_message: developerMessage,
          user_message: userMessage,
          api_key: apiKey,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to fetch response');
      }

      // Read the streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        assistantText += chunk;
        // Update or append assistant message in chat history
        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.sender === 'assistant') {
            // Replace last assistant message with updated text
            return [...prev.slice(0, -1), { sender: 'assistant', text: assistantText }];
          }
          // Add new assistant message
          return [...prev, { sender: 'assistant', text: assistantText }];
        });
      }
    } catch (err) {
      console.error('Error:', err);
      // Show error in chat
      setMessages((prev) => [
        ...prev,
        { sender: 'assistant', text: `Error: ${err.message}` },
      ]);
    } finally {
      setIsLoading(false);
      // Scroll to bottom
      setTimeout(() => {
        messageContainerRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 0);
    }
  };

  return (
    <div className="container rounded-xl border bg-card text-card-foreground shadow">
      <div className="header" style={{ textAlign: 'center' }}>
        <Image src="/assets/hoa-bud-logo.png" alt="HOA Bud" width={218} height={100} />
        <p className="tagline">The HOA assistant you’ve always wanted.</p>
      </div>
      <FileUploader onFileSelect={setSelectedFile} />
      {selectedFile && <p>Selected file: {selectedFile.name}</p>}
      {uploadStatus && <p>{uploadStatus}</p>}
      {/* API Key input field (sensitive) */}
      <div>
        <label htmlFor="apiKey">Openai API Key:</label>
        <input
          id="apiKey"
          type="password"
          className="apiKeyField"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Enter your OpenAI API key"
        />
      </div>
      {/* Chat message display area */}
      <div className="chatContainer">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chatBubble ${
              msg.sender === 'user' ? 'userBubble' : 'assistantBubble'
            }`}
          >
            {msg.text}
          </div>
        ))}
        {/* Reference for scrolling */}
        <div ref={messageContainerRef} />
      </div>
      {/* Input form for sending new messages */}
      <form onSubmit={sendMessage} className="inputForm">
        <input
          type="text"
          className="inputField"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button type="submit" className="sendButton" disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}

export default Home;