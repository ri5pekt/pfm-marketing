#!/usr/bin/env python3
"""
Test script to debug Cost Per Purchase (CPP) for a specific ad set
"""
import requests
import json
from datetime import datetime, timedelta
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
            account = db.query(models.BusinessAccount).first()

        if not account:
            print("No business account found in database")
            return None, None

        print(f"Using business account: {account.name}")
        print(f"Account ID: {account.meta_account_id}")
        return account.meta_account_id, account.meta_access_token
    finally:
        db.close()

def test_cpp_for_adset(account_id, access_token, adset_id):
    """Test different ways to get Cost Per Purchase for a specific ad set"""

    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    # Build time range (last 7 days, excluding today)
    end_time = datetime.now()
    end_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    end_time = end_time.replace(hour=23, minute=59, second=59)
    start_time = end_time - timedelta(days=6)  # 7 days total

    time_range = {
        "since": start_time.strftime("%Y-%m-%d"),
        "until": end_time.strftime("%Y-%m-%d")
    }
    time_range_str = json.dumps(time_range)

    print(f"\n{'='*80}")
    print(f"Testing CPP for Ad Set ID: {adset_id}")
    print(f"Time Range: {time_range_str}")
    print(f"{'='*80}\n")

    base_url = "https://graph.facebook.com/v21.0"

    # Test 1: Get insights with cost_per_action_type and action_breakdowns
    print("TEST 1: cost_per_action_type with action_breakdowns=action_type")
    print("-" * 80)
    fields1 = "adset_id,spend,impressions,clicks,actions,cost_per_action_type"
    filtering1 = json.dumps([{
        "field": "adset.id",
        "operator": "IN",
        "value": [adset_id]
    }])

    url1 = f"{base_url}/{account_id}/insights"
    params1 = {
        "level": "adset",
        "fields": fields1,
        "time_range": time_range_str,
        "filtering": filtering1,
        "action_breakdowns": "action_type",
        "access_token": access_token
    }

    try:
        response1 = requests.get(url1, params=params1, timeout=60)
        print(f"Status Code: {response1.status_code}")
        if response1.status_code == 200:
            data1 = response1.json()
            insights1 = data1.get("data", [])
            if insights1:
                insight = insights1[0]
                print(f"✅ Got insight data")
                print(f"Keys: {list(insight.keys())}")
                print(f"\nSpend: {insight.get('spend')}")
                print(f"Impressions: {insight.get('impressions')}")
                print(f"Clicks: {insight.get('clicks')}")

                # Check actions
                actions = insight.get("actions", [])
                print(f"\nActions: {json.dumps(actions, indent=2)}")

                # Check cost_per_action_type
                cost_per_action_type = insight.get("cost_per_action_type", [])
                print(f"\ncost_per_action_type: {json.dumps(cost_per_action_type, indent=2)}")

                if cost_per_action_type:
                    for action_cost in cost_per_action_type:
                        if isinstance(action_cost, dict):
                            action_type = action_cost.get("action_type", "")
                            value = action_cost.get("value")
                            print(f"  Action Type: {action_type}, Value: {value}")
                            if "purchase" in action_type.lower():
                                print(f"  ✅ FOUND PURCHASE: {action_type} = {value}")
                else:
                    print("⚠️  cost_per_action_type is empty or not present")
            else:
                print("⚠️  No insights returned")
                print(f"Response: {response1.text}")
        else:
            print(f"❌ Error: {response1.status_code}")
            print(f"Response: {response1.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test 2: Try with cost_per_result
    print(f"\n\nTEST 2: cost_per_result")
    print("-" * 80)
    fields2 = "adset_id,spend,impressions,clicks,actions,cost_per_result"
    params2 = {
        "level": "adset",
        "fields": fields2,
        "time_range": time_range_str,
        "filtering": filtering1,
        "access_token": access_token
    }

    try:
        response2 = requests.get(url1, params=params2, timeout=60)
        print(f"Status Code: {response2.status_code}")
        if response2.status_code == 200:
            data2 = response2.json()
            insights2 = data2.get("data", [])
            if insights2:
                insight = insights2[0]
                cost_per_result = insight.get("cost_per_result")
                print(f"cost_per_result: {cost_per_result}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

    # Test 3: Try with action_breakdowns and check all action types
    print(f"\n\nTEST 3: All fields with action_breakdowns")
    print("-" * 80)
    fields3 = "adset_id,spend,impressions,clicks,actions,cost_per_action_type,cost_per_result"
    params3 = {
        "level": "adset",
        "fields": fields3,
        "time_range": time_range_str,
        "filtering": filtering1,
        "action_breakdowns": "action_type",
        "access_token": access_token
    }

    try:
        response3 = requests.get(url1, params=params3, timeout=60)
        print(f"Status Code: {response3.status_code}")
        if response3.status_code == 200:
            data3 = response3.json()
            insights3 = data3.get("data", [])
            if insights3:
                insight = insights3[0]
                print(f"\nFull insight response:")
                print(json.dumps(insight, indent=2))

                # Calculate manually
                spend = float(insight.get("spend", 0))
                actions = insight.get("actions", [])
                purchases = 0
                for action in actions:
                    if isinstance(action, dict):
                        action_type = action.get("action_type", "")
                        if "purchase" in action_type.lower():
                            purchases += float(action.get("value", 0))
                            print(f"\nFound purchase action: {action_type} = {action.get('value')}")

                if purchases > 0:
                    calculated_cpp = spend / purchases
                    print(f"\n📊 Calculated CPP: ${spend:.2f} / {purchases} purchases = ${calculated_cpp:.2f}")
                else:
                    print(f"\n⚠️  No purchases found in actions")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test 4: Try different action breakdowns
    print(f"\n\nTEST 4: action_breakdowns with action_type and action_reaction")
    print("-" * 80)
    params4 = {
        "level": "adset",
        "fields": fields3,
        "time_range": time_range_str,
        "filtering": filtering1,
        "action_breakdowns": ["action_type", "action_reaction"],
        "access_token": access_token
    }

    try:
        response4 = requests.get(url1, params=params4, timeout=60)
        print(f"Status Code: {response4.status_code}")
        if response4.status_code == 200:
            data4 = response4.json()
            insights4 = data4.get("data", [])
            if insights4:
                insight = insights4[0]
                print(f"\ncost_per_action_type with multiple breakdowns:")
                print(json.dumps(insight.get("cost_per_action_type", []), indent=2))
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    print("Facebook CPP Debug Test")
    print("="*80)

    account_id, access_token = get_credentials()

    if not account_id or not access_token:
        print("❌ Could not get credentials from database")
        exit(1)

    # Test with the specific ad set ID
    adset_id = "120236054661350637"
    test_cpp_for_adset(account_id, access_token, adset_id)

    print("\n" + "="*80)
    print("Test Complete!")
    print("="*80)

