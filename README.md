# NewsChat

NewsChat is a comprehensive news analysis platform. It features a Streamlit-based web application that allows users to explore news highlights and interact with a chatbot powered by Retrieval-Augmented Generation (RAG).

## Features

- **Highlights**: View top news stories and clusters across categories like Finance, Music, Lifestyle, and Sports.
- **Chatbot**: A conversational assistant that answers queries about news data using Weaviate as a vector database.
- **Data Pipeline**: Notebooks for data extraction, classification, and clustering of news articles.
- **RAG Integration**: Uses Google ADK and LiteLLM for intelligent news retrieval and response generation.

## Tech Stack

- **Language**: Python 3.12+
- **Web Framework**: [Streamlit](https://streamlit.io/)
- **LLM Orchestration**: [Google ADK](https://google.github.io/adk-docs/), [LiteLLM](https://github.com/BerriAI/litellm)
- **Vector Database**: [Weaviate](https://weaviate.io/)
- **Data Processing**: Pandas, Scikit-learn, Spacy
- **Integrations**: Google Sheets (via pygsheets), OpenAI, LangSmith

## Project Structure

```text
.
├── app/                    # Streamlit application source code
│   ├── __init__.py         
│   ├── main.py             # Entry point for the Streamlit app
│   ├── news_chat.py        # Core logic for the NewsChat assistant
│   ├── services.py         # Weaviate and Google Sheets service connectors
│   ├── config.py           # Environment and configuration management
│   ├── utils.py            # UI utilities
│   └── pages/              # Multi-page application structure
│       ├── __init__.py 
│       ├── 1_Highlights.py # News highlights page
│       └── 2_Chatbot.py    # RAG-powered chatbot page
│   └── .streamlit/         
│       ├── __init__.py 
│       └── config.toml     # Config options for streamlit
├── notebooks/              # Data pipeline and experimentation notebooks
│   ├── 00_utils.ipynb
│   ├── 01_data_extraction.ipynb
│   ├── 02_classify.ipynb
│   ├── 03_clustering.ipynb
│   └── 04_RAG.ipynb
├── google_key.json         # Google Service Account key (required for Sheets)
├── requirements.txt        # Project dependencies
└── README.md               # Project documentation
```

## Setup & Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd NewsChat
```

### 2. Set Up Environment
Create a `.env` file in the root directory and provide the following variables:

```env
WEAVIATE_ENDPOINT=your_weaviate_url
WEAVIATE_API_KEY=your_weaviate_api_key
SHEET_URL=your_google_sheet_url
# LiteLLM/OpenAI setup (depending on model used)
OPENAI_API_KEY=your_openai_api_key
# Langsmith setup
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=your_project_name
```

### 3. Google Credentials
Place your Google Service Account JSON key as `google_key.json` in the root directory to enable Google Sheets integration.

### 4. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Running the Application

To start the Streamlit dashboard, run:

```bash
python -m streamlit run app/main.py
```

## Notebooks

The `notebooks/` directory contains the data processing pipeline:
1. `01_data_extraction.ipynb`: Extract news from various sources.
2. `02_classify.ipynb`: Categorize articles (Sports, Lifestyle, Music, Finance).
3. `03_clustering.ipynb`: Group similar articles into story clusters.
4. `04_RAG.ipynb`: Prototype and test the RAG implementation.

## Tests

- TODO: Add unit and integration tests for core functionalities.
