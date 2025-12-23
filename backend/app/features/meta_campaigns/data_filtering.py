import requests
import logging
import time
import json
from typing import Dict, List, Any
from urllib.parse import quote, urlparse, parse_qs, urlencode, urlunparse
from app.features.meta_campaigns.rate_limit_tracker import check_rate_limit_headers
from app.features.meta_campaigns.facebook_api_client import READ_DELAY

logger = logging.getLogger(__name__)


def apply_scope_filters(data: List[Dict], scope_filters: Dict[str, Any], rule_level: str = "ad", account_id: str = None, access_token: str = None) -> List[Dict]:
    """Apply scope filters to the data

    Args:
        data: List of items to filter
        scope_filters: Dictionary of scope filters
        rule_level: The rule level (campaign, ad_set, or ad) to determine filter behavior
        account_id: Account ID for fetching campaign data (needed for campaign_name_contains)
        access_token: Access token for fetching campaign data (needed for campaign_name_contains)
    """
    filtered_data = data.copy()

    # Name contains filter (for ad/adset level - filters by item name)
    if "name_contains" in scope_filters and scope_filters["name_contains"]:
        keywords = scope_filters["name_contains"]
        if isinstance(keywords, list):
            filtered_data = [
                item for item in filtered_data
                if any(keyword.lower() in item.get("name", "").lower() for keyword in keywords)
            ]

    # IDs filter (for ad/adset level - filters by item id)
    if "ids" in scope_filters and scope_filters["ids"]:
        ids = scope_filters["ids"]
        if isinstance(ids, list):
            filtered_data = [
                item for item in filtered_data
                if str(item.get("id", "")) in [str(id_val) for id_val in ids]
            ]
        elif isinstance(ids, str):
            # Handle comma-separated or newline-separated IDs
            ids_list = [id_val.strip() for id_val in ids.replace("\n", ",").split(",") if id_val.strip()]
            filtered_data = [
                item for item in filtered_data
                if str(item.get("id", "")) in [str(id_val) for id_val in ids_list]
            ]

    # Campaign Name contains filter
    if "campaign_name_contains" in scope_filters and scope_filters["campaign_name_contains"]:
        keywords = scope_filters["campaign_name_contains"]
        if isinstance(keywords, list) and keywords:
            if rule_level == "campaign":
                # For campaign level, filter by campaign name directly
                logger.info(f"Applying campaign_name_contains filter at campaign level: {len(filtered_data)} items before filter")
                filtered_data = [
                    item for item in filtered_data
                    if any(keyword.lower() in item.get("name", "").lower() for keyword in keywords)
                ]
                logger.info(f"After campaign_name_contains filter: {len(filtered_data)} items remaining")
                if filtered_data:
                    sample_names = [item.get("name", "N/A") for item in filtered_data[:5]]
                    logger.info(f"Sample matching campaign names: {sample_names}")
            else:
                # For ad/adset level, fetch campaigns by name, then filter by campaign_id
                if account_id and access_token:
                    try:
                        filter_start_time = time.time()
                        logger.info(f"Fetching campaigns for campaign_name_contains filter (keywords: {keywords})...")
                        # Fetch campaigns and filter by name with pagination
                        base_url = "https://graph.facebook.com/v21.0"
                        if not account_id.startswith("act_"):
                            account_id_formatted = f"act_{account_id}"
                        else:
                            account_id_formatted = account_id

                        # OPTIMIZATION: If campaign_ids is set, only fetch those specific campaigns
                        campaign_ids_to_fetch = None
                        campaign_filtering = None
                        if "campaign_ids" in scope_filters and scope_filters["campaign_ids"]:
                            campaign_ids_to_fetch = scope_filters["campaign_ids"]
                            # Convert string to list if needed
                            if isinstance(campaign_ids_to_fetch, str):
                                campaign_ids_to_fetch = [id_val.strip() for id_val in campaign_ids_to_fetch.replace("\n", ",").split(",") if id_val.strip()]

                            if isinstance(campaign_ids_to_fetch, list) and campaign_ids_to_fetch:
                                campaign_filtering = json.dumps([{
                                    "field": "id",
                                    "operator": "IN",
                                    "value": campaign_ids_to_fetch
                                }])
                                logger.info(f"Optimization: Only fetching {len(campaign_ids_to_fetch)} campaigns (from campaign_ids) for campaign_name_contains check")

                        all_campaigns = []
                        url = f"{base_url}/{account_id_formatted}/campaigns"
                        params = {
                            "fields": "id,name",
                            "limit": 2000,  # Use 2000 to minimize API calls
                            "access_token": access_token
                        }

                        # Add filtering if campaign_ids is set
                        if campaign_filtering:
                            params["filtering"] = quote(campaign_filtering)

                        using_next_url = False
                        page_count = 0
                        while True:
                            page_count += 1
                            if using_next_url:
                                response = requests.get(url, timeout=30)
                            else:
                                response = requests.get(url, params=params, timeout=30)
                            response.raise_for_status()
                            check_rate_limit_headers(response, "read", account_id=account_id)

                            data = response.json()
                            page_campaigns = data.get("data", [])
                            all_campaigns.extend(page_campaigns)

                            paging = data.get("paging", {})
                            next_url = paging.get("next")

                            if not next_url:
                                break

                            # Preserve filtering parameter in next_url if campaign_ids filter was used
                            if campaign_filtering:
                                try:
                                    parsed = urlparse(next_url)
                                    query_params = parse_qs(parsed.query)
                                    # Check if filtering is already in the URL
                                    if 'filtering' not in query_params:
                                        # Add our filtering parameter to preserve it across pagination
                                        query_params['filtering'] = [quote(campaign_filtering)]
                                        # Reconstruct the URL with filtering
                                        new_query = urlencode(query_params, doseq=True)
                                        next_url = urlunparse((
                                            parsed.scheme,
                                            parsed.netloc,
                                            parsed.path,
                                            parsed.params,
                                            new_query,
                                            parsed.fragment
                                        ))
                                        logger.debug(f"Added filtering parameter to next_url for campaign_name_contains filter (page {page_count + 1})")
                                except Exception as e:
                                    logger.warning(f"Could not parse/modify next_url for campaign_name_contains filter: {e}. Using next_url as-is.")
                                    # If parsing fails, try to append filtering manually
                                    separator = '&' if '?' in next_url else '?'
                                    next_url = f"{next_url}{separator}filtering={quote(campaign_filtering)}"

                            url = next_url
                            using_next_url = True
                            time.sleep(READ_DELAY)

                        filter_elapsed = time.time() - filter_start_time
                        logger.info(f"[TIMING] Campaign fetch for campaign_name_contains filter took {filter_elapsed:.2f} seconds")
                        logger.info(f"Fetched all campaigns: {len(all_campaigns)} total across {page_count} page(s)")

                        # Filter campaigns by name keywords
                        matching_campaign_ids = [
                            str(campaign.get("id"))
                            for campaign in all_campaigns
                            if any(keyword.lower() in campaign.get("name", "").lower() for keyword in keywords)
                        ]
                        logger.info(f"Found {len(matching_campaign_ids)} campaigns matching campaign_name_contains (keywords: {keywords})")
                        if matching_campaign_ids:
                            logger.debug(f"Matching campaign IDs: {matching_campaign_ids[:10]}")  # Log first 10

                        # Filter ads/adsets by matching campaign IDs
                        logger.info(f"Filtering {rule_level} items by campaign_id: {len(filtered_data)} items before filter")
                        if matching_campaign_ids:
                            filtered_data = [
                                item for item in filtered_data
                                if str(item.get("campaign_id", "")) in matching_campaign_ids
                            ]
                            logger.info(f"After campaign_name_contains filter: {len(filtered_data)} items remaining")
                            if filtered_data:
                                sample_names = [item.get("name", "N/A") for item in filtered_data[:5]]
                                logger.info(f"Sample matching {rule_level} names: {sample_names}")
                        else:
                            # No campaigns match, so no ads/adsets match
                            logger.info("No campaigns match, so no ads/adsets match")
                            filtered_data = []
                    except Exception as e:
                        logger.warning(f"Error fetching campaigns for campaign_name_contains filter: {str(e)}")
                        # If we can't fetch campaigns, we can't filter, so keep all data

    # Campaign IDs filter
    if "campaign_ids" in scope_filters and scope_filters["campaign_ids"]:
        campaign_ids = scope_filters["campaign_ids"]
        # Convert string to list if needed
        if isinstance(campaign_ids, str):
            campaign_ids = [id_val.strip() for id_val in campaign_ids.replace("\n", ",").split(",") if id_val.strip()]

        if isinstance(campaign_ids, list) and campaign_ids:
            if rule_level == "campaign":
                # For campaign level, filter by campaign id (item id)
                filtered_data = [
                    item for item in filtered_data
                    if str(item.get("id", "")) in [str(id_val) for id_val in campaign_ids]
                ]
            else:
                # For ad/adset level, filter by campaign_id field
                filtered_data = [
                    item for item in filtered_data
                    if str(item.get("campaign_id", "")) in [str(id_val) for id_val in campaign_ids]
                ]

    return filtered_data

