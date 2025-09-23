# BigModel Web Search + Chat Loop Demo

This repository contains a Python script that continuously combines BigModel's
Web Search tool API with the chat completion API to analyse multiple topics in a
loop. The script is intended as a backend prototype showing how a customer could
cycle through topics, retrieve fresh search intelligence, and feed it back into
the large language model for structured insights.

## Requirements

- Python 3.9+
- The [`requests`](https://docs.python-requests.org/) library (install with
  `pip install requests` if it is not already available).
- A BigModel API key with access to both the web search tool and the selected
  chat model. For quick testing you may reuse the demo key shared in the task
  description: `b8ae5075e7fa49c0bf6f248b38de2152.8DCFTJBF5qKJH3KL`.

## Usage

```bash
# Optional: create a virtual environment
python -m venv .venv
source .venv/bin/activate
pip install requests

# Export your API key so the script can pick it up
export BIGMODEL_API_KEY="<your_api_key>"

# Run one iteration across three default topics
python bigmodel_loop.py

# Run two iterations analysing custom topics with a 5 second pause
python bigmodel_loop.py --topics "自动驾驶" "AIGC" "金融风控" --iterations 2 --delay 5
```

During execution the script prints the search-backed analysis for each topic in
sequence. Use `--iterations 0` (or any negative number) to keep the loop running
indefinitely.

Consult the official documentation for more detail on the BigModel APIs:

- Web Search API: <https://docs.bigmodel.cn/api-reference/%E5%B7%A5%E5%85%B7-api/%E7%BD%91%E7%BB%9C%E6%90%9C%E7%B4%A2>
- Chat Completion API: <https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8>
