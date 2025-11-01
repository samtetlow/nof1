# 🔒 How to Set Up API Keys Safely

## ⚠️ NEVER Put API Keys Directly in Code!

API keys should NEVER be:
- ❌ Hard-coded in Python files
- ❌ Committed to GitHub
- ❌ Shared in chat messages
- ❌ Posted in public places

---

## ✅ The RIGHT Way: Use Environment Variables

### **For Production (Railway)**

1. **Get a NEW API Key** (if you posted yours publicly, revoke it first!)
   - Go to: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the key (starts with `sk-...`)

2. **Add to Railway**
   - Railway Dashboard → Your Project
   - Click **"Variables"** tab
   - Click **"+ New Variable"**
   - Name: `OPENAI_API_KEY`
   - Value: `sk-...your-key...`
   - Click "Add"

3. **Railway auto-deploys** (wait 1-2 minutes)

4. **Test it works**
   - Visit: `https://your-railway-url.up.railway.app/docs`
   - Should load without errors

---

### **For Local Development**

**Option A: Create config.json (Recommended)**

1. **Copy the example:**
   ```bash
   cd /Users/samtetlow/Cursor/nof1
   cp config.json.example config.json
   ```

2. **Edit config.json:**
   ```json
   {
     "chatgpt": {
       "api_key": "sk-...your-key...",
       "model": "gpt-3.5-turbo"
     },
     "anthropic": {
       "api_key": "your-anthropic-key-if-you-have-one"
     }
   }
   ```

3. **This file is in .gitignore** - it won't be committed!

**Option B: Use Environment Variable**

```bash
export OPENAI_API_KEY="sk-...your-key..."
python app.py
```

Or add to your shell profile:
```bash
echo 'export OPENAI_API_KEY="sk-...your-key..."' >> ~/.zshrc
source ~/.zshrc
```

---

## 🔐 How the App Loads API Keys

The app checks in this order:

1. **Environment variable** `OPENAI_API_KEY` (Railway uses this)
2. **config.json file** (for local development)
3. **Falls back to None** (API features won't work)

This is handled in `app.py` around line 48-67:

```python
def load_config() -> Dict[str, Any]:
    config = {}
    
    # Try to load from config.json first
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text())
    
    # Override with environment variables if present
    if os.getenv("OPENAI_API_KEY"):
        if "chatgpt" not in config:
            config["chatgpt"] = {}
        config["chatgpt"]["api_key"] = os.getenv("OPENAI_API_KEY")
    
    return config
```

---

## 🆘 If You Posted Your API Key Publicly

### **Immediate Steps:**

1. **Revoke the key**
   - Go to: https://platform.openai.com/api-keys
   - Find the compromised key
   - Click "Revoke" or "Delete"

2. **Generate a new key**
   - Click "Create new secret key"
   - Copy it immediately
   - Store it securely

3. **Add new key to Railway**
   - Railway Dashboard → Variables
   - Update `OPENAI_API_KEY` with new key

4. **Check for unauthorized usage**
   - Go to: https://platform.openai.com/usage
   - Look for suspicious activity
   - Contact OpenAI support if needed

---

## ✅ Security Checklist

- [ ] API key is in Railway Variables (not in code)
- [ ] config.json is in .gitignore (and not committed)
- [ ] No API keys in any .py files
- [ ] No API keys in git history
- [ ] Old keys have been revoked
- [ ] New keys are stored securely

---

## 📖 For Reference

- **Railway Variables Documentation**: https://docs.railway.app/develop/variables
- **OpenAI API Keys**: https://platform.openai.com/api-keys
- **Environment Variables Best Practices**: Never commit secrets!

---

## 🎯 Summary

**Production (Railway):**
```
Railway Dashboard → Variables → Add OPENAI_API_KEY
```

**Local Development:**
```bash
# Create config.json (already in .gitignore)
cp config.json.example config.json
# Edit config.json with your key
```

**Never:**
```python
# ❌ DON'T DO THIS!
api_key = "sk-..." 
```

---

**Your API keys are valuable - protect them like passwords!** 🔒

