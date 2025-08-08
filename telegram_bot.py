"""Telegram bot integration for sending car listing notifications."""

import json
import logging
import os
import requests
from typing import List, Optional
from config import TELEGRAM_CONFIG_FILE
from scraper import CarListing


class TelegramNotifier:
    """Handles sending notifications via Telegram bot."""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token (loaded from config if not provided)
            chat_id: Telegram chat ID to send messages to (loaded from config if not provided)
        """
        # Load configuration from file if not provided
        if bot_token is None or chat_id is None:
            config = self._load_config()
            self.bot_token = bot_token or config.get('bot_token', '')
            self.chat_id = chat_id or config.get('chat_id', '')
        else:
            self.bot_token = bot_token
            self.chat_id = chat_id
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.logger = logging.getLogger('telegram_notifier')
    
    def _load_config(self) -> dict:
        """Load Telegram configuration from file."""
        if os.path.exists(TELEGRAM_CONFIG_FILE):
            try:
                with open(TELEGRAM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load Telegram config: {e}")
        return {}
    
    def _send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send a text message to Telegram.
        
        Args:
            text: Message text
            parse_mode: Parse mode (HTML or Markdown)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                self.logger.info("Message sent successfully to Telegram")
                return True
            else:
                self.logger.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def _format_listing_message(self, listing: CarListing) -> str:
        """
        Format a car listing into a Telegram message.
        
        Args:
            listing: CarListing object
            
        Returns:
            Formatted message string
        """
        # Escape HTML special characters
        def escape_html(text: str) -> str:
            if not text:
                return ""
            return (text.replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;')
                       .replace('"', '&quot;')
                       .replace("'", '&#x27;'))
        
        title = escape_html(listing.title)
        price = escape_html(listing.price)
        year = escape_html(listing.year)
        km = escape_html(listing.km)
        location = escape_html(listing.location) if listing.location else ""
        
        # Build message with HTML formatting
        message_parts = [
            f"🚗 <b>New Car Listing Found!</b>",
            f"",
            f"<b>📋 {title}</b>",
            f"💰 Price: <b>{price}</b>"
        ]
        
        if year:
            message_parts.append(f"📅 Year: {year}")
        
        if km:
            message_parts.append(f"🛣 Kilometers: {km}")
        
        if location:
            message_parts.append(f"📍 Location: {location}")
        
        if listing.hand:
            message_parts.append(f"✋ Hand: {listing.hand}")
        
        if listing.engine_size:
            message_parts.append(f"⚙️ Engine: {listing.engine_size}")
        
        if listing.gear:
            message_parts.append(f"🔧 Gear: {listing.gear}")
        
        if listing.color:
            message_parts.append(f"🎨 Color: {listing.color}")
        
        # Add link
        if listing.url:
            message_parts.extend([
                f"",
                f"🔗 <a href=\"{listing.url}\">View Listing</a>"
            ])
        
        # Add description if available (truncated)
        if listing.description:
            desc = escape_html(listing.description)
            if len(desc) > 200:
                desc = desc[:200] + "..."
            message_parts.extend([
                f"",
                f"📝 Description: {desc}"
            ])
        
        return "\n".join(message_parts)
    
    def send_new_listing_notification(self, listing: CarListing) -> bool:
        """
        Send notification for a new car listing.
        
        Args:
            listing: CarListing object
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        message = self._format_listing_message(listing)
        return self._send_message(message)
    
    def send_multiple_listings_notification(self, listings: List[CarListing], filter_name: str) -> bool:
        """
        Send notification for multiple new listings.
        
        Args:
            listings: List of CarListing objects
            filter_name: Name of the search filter
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if not listings:
            return True
        
        if len(listings) == 1:
            return self.send_new_listing_notification(listings[0])
        
        # Multiple listings - send summary first
        summary_message = f"🚗 <b>{len(listings)} New Car Listings Found!</b>\n"
        summary_message += f"📋 Filter: <b>{filter_name}</b>\n\n"
        
        for i, listing in enumerate(listings[:5], 1):  # Show first 5
            title = listing.title[:50] + "..." if len(listing.title) > 50 else listing.title
            summary_message += f"{i}. {title}\n"
            summary_message += f"   💰 {listing.price}"
            if listing.year:
                summary_message += f" | 📅 {listing.year}"
            if listing.km:
                summary_message += f" | 🛣 {listing.km}"
            summary_message += "\n"
        
        if len(listings) > 5:
            summary_message += f"\n... and {len(listings) - 5} more listings"
        
        success = self._send_message(summary_message)
        
        # Send individual messages for first few listings
        for listing in listings[:3]:  # Send details for first 3
            if success:
                success = self.send_new_listing_notification(listing)
            else:
                break
        
        return success
    
    def send_error_notification(self, error_message: str) -> bool:
        """
        Send error notification.
        
        Args:
            error_message: Error message to send
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        message = f"❌ <b>Yad2 Scraper Error</b>\n\n{error_message}"
        return self._send_message(message)
    
    def send_status_notification(self, message: str) -> bool:
        """
        Send status notification.
        
        Args:
            message: Status message to send
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        status_message = f"ℹ️ <b>Yad2 Scraper Status</b>\n\n{message}"
        return self._send_message(status_message)
    
    def test_connection(self) -> bool:
        """
        Test the Telegram bot connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.api_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    self.logger.info(f"Successfully connected to Telegram bot: {bot_info['result']['username']}")
                    return True
            
            self.logger.error(f"Failed to connect to Telegram bot: {response.text}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error testing Telegram connection: {e}")
            return False


def setup_telegram_bot() -> TelegramNotifier:
    """
    Set up and test Telegram bot connection.
    
    Returns:
        TelegramNotifier instance
    """
    notifier = TelegramNotifier()
    
    if not notifier.bot_token or not notifier.chat_id or \
       notifier.bot_token == 'YOUR_BOT_TOKEN_HERE' or notifier.chat_id == 'YOUR_CHAT_ID_HERE':
        logging.warning("Telegram not configured. Please run 'python3 setup_telegram.py' to configure.")
        return notifier
    
    if notifier.test_connection():
        notifier.send_status_notification("🚀 Yad2 Car Scraper is now active!")
    else:
        logging.error("Failed to connect to Telegram bot. Please check your bot token and chat ID.")
    
    return notifier