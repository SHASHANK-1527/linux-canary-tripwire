"""
Webhook notification system for Canary.

Sends security events to configured webhook endpoints.
"""

from typing import Dict, Any, Optional
import requests
from datetime import datetime


class CanaryNotifier:
    """Handles webhook notifications for security events."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize the notifier.
        
        Args:
            webhook_url: Webhook endpoint URL
        """
        self.webhook_url = webhook_url
        self.timeout = 10
    
    def send_alert(self, event: Dict[str, Any]) -> bool:
        """
        Send an event to the webhook endpoint.
        
        Args:
            event: Event dictionary to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=event,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            return response.status_code in (200, 201, 202, 204)
        except requests.Timeout:
            print(f"Webhook timeout: {self.webhook_url}")
            return False
        except requests.ConnectionError:
            print(f"Webhook connection failed: {self.webhook_url}")
            return False
        except requests.RequestException as e:
            print(f"Webhook error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending webhook: {e}")
            return False
    
    def update_webhook_url(self, url: Optional[str]) -> None:
        """
        Update the webhook URL.
        
        Args:
            url: New webhook URL or None to disable
        """
        self.webhook_url = url
