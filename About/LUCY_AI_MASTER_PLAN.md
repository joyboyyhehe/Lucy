# 🤍 LUCY AI — Intelligent Desktop Companion
### Master Brainstorm & Build Plan
> *"You talk. She understands. She acts."*

---

## 🎯 Core Philosophy

Lucy is **not a command executor**.
She is an **intent resolver**.

You don't say `"open youtube and search how coke is made"`.
You say `"show me how coke is made"` — and she figures out the rest.

The LLM decides what to do. Lucy's job is to understand *what you actually want*, then make it happen.

```
Good Evening, Prathap.

System: Healthy  |  3 tasks pending  |  2 unread emails

Last session: Rising Oak Academy (3h ago)
Resume where you left off?
```

---

## 🧠 How Lucy Thinks (Intent Architecture)

This is the most important part of the whole system.

**Old (bad) approach — hardcoded:**
```
if "open youtube" in command:
    launch("youtube.com")
```

**Lucy's approach — intent-based:**
```
User says: "show me how coke is made"

Lucy thinks:
  → User wants to watch a video
  → Best source: YouTube
  → Search query: "how coca cola is made"
  → Action: open browser (headless) → navigate → play first result
  → Confirm: "Playing a video on how Coke is made."
```

The LLM receives the user's message + available tools (actions Lucy can perform), then **decides which tools to call and in what order**. This is called **tool-use / function calling** — and Groq supports it natively.

### Tool-Use Flow
```
[User speaks/types]
       ↓
[Whisper STT if voice]
       ↓
[Lucy's brain — Groq LLM]
  receives: message + memory context + list of available tools
  outputs: which tool(s) to call + parameters
       ↓
[Tool executor runs the action]
  e.g. browser.search("how coca cola is made", site="youtube")
       ↓
[Result fed back to LLM]
  LLM generates natural language response
       ↓
[Kokoro TTS speaks / UI shows response]
```

No hardcoding. Every action is decided by the LLM at runtime.

---

## 🛠️ Tech Stack (Final, Free-Only)

| Layer | Technology | Cost |
|-------|-----------|------|
| **Desktop Shell** | Tauri (Rust + WebView) | Free |
| **Frontend** | React + TypeScript + Tailwind | Free |
| **Backend** | Python + FastAPI | Free |
| **LLM + Tool Use** | Groq API (llama-3.3-70b or similar) | Free tier |
| **STT** | OpenAI Whisper (local, runs offline) | Free |
| **TTS** | Kokoro TTS (local, natural voices) | Free |
| **Auth** | Firebase Authentication | Free tier |
| **Memory / DB** | Firebase Firestore | Free tier |
| **Browser Automation** | Playwright (Python, headless) | Free |
| **OS Automation** | Python: `subprocess`, `psutil`, `pyautogui` | Free |
| **Wake Word** | Porcupine (free tier, 1 wake word) | Free |
| **Vision** | Groq vision model (llama-4-scout) | Free tier |

---

## 📁 Project Structure

