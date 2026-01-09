# Project Setup Guide

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Virtual environment support (included with Python 3.9+)

## Setup Instructions

### 1. Create and activate a Python virtual environment

```bash
cd ~/image-to-ai-to-stil
python3 -m venv venv
source venv/bin/activate
```

On Windows, use:
```bash
venv\Scripts\activate
```

### 2. Upgrade pip and install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Download required models

```bash
python download_model.py
```

This will download the Intel DPT Hybrid Midas model to `~/.cache/huggingface/hub/`

## Project Structure

- `download_model.py` - Script to download required Hugging Face models
- `requirements.txt` - Python dependency specifications
- `SETUP.md` - This setup guide
- `PROJECT_PLAN.md` - Detailed project plan and architecture

## Virtual Environment Management

### To activate the virtual environment (every time you work on the project):

```bash
source venv/bin/activate
```

### To deactivate the virtual environment:

```bash
deactivate
```

### To add new dependencies:

```bash
pip install <package_name>
pip freeze > requirements.txt
```

## Troubleshooting

If you encounter Python path issues, ensure you're using the virtual environment's Python:

```bash
which python
which pip
```

Both should point to your `venv/` directory.

## Notes

- Add `venv/` to `.gitignore` to prevent committing the virtual environment
- The `.cache/huggingface/` directory is only created after first running `download_model.py`
- Model downloads happen only once; subsequent runs will use the cached model