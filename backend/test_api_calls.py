#!/usr/bin/env python3
"""
Test script to make Facebook Graph API calls and see what parameters are returned
"""
import requests
import json
from app.core.db import SessionLocal
from app.features.meta_campaigns import models

def get_credentials():
    """Get Meta credentials from database"""
    db = SessionLocal()
    try:
        account = db.query(models.BusinessAccount).filter(
            models.BusinessAccount.is_default == True
        ).first()

        if not account:
            # Try to get any account
            account = db.query(models.BusinessAccount).first()

        if not account:
            print("No business account found in database")
            return None, None

        print(f"Using business account: {account.name}")
        print(f"Account ID: {account.meta_account_id}")
        return account.meta_account_id, account.meta_access_token
    finally:
        db.close()

def test_ads_api(account_id, access_token):
    """Test fetching ads with all fields"""
    print("\n" + "="*80)
    print("TEST 1: Fetching Ads with all fields")
    print("="*80)

    # Ensure account_id has 'act_' prefix
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    fields = "id,name,account_id,adset_id,campaign_id,status,configured_status,effective_status,bid_amount,conversion_domain,created_time,last_updated_by_app_id,issues_info,preview_shareable_link,recommendations,tracking_specs,creative{id,name,object_story_spec,thumbnail_url,asset_feed_spec}"

    url = f"https://graph.facebook.com/v21.0/{account_id}/ads"
    params = {
        "fields": fields,
        "limit": 5,  # Just get 5 for testing
        "access_token": access_token
    }

    print(f"URL: {url}")
    print(f"Fields requested: {fields}")
    print("\nMaking request...")

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            ads = data.get("data", [])
            print(f"\n✅ Success! Got {len(ads)} ads")

            if ads:
                print("\n" + "-"*80)
                print("Sample Ad (first one):")
                print("-"*80)
                sample_ad = ads[0]
                print(f"Keys in response: {list(sample_ad.keys())}")
                print("\nFull response (formatted):")
                print(json.dumps(sample_ad, indent=2))

                # Check which fields we requested are actually present
                requested_fields = fields.split(",")
                print("\n" + "-"*80)
                print("Field Presence Check:")
                print("-"*80)
                for field in requested_fields:
                    field_clean = field.strip()
                    if "{" in field_clean:
                        # Nested field
                        base_field = field_clean.split("{")[0]
                        if base_field in sample_ad:
                            print(f"✅ {field_clean} - Present")
                        else:
                            print(f"❌ {field_clean} - Missing")
                    else:
                        if field_clean in sample_ad:
                            print(f"✅ {field_clean} - Present: {sample_ad[field_clean]}")
                        else:
                            print(f"❌ {field_clean} - Missing")
            else:
                print("⚠️  No ads returned")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")

def test_insights_api(account_id, access_token):
    """Test fetching insights"""
    print("\n" + "="*80)
    print("TEST 2: Fetching Insights")
    print("="*80)

    # First, get some ad IDs
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    # Get a few ads first
    ads_url = f"https://graph.facebook.com/v21.0/{account_id}/ads"
    ads_params = {
        "fields": "id",
        "limit": 3,
        "access_token": access_token
    }

    try:
        ads_response = requests.get(ads_url, params=ads_params, timeout=30)
        if ads_response.status_code != 200:
            print(f"❌ Could not fetch ads: {ads_response.text}")
            return

        ads_data = ads_response.json()
        ad_ids = [ad["id"] for ad in ads_data.get("data", [])]

        if not ad_ids:
            print("⚠️  No ads found to test insights")
            return

        print(f"Testing insights for {len(ad_ids)} ads: {ad_ids}")

        # Build time range (last 7 days) - using the same logic as the service
        from datetime import datetime, timedelta
        end_time = datetime.now()
        exclude_today = True
        if exclude_today:
            end_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end_time = end_time.replace(hour=23, minute=59, second=59)

        amount = 7
        # Facebook API includes both start and end dates, so subtract (amount - 1) to get exactly 'amount' days
        start_time = end_time - timedelta(days=amount - 1)

        time_range = {
            "since": start_time.strftime("%Y-%m-%d"),
            "until": end_time.strftime("%Y-%m-%d")
        }
        time_range_str = json.dumps(time_range)

        # Calculate actual days
        days_count = (end_time.date() - start_time.date()).days + 1
        print(f"Time range calculation: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')} = {days_count} days")

        # Fields to fetch
        fields = "campaign_id,adset_id,ad_id,spend,impressions,clicks,cpc,cpm,ctr,actions,cost_per_action_type"

        # Use the correct filter field (ad.id instead of ad_id)
        filter_field = "ad.id"
        filtering = json.dumps([{
            "field": filter_field,
            "operator": "IN",
            "value": ad_ids
        }])

        insights_url = f"https://graph.facebook.com/v21.0/{account_id}/insights"
        insights_params = {
            "level": "ad",
            "fields": fields,
            "time_range": time_range_str,
            "filtering": filtering,
            "access_token": access_token
        }

        print(f"\nURL: {insights_url}")
        print(f"Filter field: {filter_field}")
        print(f"Time range: {time_range_str}")
        print("\nMaking request...")

        response = requests.get(insights_url, params=insights_params, timeout=60)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            insights = data.get("data", [])
            print(f"\n✅ Success! Got {len(insights)} insights")

            if insights:
                print("\n" + "-"*80)
                print("Sample Insight (first one):")
                print("-"*80)
                sample_insight = insights[0]
                print(f"Keys in response: {list(sample_insight.keys())}")
                print("\nFull response (formatted):")
                print(json.dumps(sample_insight, indent=2))

                # Check metric values
                print("\n" + "-"*80)
                print("Metric Values:")
                print("-"*80)
                metrics = ["spend", "impressions", "clicks", "cpc", "cpm", "ctr"]
                for metric in metrics:
                    value = sample_insight.get(metric)
                    print(f"{metric}: {value} (type: {type(value).__name__})")

                if "actions" in sample_insight:
                    print(f"\nactions: {sample_insight['actions']}")

                if "cost_per_action_type" in sample_insight:
                    print(f"\ncost_per_action_type: {sample_insight['cost_per_action_type']}")
                    print(f"cost_per_action_type type: {type(sample_insight['cost_per_action_type'])}")
                    if isinstance(sample_insight['cost_per_action_type'], list):
                        for item in sample_insight['cost_per_action_type']:
                            print(f"  - {item}")
                else:
                    print("\n⚠️  cost_per_action_type field not found in response")
            else:
                print("⚠️  No insights returned (ads may have no performance data)")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Facebook Graph API Test Script")
    print("="*80)

    account_id, access_token = get_credentials()

    if not account_id or not access_token:
        print("❌ Could not get credentials from database")
        exit(1)

    # Test ads API
    test_ads_api(account_id, access_token)

    # Test insights API
    test_insights_api(account_id, access_token)

    print("\n" + "="*80)
    print("Tests Complete!")
    print("="*80)