```
lucy-ai/
│
├── frontend/                   # Tauri + React app
│   ├── src/
│   │   ├── components/         # Chat UI, HUD, cards
│   │   ├── pages/              # Home, Settings, Memory
│   │   ├── hooks/              # useVoice, useLucy, useMemory
│   │   └── store/              # Zustand global state
│   └── src-tauri/              # Rust + Tauri config
│
├── backend/                    # Python FastAPI
│   ├── main.py                 # Entry point
│   ├── routes/
│   │   ├── chat.py             # /chat endpoint
│   │   ├── voice.py            # /transcribe endpoint
│   │   └── memory.py           # /memory endpoints
│   ├── lucy/
│   │   ├── brain.py            # LLM + tool-use orchestration (CORE)
│   │   ├── tools.py            # Tool registry & executor
│   │   └── context.py          # Memory + session context builder
│   └── config.py
│
├── tools/                      # Every action Lucy can take
│   ├── base.py                 # Tool interface (all tools extend this)
│   ├── browser.py              # Playwright headless automation
│   ├── os_control.py           # App launch, volume, window mgmt
│   ├── file_system.py          # Read, write, move, find files
│   ├── vision.py               # Screenshot + visual analysis
│   ├── coding.py               # File watcher, code analysis
│   └── system_info.py          # CPU, RAM, battery, etc.
│
├── voice/
│   ├── stt.py                  # Whisper speech-to-text
│   ├── tts.py                  # Kokoro TTS wrapper
│   └── wake_word.py            # Porcupine wake word listener
│
├── memory/
│   ├── firebase.py             # Firestore read/write
│   ├── session.py              # In-session short-term memory
│   └── user_profile.py        # Preferences, projects, habits
│
├── workspace/                  # Lucy's own folder (her scratch space)
│   ├── temp/                   # Temporary files she creates
│   ├── downloads/              # Things she fetches
│   ├── notes/                  # Things she saves for you
│   └── projects/               # Project metadata she tracks
│
├── config/
│   ├── settings.yaml           # User config (voice, theme, etc.)
│   └── firebase_config.json    # Firebase credentials (gitignored)
│
└── docs/
    └── LUCY_MASTER_PLAN.md     # This file
```

---

## 🔧 Tool System (How Lucy Acts)

Every action Lucy can perform is a **Tool**. Tools are registered, and the LLM picks which ones to use.

### Tool Interface
```python
# tools/base.py
class LucyTool:
    name: str               # "browser_search"
    description: str        # "Search the web or a specific site"
    parameters: dict        # JSON schema — LLM knows what to pass
    
    async def run(self, **kwargs) -> dict:
        # Executes the action, returns result
        ...
```

### Tool Registry (what Lucy can do at launch)
```python
TOOLS = [
    BrowserSearchTool(),       # Search anything, anywhere
    BrowserNavigateTool(),     # Go to a URL
    BrowserClickTool(),        # Click elements on a page
    OpenAppTool(),             # Launch any application
    CloseAppTool(),            # Kill a process
    VolumeControlTool(),       # Set/adjust volume
    ScreenshotTool(),          # Capture screen
    VisionAnalyzeTool(),       # Analyze screenshot with LLM
    FileSearchTool(),          # Find files by name/content
    FileMoveTool(),            # Move/copy/rename files
    FileCreateTool(),          # Create files/folders
    FileReadTool(),            # Read file contents
    FileWriteTool(),           # Write to a file
    SystemInfoTool(),          # CPU, RAM, battery
    CodeExplainTool(),         # Explain a code file
    WorkspaceReadTool(),       # Read Lucy's workspace
    WorkspaceWriteTool(),      # Write to Lucy's workspace
]
```

New tools = new capabilities. No rewiring needed.

---

## 🔥 Firebase Memory Architecture

Everything about you lives in Firestore under your UID.

```
firestore/
└── users/
    └── {uid}/
        ├── profile/
        │   ├── name: "Prathap"
        │   ├── preferences: { theme: "dark", voice: "af_heart" }
        │   └── habits: { coding_start: "22:00", fav_music: "lo-fi" }
        │
        ├── projects/
        │   └── {project_id}/
        │       ├── name: "Rising Oak Academy"
        │       ├── path: "C:/Projects/rising-oak"
        │       ├── last_opened: timestamp
        │       ├── stack: ["React", "Firebase"]
        │       └── notes: "Working on fee module"
        │
        ├── sessions/
        │   └── {session_id}/
        │       ├── date: timestamp
        │       ├── summary: "Worked on TPS Connect, fixed auth bug"
        │       └── actions_taken: [...]
        │
        └── memories/
            └── {memory_id}/
                ├── type: "preference" | "fact" | "project" | "habit"
                ├── content: "Prathap prefers VS Code over WebStorm"
                └── timestamp: ...
```

