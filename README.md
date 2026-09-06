# AI Automation Assistant

A browser-based AI automation assistant built with Python and Streamlit. Users can enter a natural-language coding task, ask a question about Python code, or paste code directly into the interface. The application sends the input to the Google Gemini API, which generates an explanation, produces Python code where appropriate, and describes the expected output. Any generated Python code is then executed automatically, and the actual output is displayed alongside the AI response.

The interface is designed to be straightforward enough for non-technical users while remaining useful as a development and demonstration tool.

---

## Features

- Browser-based interface built with Streamlit
- Natural-language task input (type a request in plain English)
- Python code input and analysis (paste existing code for explanation or debugging)
- AI-powered understanding via the Google Gemini API
- AI-generated Python code displayed with syntax highlighting
- Plain-English explanation of the solution or analysis
- AI-generated expected output shown before execution
- Automatic execution of generated Python code in an isolated subprocess
- Actual execution output displayed in the browser
- Execution error capture and display
- Partial output display when code produces output before failing
- Safety scanning to block dangerous operations before execution
- Execution timeout protection (10-second limit) to prevent infinite loops
- Conversation history maintained across multiple requests within a session
- Clear button to reset the conversation and start fresh
- Input validation with a warning when the input field is submitted empty
- API key configuration through environment variables (no hard-coded secrets)

---

## How It Works

```
User Input
    |
    v
Streamlit Interface  (app.py)
    |
    v
Gemini AI Processing  (ai_handler.py)
    |
    v
Structured Response: Explanation + Generated Code + Expected Output
    |
    v
Safety Scan  (code_executor.py)
    |
    v
Python Code Execution via subprocess
    |
    v
Actual Output / Execution Error / Blocked Result
    |
    v
Result displayed in the browser
```

**User Input:** The user types a coding task, question, or pastes Python code into the text area and clicks Run.

**Streamlit Interface:** Manages application state, conversation history, and renders all response panels in the browser.

**Gemini AI Processing:** The input is sent to the Gemini API with a structured system prompt. The model always returns a response in three labeled sections: an explanation, Python code (or a marker indicating none is needed), and the expected output.

**Response Parsing:** The three sections are extracted from the API response and displayed in separate, clearly labeled panels.

**Safety Scan:** Before any code is executed, the code string is scanned against a list of blocked patterns covering file writes, shell commands, network access, dynamic execution, and system-level imports.

**Python Code Execution:** If the code passes the safety scan, it is written to a temporary file and executed in a subprocess using the same Python interpreter that runs Streamlit. stdout and stderr are captured separately.

**Result Display:** The actual output, any errors, or a blocked-execution notice is shown in the browser alongside the AI explanation and generated code.

---

## Testing Examples

The following inputs can be copied directly into the application to test its capabilities.

### Example 1: Code Generation

**Input:**

```
Write a Python program to check whether a number is prime.
```

**Expected behavior:** The AI explains the approach, generates a complete Python function, provides the expected output, and executes the code. The actual output is displayed in the browser.

---

### Example 2: Debugging

**Input:**

```
Fix this Python code:
numbers = [10, 20, 30]
print(sum(numbers)
```

**Expected behavior:** The AI identifies the missing closing parenthesis, provides the corrected code, explains the fix, and executes the corrected version to show the output.

---

### Example 3: Code Explanation

**Input:**

```
Explain this Python code step by step:
numbers = [10, 20, 30]
total = sum(numbers)
print(total)
```

**Expected behavior:** The AI explains each line in plain English. Code and expected output are provided. The code is executed and the actual result is shown.

---

### Example 4: Output Prediction

**Input:**

```
What is the output of this Python code?
x = 10
y = 20
print(x + y)
```

**Expected behavior:** The AI identifies and explains the output. The code is executed and the actual result confirms the prediction.

---

### Example 5: Code Optimization

**Input:**

```
Improve the following Python code for readability and efficiency:
numbers = [1, 2, 3, 4, 5]
result = []
for number in numbers:
    result.append(number * 2)
print(result)
```

**Expected behavior:** The AI provides an improved version using a list comprehension, explains the change, and executes the improved code to show the output.

---

### Example 6: Automation Task

**Input:**

```
Create a Python program that reads numbers from a list and calculates their average.
```

**Expected behavior:** The AI generates a complete program, explains the logic, provides the expected output, and executes the code. The actual output is displayed.

---

### Example 7: Error Handling

**Input:**

```
Write Python code that safely converts a string to an integer and handles invalid input.
```

**Expected behavior:** The AI generates code using a try/except block, explains how the error handling works, and executes the code to demonstrate the result.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application language |
| Streamlit 1.36 | Browser-based UI framework |
| Google Gemini API | AI model for understanding tasks and generating responses |
| google-genai 2.22 | Official Google GenAI Python SDK used to communicate with the Gemini API |
| python-dotenv 1.0.1 | Loads environment variables from the `.env` file at runtime |
| subprocess (stdlib) | Executes generated Python code in an isolated child process |
| tempfile (stdlib) | Creates temporary files to hold generated code before execution |

---

## Project Structure

```
ai-automation-assistant/
|
|-- app.py
|-- ai_handler.py
|-- code_executor.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- README.md
```

### File Descriptions

**app.py**
The main Streamlit application. Handles the browser UI, user input, conversation history display, response panel rendering, and application session state. Orchestrates the full flow from input to displayed result.

