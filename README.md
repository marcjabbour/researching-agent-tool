# Research Agent Tool

An AI-powered research assistant that provides transparent, multi-modal research capabilities with real-time progress tracking and comprehensive result analysis.

## 🚀 Overview

The Research Agent Tool is a sophisticated research platform that combines LangGraph workflow orchestration with real-time web search and AI-powered analysis. It's designed to handle various types of research queries from simple fact-checking to comprehensive investment memos, with full transparency into the research process.

### Key Features

- **Intelligent Intent Detection**: Automatically classifies queries into research types (fact, profile, compare, memo)
- **Adaptive Research Strategies**: Generates custom research plans based on query complexity and intent
- **Parallel Task Execution**: Runs multiple research tasks simultaneously for efficiency
- **Real-time Progress Tracking**: Live updates via WebSocket connections
- **Transparent Research Process**: Full visibility into reasoning, sources, and methodology
- **Modern Web Interface**: React-based UI with real-time updates and session management
- **Comprehensive Dashboard**: Track research history, statistics, and session details

## 🏗️ Architecture

The system follows a modular, node-based architecture using LangGraph for workflow orchestration:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │   FastAPI API   │    │  LangGraph Core │
│   (Next.js)     │◄──►│   (Python)      │◄──►│   Workflow      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   SQLite DB     │    │  Research Nodes │
                    │   (Sessions)    │    │  (Processing)   │
                    └─────────────────┘    └─────────────────┘
```

### Core Components

#### 1. **LangGraph Workflow** (`app.py`)
- **Intent Detection Node**: Classifies queries and extracts entities
- **Research Planning Node**: Generates custom research strategies
- **Parallel Task Execution Node**: Runs multiple research tasks concurrently
- **Web Search Node**: Handles quick fact queries with Tavily API
- **Response Formatter Node**: Synthesizes results into final responses

#### 2. **Research Transparency System** (`research_transparency/`)
- **Types**: Comprehensive data structures for research tracking
- **State Manager**: Manages research state and progress updates
- **Real-time Logging**: Captures reasoning and execution steps

#### 3. **API Layer** (`api/`)
- **FastAPI Server**: RESTful API with WebSocket support
- **Database Management**: SQLite-based session storage
- **Real-time Updates**: WebSocket connections for live progress

#### 4. **Frontend Interface** (`research-ui/`)
- **React/Next.js**: Modern web interface with TypeScript
- **Real-time Components**: Live progress tracking and updates
- **Dashboard**: Session management and analytics

#### 5. **Research Tools** (`tools/`)
- **Intent Classification**: LLM-powered query understanding
- **Research Planning**: Dynamic strategy generation
- **Task Execution**: Parallel search and analysis
- **Response Formatting**: Context-aware result synthesis

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- OpenAI API key
- Tavily API key (for web search)

### Backend Setup

1. **Clone and navigate to the repository**:
   ```bash
   git clone <repository-url>
   cd researching-agent-tool
   ```

2. **Set up a virtual environment** (recommended):
   ```bash
   # Create virtual environment
   python3 -m venv venv

   # Activate virtual environment
   source venv/bin/activate

   # You should see (venv) in your terminal prompt
   ```


3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Add your API keys to `.env`:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

5. **Run the backend server**:
   ```bash
   # Make sure your virtual environment is activated
   source venv/bin/activate  # If not already activated

   cd api
   python main.py
   ```

   The API will be available at `http://localhost:8000`

   > **Note:** Remember to activate your virtual environment (`source venv/bin/activate`) each time you open a new terminal session to work on this project.

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd research-ui
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:3000`

## 📖 Usage

### Basic Research Query

1. **Open the web interface** at `http://localhost:3000`
2. **Enter your research query** in the input field
3. **Select research depth** (Quick, Standard, Comprehensive)
4. **Click "Research"** to start the process
5. **Monitor real-time progress** as the system:
   - Detects query intent
   - Generates research strategy
   - Executes parallel tasks
   - Formats final response

### Query Types Supported

#### **Fact Queries**
- Simple factual questions
- Quick answers via Tavily search
- Example: "Who founded OpenAI?"

#### **Profile Queries**
- Comprehensive information requests
- Multi-source research and analysis
- Example: "Create a profile for Perplexity AI"

#### **Compare Queries**
- Comparative analysis between entities
- Side-by-side evaluation
- Example: "Compare OpenAI vs Anthropic"

#### **Memo Queries**
- Investment analysis and recommendations
- Structured research with conclusions
- Example: "Investment memo for investing in Perplexity AI"

### Dashboard Features

Access the dashboard at `/dashboard` to:
- **View research history** with search and filtering
- **Track session statistics** and performance metrics
- **Review detailed session logs** and execution traces
- **Export research results** and source citations

## 🔧 Configuration

### Research Depth Levels

- **Quick**: Basic facts, 1-2 sources, ~30 seconds
- **Standard**: Moderate detail, 3-5 sources, ~2 minutes
- **Comprehensive**: Full analysis, 5+ sources, ~5 minutes

### API Endpoints

#### Research Operations
- `POST /api/research` - Start new research query
- `GET /api/research/{id}` - Get research status
- `WS /ws/research/{id}` - Real-time progress updates

#### Dashboard Operations
- `GET /api/dashboard/sessions` - List recent sessions
- `GET /api/dashboard/session/{id}` - Get session details
- `GET /api/dashboard/search` - Search sessions
- `GET /api/dashboard/stats` - Get dashboard statistics
- `DELETE /api/dashboard/session/{id}` - Delete session

## 🧪 Development

### Project Structure

```
researching-agent-tool/
├── app.py                          # Main LangGraph application
├── requirements.txt                # Python dependencies
├── api/                           # FastAPI backend
│   ├── main.py                    # API server
│   ├── database.py                # Database operations
│   └── requirements.txt           # API dependencies
├── nodes/                         # LangGraph processing nodes
│   ├── intent_detection.py        # Query classification
│   ├── research_planning.py       # Strategy generation
│   ├── parallel_task_execution.py # Concurrent task processing
│   ├── web_search.py             # Quick fact search
│   └── response_formatter.py     # Result synthesis
├── research_transparency/         # Research tracking system
│   ├── types.py                  # Data structures
│   └── state_manager.py          # State management
├── tools/                        # Research utilities
│   ├── intent_identifying/       # Intent classification tools
│   ├── research_plan_generation/ # Strategy generation
│   ├── parallel_task_execution/  # Task execution helpers
│   └── response_formatter/       # Response generation
├── research-ui/                  # Next.js frontend
│   ├── src/
│   │   ├── app/                  # App router pages
│   │   ├── components/           # React components
│   │   └── lib/                  # Utilities and types
│   └── package.json              # Frontend dependencies
```

## 🔮 Future Work: RAG Integration

Given more time, I would extend the system with Retrieval-Augmented Generation (RAG). This would allow users to upload documents (e.g., PDFs, pitch decks, filings) when a company’s online presence is limited.
	•	Ingestion: Parse, chunk, and embed user documents into a vector store (e.g., pgvector, Qdrant).
	•	Retrieval: Hybrid search (dense + keyword) with citations surfaced in the UI.
	•	LangGraph Fit: Add DocumentIngestionNode and RAGRetrieverNode before the Response Formatter, ensuring uploaded evidence is merged with web results.
	•	UX: Drag-and-drop upload, per-chunk citations, and a dashboard for managing indexed docs.

This would seamlessly ground research in private material while keeping the same transparent, citation-first workflow.