**At session start**, Lucy fetches your profile + recent sessions + active projects → builds a context string → injects into every LLM call so she always knows who you are.

---

## 🌟 Phases (Plan → Build Order)

---

### ✅ Phase 0 — Skeleton (Start Here)
*"Make it boot."*

- [ ] Tauri + React frontend running
- [ ] FastAPI backend running
- [ ] Chat box → message hits Groq API → response shows
- [ ] Firebase project created, auth working (Google Sign-In)
- [ ] Lucy's workspace folder created on first launch
- [ ] `.env` with Groq API key + Firebase config

**Done when:** You can log in, type a message, get a response.

---

### 🧠 Phase 1 — Brain + Tool Use
*"Make her understand and act."*

- [ ] Tool registry system built
- [ ] Groq function-calling hooked up to tool registry
- [ ] Tool executor runs the chosen tool and returns result
- [ ] LLM gets tool result and responds naturally
- [ ] Build first 3 tools: `OpenAppTool`, `SystemInfoTool`, `BrowserSearchTool`
- [ ] Test: "show me something relaxing on YouTube" → headless browser plays it

**Done when:** Lucy can open apps and browser-search based on natural language.

---

### 📂 Phase 2 — File System + Workspace
*"Give her hands."*

- [ ] File search, read, write, move, create tools
- [ ] Lucy's `/workspace` folder initialized with structure
- [ ] She can save notes to her workspace
- [ ] She can find and organize your files
- [ ] "Move my downloads to the right folders" works

**Done when:** File operations work end-to-end from natural language.

---

### 🔥 Phase 3 — Memory (Firebase)
*"Give her a brain that persists."*

- [ ] User profile read/write (Firestore)
- [ ] Session logger (end of session → summarize → save)
- [ ] Project tracker (detect active project, log time)
- [ ] Context builder: fetch memory → inject into every LLM prompt
- [ ] "You were working on Rising Oak yesterday, resume?" works

**Done when:** Lucy remembers you across restarts.

---

### 👀 Phase 4 — Vision
*"Let her see."*

- [ ] Screenshot capture tool
- [ ] Send screenshot to Groq vision model
- [ ] "What's wrong on my screen?" works
- [ ] "Explain this error" works
- [ ] Summarize a PDF from screenshot

**Done when:** She can read and explain what's on your screen.

---

### 🎤 Phase 5 — Voice
*"Let her hear and speak."*

- [ ] Whisper STT (local) — transcribes mic input
- [ ] Kokoro TTS — speaks Lucy's responses naturally
- [ ] Push-to-talk mode (hold key → speak → release)
- [ ] Wake word "Hey Lucy" via Porcupine
- [ ] Voice pipeline: wake → transcribe → brain → TTS

**Done when:** Full hands-free interaction works.

---

### 🤖 Phase 6 — Coding Assistant
*"Make her useful when you code."*

- [ ] File watcher detects your active project
- [ ] "Explain this function" reads the file and explains
- [ ] "Find bugs in this" sends code to Groq
- [ ] "Write a commit message" reads git diff → generates message
- [ ] "Generate docs for this file" works

**Done when:** She's genuinely useful while you're in VS Code.

---

### 🎨 Phase 7 — UI Polish
*"Make her feel premium."*

- [ ] Daily brief card on startup (weather, tasks, GitHub, email count)
- [ ] Chat UI with markdown + code highlighting
- [ ] Minimal system HUD (CPU, RAM overlay)
- [ ] Memory viewer ("here's what I know about you")
- [ ] Settings panel (voice, theme, Groq key, workspace path)
- [ ] Smooth animations (Framer Motion)

**Done when:** It looks and feels like a product, not a project.

---

## 💬 Example Interactions (Post-MVP)

