
# Streamlit App Setup

This guide will help you set up and run the Streamlit app.

## Prerequisites

- **Python 3.10+** installed on your system
- **`requirements.txt`** and **`app.py`** present in the project directory
- **`.streamlit/`** directory with `secrets.toml` for storing sensitive keys

## Setup Instructions

1. **Create and Activate Virtual Environment**

   Create a virtual environment using Python 3.10:

   ```bash
   python3.10 -m venv venv
   ```

   Activate the virtual environment:

   - **macOS/Linux**:

     ```bash
     source venv/bin/activate
     ```

   - **Windows**:

     ```bash
     venv\Scripts\activate
     ```

2. **Install Dependencies**

   With the virtual environment activated, install dependencies from `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

3. **Add Secrets**

   In the root directory, create a `secrets.toml` file to store your API keys. For example:

   ```toml
   [general]
   OPENAI_API_KEY = "your-openai-api-key"
   ```

4. **Run the App**

   Start the Streamlit app:

   ```bash
   streamlit run app.py
   ```

## Deactivating the Virtual Environment

When you’re finished, deactivate the virtual environment:

```bash
deactivate
```
