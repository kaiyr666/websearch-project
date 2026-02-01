# Job Search Agent 🚀

A modern, AI-powered job search assistant that helps you find the perfect role by analyzing your resume and matching it against real-time job postings.

## 🌟 Key Features

-   **Resume Analysis**: Upload one or multiple resumes to extract key skills and experiences.
-   **Smart Job Search**: Uses SerpAPI to find the latest job postings based on your desired roles and location.
-   **AI-Powered Matching**: GPT-4o analyzes job descriptions and provides a match score (0-100) with detailed justification.
-   **Interactive Chat**: Seamless conversational interface built with React.
-   **Search History**: Access results from your previous searches instantly through the sidebar.
-   **Premium UI**: A sleek, dark-themed interface with smooth animations and responsive design.

## 🛠 Tech Stack

### Frontend
-   **React 18** with **TypeScript**
-   **Vite** (Build tool)
-   **Tailwind CSS** (Styling)
-   **Lucide React** (Icons)
-   **Axios** (API requests)

### Backend
-   **FastAPI** (Python)
-   **SQLite** with **aiosqlite** (Database)
-   **PyPDF** (Resume parsing)
-   **Uvicorn** (ASGI Server)

### AI & External Services
-   **OpenAI GPT-4o**: For resume parsing and job description matching.
-   **SerpAPI**: Real-time Google job search data.
-   **Jina Reader**: high-quality web content extraction for job details.

## 🏗 Architecture

The project follows a classic client-server architecture:
1.  **Client**: A React SPA that handles user interactions, file uploads, and displays search results.
2.  **Server**: A FastAPI hub that orchestrates searching, parsing, and AI analysis.
3.  **Database**: SQLite stores your search history and processed job matches.
4.  **Services**: Specialized modules for Jina, SerpAPI, and OpenAI.

## 📂 Project Structure

```text
websearch project/
├── frontend/               # React Application
│   ├── src/
│   │   ├── components/     # UI Components (ChatInterface, etc.)
│   │   └── ...
│   └── package.json
├── backend/                # FastAPI Application
│   ├── database/           # SQLite DB and helper functions
│   ├── services/           # External API integrations
│   ├── main.py             # Main entry point
│   └── requirements.txt
└── .env                    # API Keys (Root & Backend)
```

## 🚀 Getting Started

### Prerequisites
-   [Python 3.9+](https://www.python.org/downloads/)
-   [Node.js 18+](https://nodejs.org/)
-   API Keys for OpenAI, SerpAPI, and Jina.

### 1. Backend Setup
1.  Navigate to the backend directory:
    ```bash
    cd "websearch project/backend"
    ```
2.  Create and activate a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    # source venv/bin/activate  # macOS/Linux
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure `.env` file (see [Environment Variables](#environment-variables)).
5.  Start the server:
    ```bash
    python -m uvicorn main:app --reload
    ```
    The API will be available at `http://localhost:8000`.

### 2. Frontend Setup
1.  Navigate to the frontend directory:
    ```bash
    cd "websearch project/frontend"
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
    The app will be available at `http://localhost:5173`.

## 🔑 Environment Variables

Create a `.env` file in the `backend/` directory with the following keys:

| Key | Description |
| :--- | :--- |
| `OPENAI_API_KEY` | Your OpenAI API key for analysis. |
| `SERPAPI_API_KEY` | Key for Google Job Search via SerpAPI. |
| `JINA_API_KEY` | Key for Jina Reader content extraction. |
| `SYSTEM_PROMPT` | (Optional) Custom tuning for the AI agent. |

