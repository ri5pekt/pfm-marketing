import logging
from typing import Dict, Tuple, Any
from app.features.meta_campaigns.facebook_api_client import _safe_float_any, _pick_canonical_purchase_action_value

logger = logging.getLogger(__name__)


def calculate_metric_from_insights(insights: Dict, field: str) -> float:
    """Calculate a metric value from insights data

    Args:
        insights: Insights data from Facebook API
        field: Field name to calculate
    """
    if not insights or len(insights) == 0:
        logger.debug(f"No insights data available for field '{field}'")
        return 0

    # Helper to safely convert to float, handling strings and None
    def safe_float(value, default=0):
        if value is None or value == "":
            return default
        try:
            return float(str(value).replace(",", ""))  # Remove commas from formatted numbers
        except (ValueError, TypeError):
            return default

    if field == "cpp":
        # Try to extract cost_per_purchase from cost_per_action_type array first
        cost_per_action_type = insights.get("cost_per_action_type", [])
        logger.debug(f"cost_per_action_type for cpp: {cost_per_action_type}, type: {type(cost_per_action_type)}")

        if cost_per_action_type:
            # Find the purchase action in the array
            # Facebook API can return various purchase action types: "purchase", "offsite_conversion.fb_pixel_purchase",
            # "onsite_web_purchase", "omni_purchase", "web_in_store_purchase", etc.
            purchase_action_types = ["purchase", "offsite_conversion.fb_pixel_purchase", "onsite_web_purchase",
                                   "omni_purchase", "web_in_store_purchase", "web_app_in_store_purchase"]
            for action_cost in cost_per_action_type:
                if isinstance(action_cost, dict):
                    action_type = action_cost.get("action_type", "")
                    logger.debug(f"Checking action_type: {action_type}, action_cost: {action_cost}")
                    # Check for any purchase action type
                    if action_type in purchase_action_types or "purchase" in action_type.lower():
                        cpp_value = action_cost.get("value")
                        logger.debug(f"Found purchase action ({action_type}), value: {cpp_value}")
                        if cpp_value:
                            # cost_per_action_type value might come as a string with currency or as a number
                            cpp_str = str(cpp_value).replace("$", "").replace(",", "")
                            result = safe_float(cpp_str, 0)
                            logger.debug(f"Calculated CPP from cost_per_action_type: {result}")
                            return result

        # Fallback: Try cost_per_result if available (for purchase-optimized campaigns)
        cost_per_result = insights.get("cost_per_result", [])
        if cost_per_result and isinstance(cost_per_result, list):
            for result_item in cost_per_result:
                if isinstance(result_item, dict):
                    indicator = result_item.get("indicator", "")
                    # Check if it's a purchase-related result
                    if "purchase" in indicator.lower():
                        values = result_item.get("values", [])
                        if values and isinstance(values, list) and len(values) > 0:
                            cpp_value = values[0].get("value")
                            if cpp_value:
                                cpp_str = str(cpp_value).replace("$", "").replace(",", "")
                                result = safe_float(cpp_str, 0)
                                logger.debug(f"Calculated CPP from cost_per_result: {result}")
                                return result

        # Fallback: Calculate from spend and purchase count if cost_per_action_type is not available
        logger.debug(f"cost_per_action_type not available, falling back to calculation from spend and actions")
        spend = safe_float(insights.get("spend"), 0)
        purchases = calculate_metric_from_insights(insights, "purchase_count")

        if purchases > 0:
            result = spend / purchases
            logger.debug(f"Calculated CPP from spend/purchases: spend={spend}, purchases={purchases}, cpp={result}")
            return result
        else:
            logger.debug(f"No purchases found. spend={spend}, actions={insights.get('actions')}")
            return 0
    elif field == "spend":
        return safe_float(insights.get("spend"), 0)
    elif field == "conversions":
        actions = insights.get("actions", [])
        conversions = 0
        if actions:
            for action in actions:
                if isinstance(action, dict) and action.get("action_type") in ["purchase", "complete_registration", "lead"]:
                    conversions += safe_float(action.get("value"), 0)
        return conversions
    elif field == "purchase_count":
        # Purchase count only (needed for Media Margin Volume / AOV calculations)
        actions = insights.get("actions", [])
        preferred = [
            "omni_purchase",
            "purchase",
            "offsite_conversion.fb_pixel_purchase",
            "onsite_web_purchase",
            "onsite_web_app_purchase",
            "web_in_store_purchase",
            "web_app_in_store_purchase",
        ]
        purchases, _chosen, _by_type = _pick_canonical_purchase_action_value(actions, preferred)
        return purchases
    elif field == "purchase_value":
        # Total purchase conversion value (revenue) for the time range.
        # Use action_values as the source (purchase conversion value isn't requestable as a field in v21.0).
        action_values = insights.get("action_values", [])
        preferred = [
            "omni_purchase",
            "purchase",
            "offsite_conversion.fb_pixel_purchase",
            "onsite_web_purchase",
            "onsite_web_app_purchase",
            "web_in_store_purchase",
            "web_app_in_store_purchase",
        ]
        value, _chosen, _by_type = _pick_canonical_purchase_action_value(action_values, preferred)
        return value
    elif field == "ctr":
        ctr_value = insights.get("ctr")
        if ctr_value:
            # CTR might come as percentage string like "1.23%" or as decimal
            ctr_str = str(ctr_value).replace("%", "")
            return safe_float(ctr_str, 0)
        return 0
    elif field == "cpc":
        return safe_float(insights.get("cpc"), 0)
    elif field == "cpm":
        return safe_float(insights.get("cpm"), 0)
    elif field == "roas":
        spend = safe_float(insights.get("spend"), 0)
        if spend == 0:
            return 0

        revenue = calculate_metric_from_insights(insights, "purchase_value")
        if revenue <= 0:
            return 0
        return revenue / spend
    elif field == "media_margin_volume":
        """
        Media Margin Volume (today):
          (Avg Order Value - Cost Per Purchase) × Purchases

        Using Meta-native definitions:
          AOV = purchase_value / purchase_count
          CPP = spend / purchase_count   (or cost_per_action_type purchase)

        This simplifies to:
          media_margin_volume = purchase_value - spend
        (when value & spend refer to the same time range and attribution settings)
        """
        purchase_value = calculate_metric_from_insights(insights, "purchase_value")
        spend = safe_float(insights.get("spend"), 0)
        return purchase_value - spend
    elif field == "daily_budget":
        # This comes from the object data, not insights
        return None
    return 0


