# Credentials Setup for Claude Code

Since Claude Code (web UI) can only access files from GitHub, credentials are managed via **environment variables** instead of credential files.

## How It Works

All credential loader functions in the code check for environment variables first, then fall back to local credential files (for local development):

```python
# Example: Canny API
api_key = os.environ.get("CANNY_API_KEY")  # ← Claude Code gets this
if not api_key:
    api_key = read_from_file()  # ← Local development uses this
```

## Setting Up Claude Code with Credentials

### Option 1: Claude Code Web UI (Recommended for you)

Since you're using Claude Code web UI without an API token, set environment variables directly:

1. **Get your API credentials:**
   - Canny: `CANNY_API_KEY`
   - Zendesk: `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN`
   - Google: See steps below
   - Anthropic: `ANTHROPIC_API_KEY`

2. **In Claude Code web UI:**
   - Claude Code should allow you to set environment variables in settings or via a `.env` file
   - Create a `.env` file (NOT in GitHub) with your credentials
   - Claude Code will read from it

### Option 2: Local Development

If you're running code locally, use the credential files as before:
```
~/canny/credentials/api_key
~/zendesk/credentials/subdomain (+ email, api_token)
~/google-services/credentials/client_secret.json
~/google-services/credentials/token.json
```

## Required Environment Variables

| Service | Variable(s) | 
|---------|----------|
| **Canny** | `CANNY_API_KEY` |
| **Zendesk** | `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN` |
| **Google** | Use OAuth flow or `GOOGLE_APPLICATION_CREDENTIALS` |
| **Anthropic** | `ANTHROPIC_API_KEY` |

## Security

✅ All `.env` files are in `.gitignore` (never committed)
✅ Credentials stay in your environment, not in GitHub
✅ Code reads from environment variables first
