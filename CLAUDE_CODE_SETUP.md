# Quick Claude Code Setup (Copy & Paste)

## Step 1: Set Environment Variables in Claude Code

Before running any script, paste and run this in Claude Code:

```bash
export CANNY_API_KEY="YOUR_CANNY_API_KEY"
export ZENDESK_SUBDOMAIN="YOUR_ZENDESK_SUBDOMAIN"
export ZENDESK_EMAIL="your_email@example.com"
export ZENDESK_API_TOKEN="YOUR_ZENDESK_API_TOKEN"
export ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/google-services/credentials/client_secret.json"
```

Replace the `YOUR_*` placeholders with your actual credentials.

---

## Step 2: Run Your Script

After setting the env vars, run your Python/Node script normally:

```bash
python your_script.py
```

or

```bash
node your_script.js
```

---

## Step 3: (Optional) Create a .env File Locally

If you prefer, create a `.env` file **locally on your machine** (NOT in GitHub):

```bash
CANNY_API_KEY=your_canny_api_key
ZENDESK_SUBDOMAIN=your_zendesk_subdomain
ZENDESK_EMAIL=your_email@example.com
ZENDESK_API_TOKEN=your_zendesk_api_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

Then load it before running:

```bash
source .env
python your_script.py
```

---

## Where to Get Your Credentials

| Credential | Where to Find |
|-----------|--------------|
| `CANNY_API_KEY` | Canny Dashboard → Settings → API |
| `ZENDESK_SUBDOMAIN` | Your Zendesk URL: `subdomain.zendesk.com` |
| `ZENDESK_EMAIL` | Your Zendesk account email |
| `ZENDESK_API_TOKEN` | Zendesk Admin → Apps → APIs → Tokens |
| `ANTHROPIC_API_KEY` | Anthropic console (api.anthropic.com) |

---

## That's It!

Your code will automatically read from these environment variables. No credentials in GitHub. 🔒
