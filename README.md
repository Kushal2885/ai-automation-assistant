# AI Automation Assistant

A browser-based AI assistant that accepts natural-language coding tasks or code snippets, generates a clear response, and safely executes the resulting Python code — all in one interface.

Built with **Python**, **Streamlit**, and the **Google Gemini API**.

---

## What It Does

| Feature | Detail |
|---|---|
| Natural-language input | Ask coding questions or paste code to analyze |
| AI explanation | Plain-English description of the response |
| Code generation | Syntax-highlighted Python code panel |
| Safe execution | Runs code in an isolated subprocess with a timeout |
| Error display | Clear, readable error messages when execution fails |
| Multi-turn conversation | Remembers the last 10 exchanges for follow-up questions |

---

## Project Structure

```
ai-automation-assistant/
├── app.py              # Streamlit UI and main orchestration
├── ai_handler.py       # Gemini API calls and response parsing
├── code_executor.py    # Safe subprocess-based code execution
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .env                # Your actual secrets (not committed)
├── .gitignore          # Git exclusion rules
└── README.md
```

---

## Prerequisites

- Python 3.10 or higher
- A Google Gemini API key (free tier available — [get one here](https://aistudio.google.com/app/apikey))

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-automation-assistant.git
cd ai-automation-assistant
```

### 2. Create and activate a virtual environment

```bash
# Create
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate.bat

# Activate (macOS / Linux)
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` in any text editor and replace the placeholder with your actual Gemini API key:

```
GEMINI_API_KEY=AIza...your-key-here...
GEMINI_MODEL=gemini-3.6-flash
```

**How to get a Gemini API key (free):**
1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API key**
4. Copy the key and paste it into your `.env` file

### 5. Run the application

```bash
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`). Open it in your browser.

---

## Usage Examples

Try these inputs in the assistant:

- `Write a function that checks if a number is prime`
- `Generate a list of the first 20 Fibonacci numbers`
- `What does this code do: for i in range(10): print(i * i)`
- `Find the bug: def add(a, b) return a + b`
- `Sort a list of dictionaries by a key called 'age'`

---

## Safety Notes

The code executor blocks the following before running any code:

- Writing or deleting files
- Running shell commands (`os.system`, `subprocess`)
- Network requests (`requests`, `urllib`, `socket`)
- Dynamic code execution (`eval`, `exec`)
- Spawning threads or processes

Execution is automatically killed after **10 seconds** to prevent infinite loops.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | Your Google Gemini API key |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Model to use (`gemini-3.6-flash`, `gemini-2.5-flash`, `gemini-2.5-pro`) |

---

## Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit 1.36 |
| AI | Google GenAI Python SDK — `google-genai` (gemini-3.6-flash) |
| Execution | Python `subprocess` + `tempfile` |
| Config | `python-dotenv` |

---

## Troubleshooting

**"Gemini API key not found"**  
→ Make sure you created `.env` (not just `.env.example`) and it contains `GEMINI_API_KEY=<your-key>`.

**"Invalid or unauthorised Gemini API key"**  
→ Double-check that you copied the full key from [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey). Keys start with `AIza`.

**"ModuleNotFoundError"**  
→ Make sure your virtual environment is activated and you ran `pip install -r requirements.txt`.

**Streamlit command not found**  
→ Run `pip install streamlit` or ensure the venv is activated.

**Code execution is blocked**  
→ The generated code contains a pattern the safety scanner flags (e.g., file writes, network calls). This is expected behavior for the sandbox.