**ai_handler.py**
Manages all communication with the Google Gemini API. Defines the system prompt that instructs the model to return structured responses. Loads the API key from the environment, constructs the conversation history, sends the request, and parses the response into its three components (explanation, code, expected output).

**code_executor.py**
Handles Python code execution. Scans generated code against a list of blocked patterns before execution. If the code passes, it is written to a temporary file and run in a subprocess with a 10-second timeout. Captures stdout, stderr, and the exit code, then returns a structured result.

**requirements.txt**
Lists the three direct Python dependencies with pinned versions: `streamlit`, `google-genai`, and `python-dotenv`.

**.env.example**
A template showing which environment variables are required. Copy this file to `.env` and fill in your actual Gemini API key. The `.env` file is never committed to the repository.

**.gitignore**
Prevents sensitive and local files from being committed to Git. Excludes `.env`, `venv/`, `__pycache__/`, and editor/OS-generated files.

**README.md**
This file.

---

## Setup and Installation

### Prerequisites

- Python 3.10 or higher
- A Google Gemini API key — free tier available at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/your-username/ai-automation-assistant.git
cd ai-automation-assistant
```

**2. Create a virtual environment**

```bash
python -m venv venv
```

**3. Activate the virtual environment**

Windows (PowerShell):
```
venv\Scripts\Activate.ps1
```

Windows (Command Prompt):
```
venv\Scripts\activate.bat
```

macOS / Linux:
```bash
source venv/bin/activate
```

**4. Install dependencies**

```bash
pip install -r requirements.txt
```

**5. Create the environment file**

Windows:
```
copy .env.example .env
```

macOS / Linux:
```bash
cp .env.example .env
```

**6. Configure your API key**

Open `.env` in a text editor and set your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```

**7. Start the application**

```bash
streamlit run app.py
```

**8. Open the browser**

Streamlit will print a local URL in the terminal, typically `http://localhost:8501`. Open that URL in any browser.

---

## Configuration

The application reads its configuration from a `.env` file in the project root.

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | None | Your Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-3.6-flash` | The Gemini model to use |

The `.env` file is excluded from version control via `.gitignore`. Never commit it to a repository or share its contents publicly.

---

## Code Execution Safety

The code executor implements a prototype-grade safety layer appropriate for a demonstration environment.

**What is implemented:**

- A list of blocked patterns is scanned using regular expressions before any code is executed. Blocked categories include: file writes and deletes, shell command execution (`os.system`, `subprocess`), network access (`requests`, `urllib`, `socket`, `http`), dynamic code execution (`eval`, `exec`), system-level imports (`ctypes`, `multiprocessing`, `threading`), and dynamic imports (`__import__`).
- Code that passes the scan is executed in a subprocess isolated from the main Streamlit process. A crash or exception in the executed code cannot affect the running application.
- A 10-second timeout is enforced. If the code does not complete within that limit, the process is terminated and an appropriate message is returned.
- stdout and stderr are captured separately and returned to the UI.

**Important limitation:** This is a pattern-matching safety layer, not a fully isolated sandbox. It is suitable for a prototype or demonstration but is not appropriate for production use with untrusted code. A production system would require container-based isolation such as Docker or gVisor.

---

## Development Notes

This project was developed with the assistance of Kiro AI, an AI-powered development environment. Kiro was used to assist with project structure, implementation, debugging, testing, code cleanup, documentation, and development workflow. The design decisions, requirements, and review of all changes were carried out by the developer throughout the process.

---

## Testing Checklist

Use the following checklist to verify the application is working correctly:

- [ ] Enter a natural-language coding task and click Run
- [ ] Verify the AI explanation panel appears
- [ ] Verify the generated code panel appears with syntax highlighting
- [ ] Verify the expected output panel appears
- [ ] Verify the actual execution output panel appears
- [ ] Submit an empty input and verify the warning message appears
- [ ] Enter code that produces a runtime error and verify the error is displayed
- [ ] Enter code that triggers a blocked pattern and verify the blocked notice appears
- [ ] Click Clear and verify the conversation and output are reset
- [ ] Enter a follow-up request and verify conversation history is maintained
- [ ] Run multiple consecutive requests and verify each produces a correct response

---

## Limitations

- The code execution safety mechanism is a prototype-grade pattern scanner. It is not a fully isolated sandbox and should not be used as-is in a production environment with untrusted input.
- Gemini API availability, response quality, and rate limits depend on the configured API key and the associated Google account quota.
- The application is focused on Python-oriented coding tasks. Requests for other programming languages will receive a Python equivalent rather than code in the requested language.
- Conversation history is held in Streamlit session state and is not persisted between browser sessions. Refreshing the page resets the conversation.
- Code that requires interactive user input at runtime (e.g., `input()`) will not work in the execution sandbox, as stdin is not connected.

---

## Future Improvements

The following are potential improvements for future iterations of this project. None of these are currently implemented.

- Container-based code execution sandbox (Docker or gVisor) for stronger isolation
- Support for additional programming languages
- File upload and processing capability
- Persistent conversation storage across sessions
- User authentication and session management
- More advanced automation workflow support
- Deployment to a cloud environment (e.g., Streamlit Community Cloud, GCP, AWS)

---

## License

License information has not been specified for this project yet.
