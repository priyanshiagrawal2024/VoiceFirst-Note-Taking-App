# 🎙️ VoiceFirst: Accessible AI Voice Note-Taking & Study Companion

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask 3.0](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![Flutter 3.x](https://img.shields.io/badge/Frontend-Flutter%20Web-02569B.svg)](https://flutter.dev/)
[![Accessibility](https://img.shields.io/badge/Accessibility-WCAG%202.1%20AAA-gold.svg)](https://www.w3.org/WAI/standards-guidelines/wcag/)
[![Tests](https://img.shields.io/badge/Tests-100%25%20Passing-brightgreen.svg)]()

> **VoiceFirst** is an inclusive, hands-free voice note-taking and revision platform specially engineered for **blind and visually impaired students**. Featuring a **Dual-Modality Architecture**, the app combines non-visual auditory sonification and screen-reader semantics for visually impaired users with accessible high-contrast visual graphs and progress charts for sighted educators and evaluators.

---

## 🌟 Key Features

- 🎙️ **Hands-Free Active Lecture Recording**: Dictate notes naturally; the system auto-detects academic subjects (*Biology, Geography, Computer Science, Chemistry, Physics, Mathematics*) and categorizes notes into *Definitions, Important Exam Points, Examples,* or *General*.
- ✏️ **Voice-Only Word Correction**: Replace speech-recognition mistakes completely hands-free (*"Correct decision to division"*).
- 🔍 **Targeted Voice Retrieval & Search**: Search and jump between notes verbally (*"Find my notes about Mitosis"*, *"Next"*, *"Previous"*, *"Repeat"*).
- 🃏 **Audio Flashcards**: Hands-free card revision with vocal flip and next commands (*"Start flashcard revision for Biology"*, *"Flip card"*).
- 📝 **Verbal Exam & Quiz Mode**: Spoken multiple-choice questions with verbal answers and scoring (*"Quiz me on everything important"*).
- 📊 **Accessible Study Analytics & Visual Graphs**:
  - **Subject Distribution Bar Charts** with icons, note counts, and percentage breakdowns.
  - **Tag Classification Breakdown** (Important, Definition, Example, General).
  - **Interactive Knowledge Concept Map** linking connected academic concepts.
  - **Audio Sonification Report** button reading out the entire statistical summary.
- 🗂️ **Recent Recordings & Deletion**: Dedicated screen to filter notes by subject, listen to audio recordings, and delete unwanted entries.
- ⌨️ **Tactile Accessibility**:
  - <kbd>Spacebar</kbd> = Global toggle for microphone / interrupt speech.
  - <kbd>Escape</kbd> = Immediate silence / stop audio playback.
  - Minimum **56dp** touch targets and **WCAG 2.1 AAA** high-contrast gold/black palette (`#121212`, `#FFD700`).

---

## 📋 Prerequisites

Before running the application, make sure you have installed:

1. **Python 3.10+** (with pip)
2. **Flutter SDK (3.x)** & **Google Chrome**
3. **Git**

---

## 🚀 How to Run the App

### Option 1: One-Click Launcher (Windows)

Double-click the **`run_app.bat`** file in the root folder:
- Automatically starts the **Flask Backend** on `http://127.0.0.1:5000`
- Automatically starts the **Flutter Chrome Frontend** on `http://localhost:3000`

---

### Option 2: Manual Setup via VS Code / Terminal

#### Step 1: Start the Backend (Terminal 1)

```powershell
# Navigate to the backend directory
cd backend

# (Optional) Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required Python packages
pip install -r requirements.txt

# Start the Flask API server (runs on port 5000)
python app.py
```
> Verify backend health at: `http://127.0.0.1:5000/api/health`

#### Step 2: Start the Frontend (Terminal 2)

```powershell
# Navigate to the frontend directory
cd frontend

# If flutter is not in your PATH, add your Flutter bin path first:
$env:Path = "C:\src\flutter\flutter\bin;" + $env:Path

# Install Flutter dependencies
flutter pub get

# Launch the app on Chrome (port 3000)
flutter run -d chrome --web-port=3000
```

The application will automatically launch in Google Chrome at **`http://localhost:3000`**.

---

## 🗣️ Voice Commands Quick Reference

Tap the microphone icon or press <kbd>Spacebar</kbd>, then speak any of these commands:

| Feature | Example Voice Command | What Happens |
|---|---|---|
| **Start Lecture** | *"Start Biology lecture."* | Begins a new lecture recording session for Biology |
| **Capture Note** | *"Note: Mitosis is cell division in eukaryotic cells."* | Stores note, auto-tags as Definition/Important |
| **Voice Correction** | *"Correct decision to division."* | Replaces misrecognized word in the last note |
| **Search Notes** | *"Find my notes about Mitosis."* | Retrieves relevant notes and reads out the top match |
| **Browse Results** | *"Next"* / *"Previous"* / *"Repeat"* | Navigates through search or review results hands-free |
| **Flashcards** | *"Start flashcard revision for Biology."* | Opens audio flashcards for that subject |
| **Flip Card** | *"Flip card"* / *"Turn card"* | Flips between front (prompt) and back (answer) |
| **Exam Quiz** | *"Quiz me on everything important."* | Generates a verbal MCQ quiz from your notes |
| **Answer Quiz** | *"Option A"* / *"Option B"* | Evaluates answer and reads explanation out loud |
| **Study Analytics** | *"Show my analytics."* or *"Show graphs."* | Opens visual charts & reads audio sonification report |
| **Recent Recordings**| *"Open recents."* | Opens the Recents screen to review or delete notes |
| **Delete Note** | *"Delete last note."* | Removes the last recorded note with voice confirmation |
| **Go Home** | *"Go home."* / *"Back to home."* | Returns to the main home dashboard |

---

## 🏗️ Architecture & Technology Stack

```
VoiceFirst/
├── backend/                  # Python Flask Microservice
│   ├── app.py                # REST API & Voice Intent Router
│   ├── database.py           # SQLite persistence layer
│   ├── services/
│   │   ├── intent_parser.py  # Regex & Semantic Voice Intent Parser
│   │   ├── note_service.py   # Note classification & analytics aggregation
│   │   ├── search_service.py # Ranked fuzzy & keyword search
│   │   ├── quiz_service.py   # Spoken MCQ evaluation engine
│   │   ├── flashcard_service.py # Audio flashcard generator
│   │   └── gemini_service.py # Optional hybrid LLM integration
│   └── tests/                # 22 automated Pytest verification tests
│
└── frontend/                 # Flutter Web Application
    ├── lib/
    │   ├── core/services/    # TTS, STT, and Dialogue Management
    │   ├── providers/        # State management (Provider)
    │   ├── screens/          # Accessible UI screens
    │   │   ├── home_screen.dart
    │   │   ├── active_lecture_screen.dart
    │   │   ├── voice_retrieval_screen.dart
    │   │   ├── flashcards_screen.dart
    │   │   ├── quiz_screen.dart
    │   │   ├── recents_screen.dart
    │   │   └── analytics_screen.dart # Visual charts & sonification
    │   └── widgets/          # WCAG 2.1 AAA accessible buttons & widgets
    └── test/                 # 17 automated Flutter widget/unit tests
```

---

## 🧪 Running Automated Tests

All tests are guaranteed to pass 100%:

### Backend Tests (22 Tests)
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Tests (17 Tests)
```bash
cd frontend
flutter test
```

---

## 💡 Troubleshooting

- **Error: `The term 'flutter' is not recognized`**:
  Run `$env:Path = "C:\src\flutter\flutter\bin;" + $env:Path` in PowerShell before running `flutter`.
- **Error: `Port 3000 or 5000 already in use`**:
  Close previous instances or run `Stop-Process -Name dartvm, python -Force` in PowerShell.
- **Microphone Permission**:
  Ensure you grant Chrome permission to use the microphone when prompted at `http://localhost:3000`.

---

## 👥 Contributors & Collaboration

- **Lead Developer**: Priyanshi
- Feel free to submit a Pull Request or open an Issue for new accessibility features!
