# How to Get Required Credentials

This guide will walk you through obtaining all the credentials needed for the YouTube Analytics pipeline.

## 1. YouTube API Key (YOUTUBE_API_KEY)

### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click **"New Project"**
4. Enter a project name (e.g., "YouTube Analytics")
5. Click **"Create"**

### Step 2: Enable YouTube Data API v3
1. In your project, go to **"APIs & Services"** > **"Library"**
2. Search for **"YouTube Data API v3"**
3. Click on it and click **"Enable"**

### Step 3: Create API Credentials
1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"**
3. Select **"API Key"**
4. Copy the generated API key
5. (Optional) Click **"Restrict Key"** to limit usage to YouTube Data API v3 for security

**Your API Key will look like:** `AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567`

---

## 2. YouTube Channel ID (YOUTUBE_CHANNEL_ID)

### Method 1: From YouTube Studio
1. Go to [YouTube Studio](https://studio.youtube.com/)
2. Click on **"Customization"** in the left menu
3. Click on **"Basic info"**
4. Your Channel ID is displayed under your channel name
   - Format: `UCxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Method 2: From Your Channel URL
1. Go to your YouTube channel
2. Look at the URL: `https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. The part after `/channel/` is your Channel ID

### Method 3: Using YouTube API (if you have API key)
Visit this URL (replace `YOUR_API_KEY`):
```
https://www.googleapis.com/youtube/v3/channels?part=id&mine=true&key=YOUR_API_KEY
```

**Note:** If you want to monitor a specific playlist instead, use `YOUTUBE_PLAYLIST_ID` instead of `YOUTUBE_CHANNEL_ID`

---

## 3. YouTube Playlist ID (YOUTUBE_PLAYLIST_ID) - Optional

If you prefer to monitor a specific playlist instead of a channel:

1. Go to the playlist on YouTube
2. Look at the URL: `https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. The part after `list=` is your Playlist ID

**Note:** You can use either `YOUTUBE_CHANNEL_ID` OR `YOUTUBE_PLAYLIST_ID`, not both.

---

## 4. Telegram Bot Token (TELEGRAM_BOT_TOKEN)

### Step 1: Create a Bot
1. Open Telegram and search for **[@BotFather](https://t.me/botfather)**
2. Start a chat with BotFather
3. Send the command: `/newbot`
4. Follow the prompts:
   - Choose a name for your bot (e.g., "YouTube Analytics Bot")
   - Choose a username (must end with "bot", e.g., "youtube_analytics_bot")
5. BotFather will give you a token that looks like:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890
   ```
6. **Copy and save this token** - this is your `TELEGRAM_BOT_TOKEN`

### Step 2: (Optional) Configure Bot Settings
- `/setdescription` - Set bot description
- `/setabouttext` - Set about text
- `/setuserpic` - Set bot profile picture

---

## 5. Telegram Chat ID (TELEGRAM_CHAT_ID)

### Method 1: Using @userinfobot
1. Search for **[@userinfobot](https://t.me/userinfobot)** on Telegram
2. Start a chat with it
3. It will immediately reply with your Chat ID
4. Copy the number (e.g., `123456789`)

### Method 2: Using @getidsbot
1. Search for **[@getidsbot](https://t.me/getidsbot)** on Telegram
2. Start a chat with it
3. Forward any message to it
4. It will reply with your Chat ID

### Method 3: Using Telegram API
1. Send a message to your bot
2. Visit this URL (replace `BOT_TOKEN` with your bot token):
   ```
   https://api.telegram.org/botBOT_TOKEN/getUpdates
   ```
3. Look for `"chat":{"id":123456789}` in the response
4. The number is your Chat ID

### Method 4: For Group Chats
1. Add your bot to the group
2. Send a message in the group
3. Visit: `https://api.telegram.org/botBOT_TOKEN/getUpdates`
4. Find the group chat ID (it will be negative, like `-123456789`)

**Note:** 
- Personal chat IDs are positive numbers
- Group chat IDs are negative numbers
- Make sure you've sent at least one message to your bot before checking

---

## 6. Create Your .env File

Once you have all credentials, create a `.env` file in the project root:

```env
# YouTube API Configuration
YOUTUBE_API_KEY=AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# OR use playlist ID instead:
# YOUTUBE_PLAYLIST_ID=PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890
TELEGRAM_CHAT_ID=123456789

# Pipeline Configuration (Optional - defaults shown)
POLL_INTERVAL=60
CHANGE_THRESHOLD=0.05
NOTIFICATION_THRESHOLD=0.05
```

---

## Quick Test Commands

### Test YouTube API Key:
```bash
curl "https://www.googleapis.com/youtube/v3/channels?part=snippet&id=UCp2ao9X9mlPjlMrkvg3_-fg&key=AIzaSyAieA8BXJZn1sbmtI4UfcORzjDIoXcYISI"
```

### Test Telegram Bot:
```bash
curl "https://api.telegram.org/bot8445646129:AAGqQVGyd1ZkEMHHoQ1WeAOkD9Dt1hlT_SQ/getMe"
```

### Test Telegram Chat ID:
```bash
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage?chat_id=956393829&text=Test"
```

---

## Troubleshooting

### YouTube API Issues:
- **403 Forbidden**: Check if YouTube Data API v3 is enabled
- **400 Bad Request**: Verify your API key is correct
- **Quota Exceeded**: YouTube API has daily quotas (10,000 units/day by default)

### Telegram Issues:
- **401 Unauthorized**: Check your bot token
- **400 Bad Request**: Verify your chat ID (make sure you've messaged the bot first)
- **403 Forbidden**: Make sure your bot is not blocked

---

## Security Notes

⚠️ **Important:**
- Never commit your `.env` file to version control
- Add `.env` to your `.gitignore` file
- Keep your API keys secure
- Consider restricting your YouTube API key to specific IPs/APIs
- Don't share your bot token publicly

---

## Need Help?

- YouTube API: [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- Telegram Bot API: [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- Google Cloud Console: [Google Cloud Console](https://console.cloud.google.com/)

