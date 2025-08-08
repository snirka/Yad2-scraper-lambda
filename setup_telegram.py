"""Setup script to help configure Telegram bot."""

import os
import requests


def create_telegram_bot():
    """Guide user through creating a Telegram bot."""
    print("🤖 Telegram Bot Setup Guide")
    print("=" * 40)
    print()
    print("1. Open Telegram and search for @BotFather")
    print("2. Start a chat with BotFather and send: /newbot")
    print("3. Follow the instructions to create your bot")
    print("4. Copy the bot token when provided")
    print()
    
    bot_token = input("Enter your bot token: ").strip()
    
    if not bot_token:
        print("❌ Bot token is required!")
        return None, None
    
    # Test bot token
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        if response.status_code != 200:
            print("❌ Invalid bot token!")
            return None, None
        
        bot_info = response.json()
        if not bot_info.get('ok'):
            print("❌ Invalid bot token!")
            return None, None
        
        print(f"✅ Bot token valid! Bot name: {bot_info['result']['first_name']}")
        
    except Exception as e:
        print(f"❌ Error testing bot token: {e}")
        return None, None
    
    print()
    print("Now you need to get your chat ID:")
    print("1. Start a chat with your bot (search for its username)")
    print("2. Send any message to the bot")
    print("3. We'll try to get your chat ID automatically")
    print()
    
    input("Press Enter after you've sent a message to your bot...")
    
    # Try to get chat ID
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates", timeout=10)
        if response.status_code == 200:
            updates = response.json()
            if updates.get('ok') and updates.get('result'):
                for update in updates['result']:
                    if 'message' in update:
                        chat_id = str(update['message']['chat']['id'])
                        print(f"✅ Found chat ID: {chat_id}")
                        return bot_token, chat_id
        
        print("❌ Could not automatically get chat ID.")
        print("Please get your chat ID manually:")
        print(f"   Visit: https://api.telegram.org/bot{bot_token}/getUpdates")
        print("   Look for 'chat':{'id': YOUR_CHAT_ID}")
        print()
        
        chat_id = input("Enter your chat ID: ").strip()
        if not chat_id:
            print("❌ Chat ID is required!")
            return None, None
        
        return bot_token, chat_id
        
    except Exception as e:
        print(f"❌ Error getting chat ID: {e}")
        return None, None


def save_telegram_config(bot_token, chat_id):
    """Save Telegram configuration to environment file."""
    env_file = '.env'
    
    config_lines = [
        f"TELEGRAM_BOT_TOKEN={bot_token}",
        f"TELEGRAM_CHAT_ID={chat_id}"
    ]
    
    try:
        # Read existing .env file if it exists
        existing_lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                existing_lines = f.readlines()
        
        # Remove existing telegram config
        filtered_lines = [line for line in existing_lines 
                         if not line.startswith('TELEGRAM_BOT_TOKEN=') 
                         and not line.startswith('TELEGRAM_CHAT_ID=')]
        
        # Add new config
        all_lines = filtered_lines + [line + '\\n' for line in config_lines]
        
        with open(env_file, 'w') as f:
            f.writelines(all_lines)
        
        print(f"✅ Configuration saved to {env_file}")
        print()
        print("You can now run the scraper with:")
        print("  python main.py test-telegram  # Test the connection")
        print("  python main.py run           # Start the scraper")
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        print("Please manually add these to your environment:")
        print(f"  TELEGRAM_BOT_TOKEN={bot_token}")
        print(f"  TELEGRAM_CHAT_ID={chat_id}")


def main():
    """Main setup function."""
    print("🚗 Yad2 Car Scraper - Telegram Setup")
    print("=" * 50)
    print()
    
    bot_token, chat_id = create_telegram_bot()
    
    if bot_token and chat_id:
        save_telegram_config(bot_token, chat_id)
        
        # Test the configuration
        print("\\n🧪 Testing Telegram connection...")
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                data={
                    'chat_id': chat_id,
                    'text': '🎉 Yad2 Car Scraper setup complete! You will receive notifications here.',
                    'parse_mode': 'HTML'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Test message sent successfully!")
            else:
                print("❌ Failed to send test message")
                
        except Exception as e:
            print(f"❌ Error sending test message: {e}")
    else:
        print("❌ Setup failed. Please try again.")


if __name__ == "__main__":
    main()