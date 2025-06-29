# Setup

## Python

```bash
python3 -m venv ./.venv
. .venv/bin/activate
pip install --upgrade pip
python3 -m pip install -r ./requirements.txt
```

## Internet Archive

```bash
ia configure
```

## Environment Variables

### Required

* *OPENAI_API_KEY*

### Optional

* *BLUESKY_HANDLE*
* *BLUESKY_PASSWORD*