def evaluate_condition(item: Dict, insights: Dict, condition: Dict, campaign_status_cache: Dict[str, str] = None) -> Tuple[bool, Dict]:
    """Evaluate a single condition against an item

    Args:
        item: The item (ad, adset, or campaign) to evaluate
        insights: Insights data for the item
        condition: The condition to evaluate
        campaign_status_cache: Optional dict mapping campaign_id to campaign status
    """
    field = condition.get("field")
    operator = condition.get("operator")
    expected_raw = condition.get("value")
    expected_value = expected_raw

    # Support structured expected values, e.g. { "base": "__daily_budget__", "mul": 1.2, "add": 0 }
    # This lets the UI express comparisons like DailyBudget * 1.2 without adding many special tokens.
    def _resolve_special_value_token(token: str) -> float:
        if token == "__daily_budget__":
            return float(item.get("daily_budget", 0)) / 100
        if token == "__lifetime_budget__":
            return float(item.get("lifetime_budget", 0)) / 100
        if token == "__current_spend__":
            return calculate_metric_from_insights(insights, "spend")
        logger.warning(f"Unknown special value: {token}")
        return 0

    if isinstance(expected_value, dict) and "base" in expected_value:
        base = expected_value.get("base")
        mul = expected_value.get("mul", 1)
        add = expected_value.get("add", 0)

        try:
            mul_f = float(mul) if mul is not None and mul != "" else 1.0
        except (ValueError, TypeError):
            mul_f = 1.0

        try:
            add_f = float(add) if add is not None and add != "" else 0.0
        except (ValueError, TypeError):
            add_f = 0.0

        base_val = 0.0
        if isinstance(base, str) and base.startswith("__") and base.endswith("__"):
            base_val = _resolve_special_value_token(base)
        else:
            try:
                base_val = float(base) if base is not None and base != "" else 0.0
            except (ValueError, TypeError):
                base_val = 0.0

        expected_value = (base_val * mul_f) + add_f

    # Handle special values (shortcodes like __daily_budget__)
    if isinstance(expected_value, str) and expected_value.startswith("__") and expected_value.endswith("__"):
        if expected_value == "__daily_budget__":
            # Get daily budget from item (in cents, convert to dollars)
            expected_value = float(item.get("daily_budget", 0)) / 100
            logger.debug(f"Special value __daily_budget__ resolved to: ${expected_value:.2f}")
        elif expected_value == "__lifetime_budget__":
            # Get lifetime budget from item (in cents, convert to dollars)
            expected_value = float(item.get("lifetime_budget", 0)) / 100
            logger.debug(f"Special value __lifetime_budget__ resolved to: ${expected_value:.2f}")
        elif expected_value == "__current_spend__":
            # Get current spend from insights
            expected_value = calculate_metric_from_insights(insights, "spend")
            logger.debug(f"Special value __current_spend__ resolved to: ${expected_value:.2f}")
        else:
            # Unknown special value, treat as 0
            logger.warning(f"Unknown special value: {expected_value}")
            expected_value = 0

    # Build a human-friendly expected expression (as configured)
    def _format_expected_expression(raw_val) -> str:
        try:
            if isinstance(raw_val, dict) and "base" in raw_val:
                base = raw_val.get("base")
                mul = raw_val.get("mul", 1)
                add = raw_val.get("add", 0)

                parts = [str(base)]
                if mul is not None and mul != "" and float(mul) != 1.0:
                    parts.append(f"× {mul}")
                if add is not None and add != "" and float(add) != 0.0:
                    sign = "+" if float(add) >= 0 else "-"
                    parts.append(f"{sign} {abs(float(add))}")
                return " ".join(parts)

            if isinstance(raw_val, str):
                return raw_val

            # numeric or other types
            return str(raw_val)
        except Exception:
            return str(raw_val)

    evaluation = {
        "field": field,
        "operator": operator,
        "expected_expression": _format_expected_expression(expected_raw),
        "expected_value": expected_value,
        "actual_value": None,
        "passed": False
    }

    # Include threshold for CPP Winning Days
    if field == "cpp_winning_days" and condition.get("threshold") is not None:
        evaluation["threshold"] = condition.get("threshold")

    # Handle status field (from object data)
    if field == "status":
        actual_value = item.get("status") or item.get("effective_status")
        evaluation["actual_value"] = actual_value
        if operator == "=":
            evaluation["passed"] = str(actual_value) == str(expected_value)
        elif operator == "!=":
            evaluation["passed"] = str(actual_value) != str(expected_value)

    # Handle campaign_status field (from campaign data)
    elif field == "campaign_status":
        campaign_id = item.get("campaign_id")
        if campaign_id and campaign_status_cache:
            actual_value = campaign_status_cache.get(str(campaign_id))
            evaluation["actual_value"] = actual_value
            if actual_value is not None:
                if operator == "=":
                    evaluation["passed"] = str(actual_value) == str(expected_value)
                elif operator == "!=":
                    evaluation["passed"] = str(actual_value) != str(expected_value)
            else:
                # Campaign status not found in cache, condition fails
                evaluation["passed"] = False
        else:
            # No campaign_id or no cache available, condition fails
            evaluation["actual_value"] = None
            evaluation["passed"] = False

    # Handle name_contains field (from object data)
    elif field == "name_contains":
        actual_value = item.get("name", "")
        evaluation["actual_value"] = actual_value
        if operator == "=":
            evaluation["passed"] = str(expected_value).lower() in actual_value.lower()
        elif operator == "!=":
            evaluation["passed"] = str(expected_value).lower() not in actual_value.lower()

    # Handle daily_budget (from object data)
    elif field == "daily_budget":
        actual_value = item.get("daily_budget")
        if actual_value is not None:
            actual_value = float(actual_value) / 100  # Convert cents to dollars
            evaluation["actual_value"] = actual_value  # Store converted value (in dollars) for display
            expected_value = float(expected_value)
            if operator == ">":
                evaluation["passed"] = actual_value > expected_value
            elif operator == ">=":
                evaluation["passed"] = actual_value >= expected_value
            elif operator == "<":
                evaluation["passed"] = actual_value < expected_value
            elif operator == "<=":
                evaluation["passed"] = actual_value <= expected_value
            elif operator == "=":
                evaluation["passed"] = actual_value == expected_value
            elif operator == "!=":
                evaluation["passed"] = actual_value != expected_value
        else:
            evaluation["actual_value"] = None

    # Handle cpp_winning_days (calculated from daily insights in service.py)
    elif field == "cpp_winning_days":
        # This is calculated in service.py and added to insights as "cpp_winning_days"
        actual_value = insights.get("cpp_winning_days", 0)
        if actual_value is None:
            actual_value = 0

        evaluation["actual_value"] = actual_value

    # Handle amount_of_active_ads (calculated in service.py)
    elif field == "amount_of_active_ads":
        # This is calculated in service.py and added to insights as "amount_of_active_ads"
        actual_value = insights.get("amount_of_active_ads", 0)
        if actual_value is None:
            actual_value = 0

        evaluation["actual_value"] = actual_value

        # Compare active ads count with expected value
        if actual_value is not None:
            expected_value = float(expected_value)
            if operator == ">":
                evaluation["passed"] = actual_value > expected_value
            elif operator == ">=":
                evaluation["passed"] = actual_value >= expected_value
            elif operator == "<":
                evaluation["passed"] = actual_value < expected_value
            elif operator == "<=":
                evaluation["passed"] = actual_value <= expected_value
            elif operator == "=":
                evaluation["passed"] = abs(actual_value - expected_value) < 0.01  # Float comparison
            elif operator == "!=":
                evaluation["passed"] = abs(actual_value - expected_value) >= 0.01
        else:
            evaluation["passed"] = False

        return evaluation["passed"], evaluation

        # Compare winning days count with expected value
        if actual_value is not None:
            expected_value = float(expected_value)
            if operator == ">":
                evaluation["passed"] = actual_value > expected_value
            elif operator == ">=":
                evaluation["passed"] = actual_value >= expected_value
            elif operator == "<":
                evaluation["passed"] = actual_value < expected_value
            elif operator == "<=":
                evaluation["passed"] = actual_value <= expected_value
            elif operator == "=":
                evaluation["passed"] = abs(actual_value - expected_value) < 0.01  # Float comparison
            elif operator == "!=":
                evaluation["passed"] = abs(actual_value - expected_value) >= 0.01
        else:
            evaluation["passed"] = False

        return evaluation["passed"], evaluation

    # Handle metrics from insights
    else:
        actual_value = calculate_metric_from_insights(insights, field)

        # Attach detailed calculation for debugging Media Margin Volume
        if field == "media_margin_volume":
            spend = _safe_float_any(insights.get("spend"), 0.0)

            # Canonical purchase types (avoid double counting)
            actions = insights.get("actions", [])
            action_values = insights.get("action_values", [])
            preferred = [
                "omni_purchase",
                "purchase",
                "offsite_conversion.fb_pixel_purchase",
                "onsite_web_purchase",
                "onsite_web_app_purchase",
                "web_in_store_purchase",
                "web_app_in_store_purchase",
            ]
            purchase_count, purchase_count_type, purchase_count_by_type = _pick_canonical_purchase_action_value(
                actions, preferred
            )
            purchase_value, purchase_value_type, purchase_value_by_type = _pick_canonical_purchase_action_value(
                action_values, preferred
            )

            purchase_value_source = "action_values" if purchase_value > 0 else "none"
            cpp = calculate_metric_from_insights(insights, "cpp")
            aov = (purchase_value / purchase_count) if purchase_count > 0 else None

            # Match the simplified backend definition: MMV = purchase_value - spend
            mmv = purchase_value - spend
            actual_value = mmv

            evaluation["calculation_details"] = {
                "metric": "media_margin_volume",
                "formula": "purchase_value - spend  (equivalent to (AOV - CPP) × Purchases when CPP=spend/purchases and AOV=value/purchases)",
                "purchase_value": purchase_value,
                "purchase_value_source": purchase_value_source,
                "spend": spend,
                "purchase_count": purchase_count,
                "purchase_count_action_type_used": purchase_count_type,
                "purchase_count_by_action_type": purchase_count_by_type,
                "purchase_value_action_type_used": purchase_value_type,
                "purchase_value_by_action_type": purchase_value_by_type,
                "aov": aov,
                "cpp": cpp,
                "result": mmv,
                "note": (
                    "If purchase_value is 0, verify Insights returns action_values for the selected time range/attribution."
                ),
            }

        evaluation["actual_value"] = actual_value

        # Log for debugging when actual_value is 0 or None
        if actual_value == 0 or actual_value is None:
            logger.debug(f"Field '{field}' evaluation - actual_value: {actual_value}, insights keys: {list(insights.keys()) if insights else 'empty'}")
            if insights:
                logger.debug(f"Insights data for field '{field}': spend={insights.get('spend')}, impressions={insights.get('impressions')}, clicks={insights.get('clicks')}, actions={insights.get('actions')}")

        if actual_value is not None:
            expected_value = float(expected_value)
            if operator == ">":
                evaluation["passed"] = actual_value > expected_value
            elif operator == ">=":
                evaluation["passed"] = actual_value >= expected_value
            elif operator == "<":
                evaluation["passed"] = actual_value < expected_value
            elif operator == "<=":
                evaluation["passed"] = actual_value <= expected_value
            elif operator == "=":
                evaluation["passed"] = abs(actual_value - expected_value) < 0.01  # Float comparison
            elif operator == "!=":
                evaluation["passed"] = abs(actual_value - expected_value) >= 0.01

    return evaluation["passed"], evaluation