```
You: "I want to watch something funny"
Lucy: [searches YouTube headless] "Playing a trending comedy video."

You: "What was I working on yesterday?"
Lucy: [reads Firebase memory] "Yesterday you worked on the fee management 
       module in Rising Oak Academy for about 3 hours."

You: "Find that invoice PDF from last week"
Lucy: [searches Downloads + Documents] "Found invoice_client_nov.pdf 
       in your Downloads. Want me to open it?"

You: "My screen has an error, fix it"
Lucy: [takes screenshot → vision LLM] "I see a TypeError on line 42. 
       The variable `userData` is undefined. Want me to add a null check?"

You: "Start my coding session"
Lucy: [opens VS Code, Spotify lo-fi, closes Discord] 
      "You're set. Spotify is playing lo-fi. Discord is closed. 
       Last you were on: Rising Oak, fee module. Good luck."
```

---

## 🚀 Advanced Intent Upgrades (Cognitive Architecture)

To make Lucy feel like an intelligent, next-generation agent, she will incorporate the following advanced capabilities:

1. **Multi-Step Tool Chaining (ReAct Pattern):** The brain uses a reasoning loop. If a request requires multiple steps (e.g., "Find my invoice note, compile to PDF, and email it"), she calls search, read, and email tools sequentially, feeding outputs into the next step.
2. **Sandbox Python Code Interpreter (`PythonExecutionTool`):** Lucy can write and run local Python scripts to manipulate data, parse complex files, or generate custom charts/plots (displayed directly in the React UI).
3. **Self-Correction & Fallbacks:** When a tool fails, Lucy evaluates the error and tries alternative paths (e.g., if a desktop app won't launch, she falls back to web-based automation).
4. **Vision-Based GUI Control:** By matching screenshots with vision LLM coordinates, Lucy can locate elements visually (e.g., a "Close" button on a popup) and perform OS-level clicks.
5. **Proactive Semantic Memory:** Using vector embeddings / Firestore indexing, Lucy maps preferences, habits, and details implicitly (e.g., "user likes dark mode in the evening") and proactively applies them.
6. **Duplex Interruptible Voice:** Low-power microphone monitoring while speaking allows users to interrupt Lucy mid-sentence to cancel and redirect her.

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Groq free tier rate limits | Cache frequent responses, batch where possible |
| LLM picks wrong tool | Clear tool descriptions + few-shot examples in system prompt |
| Whisper slow on low-end CPU | Run whisper tiny/base model, push-to-talk only |
| Firebase free tier limits | Summarize old sessions instead of storing raw logs |
| Headless browser detected / blocked | Use real user-agent, stealth Playwright settings |
| Privacy (screenshots) | Screenshots never leave device unless user explicitly asks |

---

## 📋 Locked Decisions

| Decision | Choice | Reason |
|---------|--------|--------|
| Name | **Lucy AI** | — |
| LLM | **Groq** (llama-3.3-70b) | Free, fast, supports tool use |
| Desktop | **Tauri** | Lighter than Electron |
| TTS | **Kokoro TTS** | Local, free, natural voice |
| STT | **Whisper** (local) | Free, accurate, offline |
| Memory | **Firebase Firestore** | Free tier, cloud sync, auth included |
| Auth | **Firebase Auth** | Google sign-in, free |
| Browser | **Playwright headless** | Silent background automation |
| Architecture | **Intent-based tool use** | No hardcoded command mapping |
| Workspace | **Dedicated `/workspace` folder** | Lucy's own scratch space |

---

## 🗓️ Timeline

| Week | Phase | Milestone |
|------|-------|-----------|
| 1 | 0 + 1 | Lucy boots, chats, uses tools |
| 2 | 2 + 3 | File ops + Firebase memory |
| 3 | 4 | Vision — she can see your screen |
| 4 | 5 | Voice — hands-free Lucy |
| 5 | 6 | Coding assistant |
| 6 | 7 | UI polish, daily brief, ship it |

---

*v2.0 — Lucy AI Master Plan | All decisions locked. Ready to build.*
*Next step → Phase 0: Boot the skeleton.*
