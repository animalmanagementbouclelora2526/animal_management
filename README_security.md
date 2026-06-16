# 🔒 Google Cloud Credentials Security Guide

This guide describes how to securely manage your Google Cloud Service Account credentials to prevent leaks and configuration issues.

## 🚨 What Happened?

Your service account JSON credentials were leaked on GitHub because the project folder was uploaded manually using the **"Add files via upload"** feature on github.com. 

Manually dragging and dropping or selecting files through the GitHub website **bypasses your local `.gitignore` configuration**. It uploads all files in the folder, regardless of whether they are supposed to be ignored.

Google detected the exposure and permanently disabled the compromised key. A new key has been generated and configured locally.

---

## 🛠️ Secure Configuration locally and in production

### 1. Local Development
We updated `.gitignore` to use wildcards for JSON files:
```gitignore
*.json
!vercel.json
```
This ensures that any JSON credentials (such as `credentials.json` or `animaltracker-499320-0c2c76b1a2ff.json`) cannot be committed through git command-line tool.

> [!CAUTION]
> **NEVER** use the "Add files via upload" feature on GitHub's website to upload files or directories for this project. Always commit and push changes using Git from your command line (e.g. `git add`, `git commit`, `git push`), which guarantees that `.gitignore` is respected.

---

### 2. Production Deployment (Render)
For your deployment on Render, **do not upload any credentials files**. Render reads your credentials securely from environment variables.

To update Render with your new key:
1. Open your **Render Dashboard**.
2. Select your Web Service.
3. Click on **Environment** in the left sidebar.
4. Locate the environment variable named **`GOOGLE_CREDS`**.
5. Replace its value with the **complete contents of your new JSON key** (copy and paste the entire JSON text from your local `credentials.json` file).
6. Click **Save Changes**.

Render will automatically trigger a redeploy of your service with the new, secure environment variable, restoring connectivity to your Google Sheets.
