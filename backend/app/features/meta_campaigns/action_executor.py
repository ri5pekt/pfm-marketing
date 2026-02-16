import requests
import logging
import time
from typing import Dict, List
from app.features.meta_campaigns.rate_limit_tracker import check_rate_limit_headers
from app.features.meta_campaigns.facebook_api_client import WRITE_DELAY

logger = logging.getLogger(__name__)


def send_slack_notification(webhook_url: str, rule_name: str, action_type: str, result: Dict) -> bool:
    """
    Send a Slack notification about an action execution result.

    Args:
        webhook_url: Slack webhook URL
        rule_name: Name of the rule that triggered the action
        action_type: Type of action (set_status, adjust_daily_budget)
        result: Action result dictionary with success, message, item_name, etc.

    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    if not webhook_url:
        return False

    try:
        # Determine color based on success
        color = "good" if result.get("success") else "danger"

        # Build message text
        status_emoji = "✅" if result.get("success") else "❌"
        item_name = result.get("item_name", "Unknown")
        message = result.get("message", "")

        # Format action type for display
        action_display = action_type.replace("_", " ").title()
        if action_type == "set_status":
            action_display = f"Set Status: {result.get('message', '')}"
        elif action_type == "adjust_daily_budget":
            old_budget = result.get("old_budget")
            new_budget = result.get("new_budget")
            if old_budget is not None and new_budget is not None:
                action_display = f"Budget Adjusted: ${old_budget:.2f} → ${new_budget:.2f}"
        elif action_type == "append_to_name":
            old_name = result.get("old_name", "")
            new_name = result.get("new_name", "")
            if old_name and new_name and old_name != new_name:
                action_display = f"Name Updated: {old_name} → {new_name}"
            else:
                action_display = f"Name Append: {result.get('message', '')}"
        elif action_type == "remove_from_name":
            old_name = result.get("old_name", "")
            new_name = result.get("new_name", "")
            if old_name and new_name and old_name != new_name:
                action_display = f"Name Updated: {old_name} → {new_name}"
            else:
                action_display = f"Name Remove: {result.get('message', '')}"
        elif action_type == "send_notification":
            action_display = "Notification: Rule conditions met"

        # Create Slack message payload
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"{status_emoji} Rule Action Executed: {rule_name}",
                    "fields": [
                        {
                            "title": "Item",
                            "value": item_name,
                            "short": True
                        },
                        {
                            "title": "Item ID",
                            "value": result.get("item_id", "N/A"),
                            "short": True
                        },
                        {
                            "title": "Action",
                            "value": action_display,
                            "short": False
                        },
                        {
                            "title": "Status",
                            "value": "Success" if result.get("success") else "Failed",
                            "short": True
                        }
                    ],
                    "footer": "PFM Marketing Automation",
                    "ts": int(time.time())
                }
            ]
        }

        # Add error field if action failed
        if not result.get("success") and result.get("error"):
            payload["attachments"][0]["fields"].append({
                "title": "Error",
                "value": result.get("error", "Unknown error")[:500],  # Limit error length
                "short": False
            })

        # Send to Slack
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Slack notification sent successfully for action on {item_name}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Slack notification: {str(e)}", exc_info=True)
        return False


def execute_action(account_id: str, access_token: str, rule_level: str, items: List[Dict], action: Dict, slack_webhook_url: str = None, rule_name: str = None, api_call_counter: Dict[str, int] = None) -> List[Dict]:
    """
    Execute an action on items via Meta API.
    Returns a list of action results with success/failure status.
    """
    action_type = action.get("type")
    results = []
    base_url = "https://graph.facebook.com/v21.0"

    for index, item in enumerate(items):
        item_id = item.get("id")
        item_name = item.get("name", "Unknown")
        result = {
            "item_id": item_id,
            "item_name": item_name,
            "action_type": action_type,
            "success": False,
            "message": "",
            "error": None
        }

        try:
            if action_type == "set_status":
                status = action.get("status", "PAUSED")
                url = f"{base_url}/{item_id}"
                params = {
                    "status": status,
                    "access_token": access_token
                }
                response = requests.post(url, params=params, timeout=30)
                
                # Track API call
                if api_call_counter is not None:
                    api_call_counter["total"] += 1
                    api_call_counter["actions"] += 1
                
                response.raise_for_status()
                check_rate_limit_headers(response, "write", account_id=account_id)
                result["success"] = True
                result["message"] = f"Status set to {status}"
                logger.info(f"Successfully set status to {status} for {rule_level} {item_id}")

            elif action_type == "adjust_daily_budget":
                # Get current budget first
                if rule_level == "ad_set":
                    # Fetch current adset to get daily_budget
                    url = f"{base_url}/{item_id}"
                    params = {"fields": "daily_budget", "access_token": access_token}
                    get_response = requests.get(url, params=params, timeout=30)
                    
                    # Track API call
                    if api_call_counter is not None:
                        api_call_counter["total"] += 1
                        api_call_counter["actions"] += 1
                    
                    get_response.raise_for_status()
                    check_rate_limit_headers(get_response, "read", account_id=account_id)
                    adset_data = get_response.json()
                    current_budget = float(adset_data.get("daily_budget", 0)) / 100  # Convert cents to dollars

                    # Calculate new budget
                    direction = action.get("direction", "increase")
                    percent = float(action.get("percent", 0))
                    min_cap = action.get("min_cap")
                    max_cap = action.get("max_cap")

                    if direction == "increase":
                        new_budget = current_budget * (1 + percent / 100)
                        # Check if increase would exceed max cap - if so, skip the action
                        if max_cap is not None and new_budget > float(max_cap):
                            result["success"] = False
                            result["message"] = f"Budget increase would exceed max cap (${max_cap:.2f}). Current: ${current_budget:.2f}, Would be: ${new_budget:.2f}. Action skipped."
                            result["old_budget"] = current_budget
                            result["new_budget"] = current_budget
                            logger.info(f"Skipping budget increase for adset {item_id}: would exceed max cap ${max_cap:.2f} (current: ${current_budget:.2f}, would be: ${new_budget:.2f})")
                        else:
                            # Update budget (in cents)
                            url = f"{base_url}/{item_id}"
                            params = {
                                "daily_budget": int(new_budget * 100),
                                "access_token": access_token
                            }
                            response = requests.post(url, params=params, timeout=30)
                            
                            # Track API call
                            if api_call_counter is not None:
                                api_call_counter["total"] += 1
                                api_call_counter["actions"] += 1
                            
                            response.raise_for_status()
                            check_rate_limit_headers(response, "write")
                            result["success"] = True
                            result["message"] = f"Budget adjusted from ${current_budget:.2f} to ${new_budget:.2f}"
                            result["old_budget"] = current_budget
                            result["new_budget"] = new_budget
                            logger.info(f"Successfully adjusted budget for adset {item_id}: ${current_budget:.2f} -> ${new_budget:.2f}")
                    else:  # decrease
                        new_budget = current_budget * (1 - percent / 100)
                        # Check if decrease would go below min cap - if so, skip the action
                        if min_cap is not None and new_budget < float(min_cap):
                            result["success"] = False
                            result["message"] = f"Budget decrease would go below min cap (${min_cap:.2f}). Current: ${current_budget:.2f}, Would be: ${new_budget:.2f}. Action skipped."
                            result["old_budget"] = current_budget
                            result["new_budget"] = current_budget
                            logger.info(f"Skipping budget decrease for adset {item_id}: would go below min cap ${min_cap:.2f} (current: ${current_budget:.2f}, would be: ${new_budget:.2f})")
                        else:
                            # Update budget (in cents)
                            url = f"{base_url}/{item_id}"
                            params = {
                                "daily_budget": int(new_budget * 100),
                                "access_token": access_token
                            }
                            response = requests.post(url, params=params, timeout=30)
                            
                            # Track API call
                            if api_call_counter is not None:
                                api_call_counter["total"] += 1
                                api_call_counter["actions"] += 1
                            
                            response.raise_for_status()
                            check_rate_limit_headers(response, "write")
                            result["success"] = True
                            result["message"] = f"Budget adjusted from ${current_budget:.2f} to ${new_budget:.2f}"
                            result["old_budget"] = current_budget
                            result["new_budget"] = new_budget
                            logger.info(f"Successfully adjusted budget for adset {item_id}: ${current_budget:.2f} -> ${new_budget:.2f}")
                else:
                    result["success"] = False
                    result["message"] = "Budget adjustment only available for ad sets"
                    result["error"] = "Invalid rule level for budget adjustment"
                    logger.warning(f"Budget adjustment attempted on {rule_level} {item_id}, but only ad sets support budget adjustment")

            elif action_type == "append_to_name":
                # Append text to the end of the item's name
                text_to_append = action.get("text", "")
                if not text_to_append:
                    result["success"] = False
                    result["message"] = "No text specified to append"
                    result["error"] = "Missing 'text' parameter"
                    logger.warning(f"Append to name action missing 'text' parameter for {rule_level} {item_id}")
                else:
                    # Check if text is already in the name to avoid duplicates
                    if text_to_append in item_name:
                        result["success"] = True
                        result["message"] = f"Text already present in name: {item_name}"
                        result["old_name"] = item_name
                        result["new_name"] = item_name
                        logger.info(f"Text '{text_to_append}' already present in {rule_level} {item_id} name, skipping")
                    else:
                        new_name = item_name + text_to_append
                        url = f"{base_url}/{item_id}"
                        params = {
                            "name": new_name,
                            "access_token": access_token
                        }
                        response = requests.post(url, params=params, timeout=30)
                        
                        # Track API call
                        if api_call_counter is not None:
                            api_call_counter["total"] += 1
                            api_call_counter["actions"] += 1
                        
                        response.raise_for_status()
                        check_rate_limit_headers(response, "write", account_id=account_id)
                        result["success"] = True
                        result["message"] = f"Appended '{text_to_append}' to name"
                        result["old_name"] = item_name
                        result["new_name"] = new_name
                        logger.info(f"Successfully appended '{text_to_append}' to {rule_level} {item_id} name: {item_name} -> {new_name}")

            elif action_type == "remove_from_name":
                # Remove text from the item's name
                text_to_remove = action.get("text", "")
                if not text_to_remove:
                    result["success"] = False
                    result["message"] = "No text specified to remove"
                    result["error"] = "Missing 'text' parameter"
                    logger.warning(f"Remove from name action missing 'text' parameter for {rule_level} {item_id}")
                else:
                    # Check if text is in the name
                    if text_to_remove not in item_name:
                        result["success"] = True
                        result["message"] = f"Text not found in name: {item_name}"
                        result["old_name"] = item_name
                        result["new_name"] = item_name
                        logger.info(f"Text '{text_to_remove}' not found in {rule_level} {item_id} name, skipping")
                    else:
                        new_name = item_name.replace(text_to_remove, "")
                        url = f"{base_url}/{item_id}"
                        params = {
                            "name": new_name,
                            "access_token": access_token
                        }
                        response = requests.post(url, params=params, timeout=30)
                        
                        # Track API call
                        if api_call_counter is not None:
                            api_call_counter["total"] += 1
                            api_call_counter["actions"] += 1
                        
                        response.raise_for_status()
                        check_rate_limit_headers(response, "write", account_id=account_id)
                        result["success"] = True
                        result["message"] = f"Removed '{text_to_remove}' from name"
                        result["old_name"] = item_name
                        result["new_name"] = new_name
                        logger.info(f"Successfully removed '{text_to_remove}' from {rule_level} {item_id} name: {item_name} -> {new_name}")

            elif action_type == "send_notification":
                # Send notification action - no API call, just notification
                result["success"] = True
                result["message"] = "Notification sent (no changes made)"
                logger.info(f"Send notification action for {rule_level} {item_id}: {item_name}")

            else:
                result["success"] = False
                result["message"] = f"Unknown action type: {action_type}"
                result["error"] = f"Unsupported action type: {action_type}"
                logger.warning(f"Unknown action type: {action_type}")

        except requests.exceptions.RequestException as e:
            result["success"] = False
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    error_msg = e.response.text or error_msg
            result["error"] = error_msg
            result["message"] = f"Failed to execute action: {error_msg}"
            logger.error(f"Error executing action {action_type} on {rule_level} {item_id}: {error_msg}")
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            result["message"] = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error executing action {action_type} on {rule_level} {item_id}: {str(e)}", exc_info=True)

        results.append(result)

        # Send Slack notification if enabled and webhook URL is provided
        send_notification = action.get("send_slack_notification", True)  # Default to True if not specified
        if send_notification and slack_webhook_url and rule_name:
            # For send_notification action, customize the message
            if action_type == "send_notification":
                # Create a custom result for notification-only actions
                notification_result = result.copy()
                notification_result["message"] = f"Rule conditions met for {item_name}"
                send_slack_notification(slack_webhook_url, rule_name, action_type, notification_result)
            else:
                send_slack_notification(slack_webhook_url, rule_name, action_type, result)

        # Add delay between items (except after the last item)
        if index < len(items) - 1:
            # Use smaller delay for notification-only actions, full delay for Meta API calls
            delay = 0.1 if action_type == "send_notification" else WRITE_DELAY
            time.sleep(delay)
            logger.debug(f"Waiting {delay}s before processing next item")

    return results

