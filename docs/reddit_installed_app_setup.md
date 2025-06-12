# Reddit Installed App Setup Guide

## Why We Need an Installed App

Your Reddit account was created using Google login, which means it doesn't have a Reddit password. Reddit "script" apps require password authentication, but since you don't have a Reddit password, we need to use an "installed app" instead.

**Benefits of Installed App:**
- No password needed
- Works with `client_credentials` grant type
- Perfect for read-only access to public subreddits
- Exactly what our scraper needs

## Step-by-Step Setup

### 1. Go to Reddit Apps Page
- Visit https://www.reddit.com/prefs/apps
- Log in with your Google account (nicholasreichert86@gmail.com)

### 2. Create New App
Click "Create App" or "Create Another App" and fill in:

- **Name:** HuntingSightingsInstalled
- **App type:** Select **"installed app"** (NOT "script")
- **Description:** Bot for hunting/wildlife sightings - read only
- **About URL:** (leave blank)
- **Redirect URI:** http://localhost:8080

### 3. Click "Create App"
Make sure to actually click the button at the bottom!

### 4. Get Your Credentials
After creating, you'll see:
- **Client ID:** The string under "installed app" (looks like: ABC123xyz...)
- **Secret:** The string shown as "secret"

### 5. Update .env File
Replace the current Reddit credentials in your `.env` file with the new ones:

```
REDDIT_CLIENT_ID=your_new_installed_app_id
REDDIT_CLIENT_SECRET=your_new_installed_app_secret
REDDIT_USER_AGENT=installed:HuntingSightingsBot:1.0 (by /u/Fit-Indication-2067)
```

Note: Change "script:" to "installed:" in the user agent!

## Testing

After updating the credentials, run:
```bash
python scripts/test_reddit_installed_app.py
```

This should now work and show:
- Successfully obtained access token!
- Recent posts from r/14ers

## What This Means for the Scraper

The Reddit scraper will now:
- Use client_credentials authentication (no password needed)
- Have read-only access to all public subreddit data
- Be able to scrape posts and comments from r/14ers, r/coloradohikers, etc.
- Work reliably without password authentication issues
