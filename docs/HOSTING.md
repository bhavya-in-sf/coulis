# Hosting the sauce API (Fly.io, about $2 to $5 a month)

The API is one Python process with a SQLite file. It runs on one small machine that sleeps when idle.

## Once
```bash
brew install flyctl && fly auth login
cd ~/Projects/tastee
fly launch --copy-config --no-deploy          # accept the app name sauce-api (or pick one)
fly volumes create sauce_data --region sjc --size 1
fly secrets set SAUCE_ENC_KEY="$(python3 api/admin.py new-enc-key)" ANTHROPIC_API_KEY="$(cut -d= -f2- ~/.tastee/secrets/anthropic.env)"
fly deploy
```
The URL is `https://sauce-api.fly.dev`. Check it:
```bash
curl -s https://sauce-api.fly.dev/v1/health
```

## Give someone an API key
```bash
fly ssh console -C "python3 api/admin.py create-key --owner 'tester name'"
```
Send them the key and `docs/API.md`. Keys are stored hashed; a lost key is replaced, not recovered.

## Every later change
```bash
fly deploy
```

## What this does not do yet
No signup page, no billing, no email. Keys are made by hand with the command above.
