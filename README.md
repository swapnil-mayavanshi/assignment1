# AI-Powered Document Structuring & Data Extraction

## 📌 Project Overview
This project is an AI-powered ETL (Extract, Transform, Load) solution designed to transform unstructured PDF documents into structured Excel reports. 

Built for the **AI Intern Assignment**, it leverages **Google Gemini 2.0 Flash** to intelligently parse text, identify key-value pairs without rigid regex rules, and capture 100% of the document's data with context-aware comments.

## 🚀 Key Features
- **Zero-OCR Extraction:** Uses `pypdf` to directly access the text layer for higher accuracy and speed.
- **LLM-Powered Parsing:** Utilizes **Gemini 2.0 Flash** with strict JSON enforcement (`application/json`) to ensure reliable data structuring.
- **Dynamic Schema Discovery:** Automatically detects fields (e.g., "Blood Group", "Promotion Year") based on the document content rather than pre-defined hardcoded keys.
- **Context Preservation:** Captures source tags (e.g., ``) and adds them to a specific "Comments" column for data lineage.
- **Automated Excel Formatting:** Uses `pandas` to generate a clean, business-ready `.xlsx` file.

## 🛠️ Tech Stack
- **Language:** Python 3.x
- **AI Model:** Google Gemini 2.0 Flash
- **Libraries:**
  - `google-generativeai` (LLM Interface)
  - `pandas` (Data Manipulation & Excel Export)
  - `pypdf` (PDF Text Extraction)
  - `openpyxl` (Excel Engine)

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <your-folder-name>

   Configure API Key:
"
Get a free API Key from Google AI Studio.

Open app.py.

Locate the API_KEY variable and paste your key:Configure API Key:

Get a free API Key from Google AI Studio.

Open app.py.

Locate the API_KEY variable and paste your key:
API_KEY = "your_actual_api_key_here"
"# AI-Powered Document Structuring & Data Extraction

## 📌 Project Overview
This project is an AI-powered ETL (Extract, Transform, Load) solution designed to transform unstructured PDF documents into structured Excel reports. 

Built for the **AI Intern Assignment**, it leverages **Google Gemini 2.0 Flash** to intelligently parse text, identify key-value pairs without rigid regex rules, and capture 100% of the document's data with context-aware comments.

## 🚀 Key Features
- **Zero-OCR Extraction:** Uses `pypdf` to directly access the text layer for higher accuracy and speed.
- **LLM-Powered Parsing:** Utilizes **Gemini 2.0 Flash** with strict JSON enforcement (`application/json`) to ensure reliable data structuring.
- **Dynamic Schema Discovery:** Automatically detects fields (e.g., "Blood Group", "Promotion Year") based on the document content rather than pre-defined hardcoded keys.
- **Context Preservation:** Captures source tags (e.g., ``) and adds them to a specific "Comments" column for data lineage.
- **Automated Excel Formatting:** Uses `pandas` to generate a clean, business-ready `.xlsx` file.

## 🛠️ Tech Stack
- **Language:** Python 3.x
- **AI Model:** Google Gemini 2.0 Flash
- **Libraries:**
  - `google-generativeai` (LLM Interface)
  - `pandas` (Data Manipulation & Excel Export)
  - `pypdf` (PDF Text Extraction)
  - `openpyxl` (Excel Engine)

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <your-folder-name>

   Configure API Key:
"
Get a free API Key from Google AI Studio.

Open app.py.

Locate the API_KEY variable and paste your key:Configure API Key:

Get a free API Key from Google AI Studio.

Open app.py.

Locate the API_KEY variable and paste your key:
API_KEY = "your_actual_api_key_here"
"
