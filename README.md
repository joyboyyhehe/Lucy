# 🤍 Lucy AI — Intelligent Desktop Companion

Lucy is an intent-based local desktop companion that leverages Tauri, React, and FastAPI to resolve tasks. She translates natural language requests into complex multi-step tool calls dynamically.

## 📂 Project Structure

- **`About/`**: Documentation, master plan, and concept files.
- **`Lucy_ai/`**: The core application directory.
  - **`backend/`**: Python FastAPI server, LLM integration, and tool registry.
  - **`frontend/`**: Tauri desktop shell + React (TypeScript + CSS) chat interface.
- **`Lucy_web/`**: Landing pages or websites related to Lucy.
- **`Lucy_workspace/`**: Lucy's local workspace sandbox for files, downloads, and code caches.

## 🚀 Running the Application

### 1. Start the Backend
1. Open a terminal in `Lucy_ai/backend`.
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   # Linux/macOS
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env` template and set your Groq API Key:
   ```bash
   # Set GROQ_API_KEY in .env
   ```
5. Run the server:
   ```bash
   python main.py
   ```
   The backend will start at `http://localhost:8000`.

### 2. Start the Frontend
1. Open a terminal in `Lucy_ai/frontend`.
2. Install package dependencies:
   ```bash
   npm install
   ```
3. Run the development server (in-browser):
   ```bash
   npm run dev
   ```
   The app will be accessible at `http://localhost:1420`.
4. Once Rust is installed, you can launch the native desktop shell using:
   ```bash
   npm run tauri dev
   ```

## 🧠 Core Features (Planned & Upgrades)
- **Multi-Step Chaining (ReAct):** Runs reasoning loops to execute sequential actions.
- **Python Code Interpreter:** Writes and executes scripts inside the local workspace.
- **Self-Correction & Fallbacks:** Gracefully handles tool errors and tries alternative routes.
- **Vision-Based GUI Control:** Takes screenshots and uses coordinates to interact with apps.
- **Semantic Memory:** Firestore-based persistent user profiles and habit tracking.
- **Duplex Interruptible Voice:** Offline speech-to-text (Whisper) and text-to-speech (Kokoro).
