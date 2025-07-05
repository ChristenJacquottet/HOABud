### Front End

This Next.js application provides a chat interface to the OpenAI Chat API.

## Prerequisites

- Node.js (>=14)
- npm

## Setup Backend

1. Install backend dependencies:
   ```bash
   pip install -r api/requirements.txt
   ```
2. Start the backend server:
   ```bash
   uvicorn api.app:app --reload --port 8000
   ```

## Setup and Run Locally

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open your browser to `http://localhost:3000`.

## Usage

1. Enter your OpenAI API key in the input field.
2. Type a message and press Send to chat with the model.
3. Drag & drop your HOA bylaws PDF into the uploader area or click “browse” to select a PDF. The selected file’s name will display.

## Production Build

To build the application for production:

```bash
npm run build
npm start