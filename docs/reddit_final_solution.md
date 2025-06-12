# Reddit API - Final Solution

## Current Status
- Password authentication is failing with 401 error
- This means either the password is wrong, 2FA is enabled, or the app ownership is mismatched
- Since we only need read-only access, we should use an "installed app" instead

## Solution: Create an Installed App

### Step 1: Create New Reddit App
1. Go to https://www.reddit.com/prefs/apps
2. Log in with your Reddit account (Fit-Indication-2067)
3. Click "Create App" or "Create Another App"
4. Fill in:
   - **Name:** HuntingSightingsReadOnly
   - **App type:** Select **"installed app"** (NOT "script")
   - **Description:** Read-only bot for wildlife sightings
   - **About URL:** (leave blank)
   - **Redirect URI:** http://localhost:8080
5. Click "Create app"

### Step 2: Get New Credentials
After creating, you'll see:
- **Client ID:** The string under "installed app" 
- **Secret:** The string shown as "secret"

### Step 3: Update .env File
Replace the Reddit section in your `.env` file:
```
# Reddit API Configuration
REDDIT_CLIENT_ID=your_new_installed_app_id
REDDIT_CLIENT_SECRET=your_new_installed_app_secret
REDDIT_USER_AGENT=installed:HuntingSightingsBot:1.0 (by /u/Fit-Indication-2067)
```

Note: Change "script:" to "installed:" in the user agent!

### Step 4: Test with curl
```bash
curl -X POST https://www.reddit.com/api/v1/access_token \
  -H "User-Agent: installed:HuntingSightingsBot:1.0 (by /u/Fit-Indication-2067)" \
  -u "NEW_CLIENT_ID:NEW_CLIENT_SECRET" \
  -d "grant_type=client_credentials"
```

This should return:
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 3600,
  "scope": "read"
}
```

### Step 5: Test with Python
Run:
```bash
python scripts/test_reddit_installed_app.py
```

## Why This Works Better

1. **No password needed** - Uses client_credentials grant
2. **No 2FA issues** - Doesn't require user authentication
3. **Perfect for our use case** - Read-only access to public subreddits
4. **More reliable** - No password sync issues

## What This Gives You

- Read access to all public subreddits
- Ability to fetch posts and comments
- Extract wildlife sightings from r/14ers, r/coloradohikers, etc.
- No ability to post (which we don't need)

## If You Still Want Password Auth

If you absolutely need password authentication:
1. Log into Reddit.com with username/password to verify it works
2. Check if 2FA is enabled (User Settings → Safety & Privacy)
3. If 2FA is on, disable it
4. If password doesn't work, set a new one (User Settings → Account → Change password)
5. Verify the app is owned by Fit-Indication-2067 at https://www.reddit.com/prefs/apps
