#!/usr/bin/env python3
"""
Credential Verification Script
Tests all credentials from the local .env file before starting the pipeline.

Expected variables in .env:
  - YOUTUBE_API_KEY
  - YOUTUBE_CHANNEL_ID (or YOUTUBE_PLAYLIST_ID)
  - YOUTUBE_PLAYLIST_ID (optional, alternative to channel)
  - TELEGRAM_BOT_TOKEN
  - TELEGRAM_CHAT_ID
"""
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


def load_env():
    """Load .env from the project root and show what we found (safely)."""
    # Try to load .env that lives next to this script (project root)
    env_path = Path(__file__).with_name(".env")
    loaded = load_dotenv(dotenv_path=env_path)

    print("=" * 60)
    print("Loading environment variables from .env")
    print("=" * 60)
    if not loaded:
        print("⚠️  .env file not found next to verify_credentials.py")
        print(f"   Expected at: {env_path}")
        print("   Create it from .env.example and fill in your values.")
    else:
        print(f"✅ Loaded .env from: {env_path}")

    # Show a safe summary of what we have (masking secrets)
    def mask(val: str | None, show: int = 4) -> str:
        if not val:
            return "(missing)"
        if len(val) <= show:
            return "*" * len(val)
        return val[:show] + "..." + "*" * 4

    print("\nCurrent .env values (masked):")
    print(f"  YOUTUBE_API_KEY      = {mask(os.getenv('YOUTUBE_API_KEY'))}")
    print(f"  YOUTUBE_CHANNEL_ID   = {os.getenv('YOUTUBE_CHANNEL_ID') or '(not set)'}")
    print(f"  YOUTUBE_PLAYLIST_ID  = {os.getenv('YOUTUBE_PLAYLIST_ID') or '(not set)'}")
    print(f"  TELEGRAM_BOT_TOKEN   = {mask(os.getenv('TELEGRAM_BOT_TOKEN'))}")
    print(f"  TELEGRAM_CHAT_ID     = {os.getenv('TELEGRAM_CHAT_ID') or '(not set)'}")
    print()

def test_youtube_api():
    """Test YouTube API Key"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    channel_id = os.getenv('YOUTUBE_CHANNEL_ID')
    playlist_id = os.getenv('YOUTUBE_PLAYLIST_ID')
    
    if not api_key:
        print("❌ YOUTUBE_API_KEY not found in .env file")
        return False
    
    print(f"🔍 Testing YouTube API Key: {api_key[:10]}...")
    
    # Test with channel ID
    if channel_id:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet&id={channel_id}&key={api_key}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    channel_name = data['items'][0]['snippet']['title']
                    print(f"✅ YouTube API Key is valid!")
                    print(f"   Channel: {channel_name} ({channel_id})")
                    return True
                else:
                    print(f"❌ Channel ID not found: {channel_id}")
                    return False
            else:
                print(f"❌ YouTube API Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ Error connecting to YouTube API: {e}")
            return False
    
    # Test with playlist ID
    elif playlist_id:
        url = f"https://www.googleapis.com/youtube/v3/playlists?part=snippet&id={playlist_id}&key={api_key}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    playlist_name = data['items'][0]['snippet']['title']
                    print(f"✅ YouTube API Key is valid!")
                    print(f"   Playlist: {playlist_name} ({playlist_id})")
                    return True
                else:
                    print(f"❌ Playlist ID not found: {playlist_id}")
                    return False
            else:
                print(f"❌ YouTube API Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ Error connecting to YouTube API: {e}")
            return False
    else:
        print("⚠️  Neither YOUTUBE_CHANNEL_ID nor YOUTUBE_PLAYLIST_ID found")
        print("   Testing API key only...")
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&key={api_key}&maxResults=1"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("✅ YouTube API Key is valid!")
                return True
            else:
                print(f"❌ YouTube API Error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error connecting to YouTube API: {e}")
            return False

def test_telegram_bot():
    """Test Telegram Bot Token"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        return False
    
    print(f"🔍 Testing Telegram Bot Token: {bot_token[:10]}...")
    
    # Test bot token
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Telegram Bot Token is valid!")
                print(f"   Bot: @{bot_info.get('username')} ({bot_info.get('first_name')})")
                
                # Test sending message if chat_id is provided
                if chat_id:
                    print(f"🔍 Testing Telegram Chat ID: {chat_id}...")
                    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    payload = {
                        'chat_id': chat_id,
                        'text': '✅ Credential verification successful! Your YouTube Analytics pipeline is ready.'
                    }
                    send_response = requests.post(send_url, json=payload)
                    if send_response.status_code == 200:
                        print(f"✅ Successfully sent test message to chat {chat_id}")
                        print("   Check your Telegram for the test message!")
                        return True
                    else:
                        print(f"❌ Failed to send message: {send_response.status_code}")
                        print(f"   Response: {send_response.text[:200]}")
                        print("   Make sure you've sent at least one message to your bot first!")
                        return False
                else:
                    print("⚠️  TELEGRAM_CHAT_ID not found - skipping message test")
                    return True
            else:
                print(f"❌ Invalid bot token")
                return False
        else:
            print(f"❌ Telegram API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to Telegram API: {e}")
        return False

def main():
    """Main verification function"""
    # Always load .env first so tests use the latest values
    load_env()

    print("=" * 60)
    print("YouTube Analytics Pipeline - Credential Verification")
    print("=" * 60)
    print()
    
    results = []
    
    # Test YouTube API
    print("\n📺 Testing YouTube API...")
    print("-" * 60)
    results.append(("YouTube API", test_youtube_api()))
    
    # Test Telegram Bot
    print("\n💬 Testing Telegram Bot...")
    print("-" * 60)
    results.append(("Telegram Bot", test_telegram_bot()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All credentials are valid! You're ready to start the pipeline.")
        print("   Run: docker-compose up -d")
        return 0
    else:
        print("\n⚠️  Some credentials failed verification.")
        print("   Please check SETUP_CREDENTIALS.md for help.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

