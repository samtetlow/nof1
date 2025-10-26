# Railway Environment Variables Setup

## Add Your OpenAI API Key (Optional but Recommended)

Your OpenAI API key enables the ChatGPT-powered company search feature.

### Steps:

1. **Go to Railway Dashboard**
   - Visit: https://railway.app/dashboard
   - Select your `nof1` project

2. **Go to Variables Tab**
   - Click on **"Variables"** in the left sidebar

3. **Add Environment Variable**
   
   Click **"+ New Variable"** and add:
   
   **Variable Name:**
   ```
   OPENAI_API_KEY
   ```
   
   **Value:**
   ```
   your-openai-api-key-here
   ```
   
   (Use your actual OpenAI API key from https://platform.openai.com/api-keys)
   
4. **Click "Add"**

5. **Redeploy**
   - Railway will automatically redeploy with the new environment variable
   - Wait for deployment to complete

---

## How the App Uses the API Key

The backend (`app.py`) loads the config from `config.json` by default, but can also read from environment variables.

Currently, your API key is hardcoded in `config.json`. For security in production, it's better to use Railway environment variables.

### To Use Environment Variable Instead:

Add this to Railway Variables:
```
OPENAI_API_KEY=your-api-key-here
```

Then the app will use it automatically through the data sources configuration.

---

## Verify API Key is Working

After adding the environment variable and redeploying:

1. Visit: https://web-production-978ba.up.railway.app/health
2. Check the response - if ChatGPT is configured correctly, you'll see it in the logs

---

## Other Optional Environment Variables

### Database (Default: SQLite)
```
DATABASE_URL=sqlite:///./nof1.db
```

### Config Path (Default: ./config.json)
```
CONFIG_PATH=./config.json
```

---

## Security Note

⚠️ **Never commit API keys to GitHub!**

The `config.json` file with API keys should be in `.gitignore`.

For production:
- Use Railway environment variables ✅
- Keep `config.json` local only ✅

