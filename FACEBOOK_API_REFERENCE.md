# Facebook/Meta Graph API Reference - Ads, Ad Sets, and Campaigns

This document provides a comprehensive reference for all available fields (parameters) and actions for Ads, Ad Sets, and Campaigns in the Facebook/Meta Graph API (v21.0+).

## Table of Contents

1. [Ads](#ads)
2. [Ad Sets](#ad-sets)
3. [Campaigns](#campaigns)

---

## Ads

### Available Fields (Read Parameters)

| Field Name               | Type    | Description                                                                    | Read-Only |
| ------------------------ | ------- | ------------------------------------------------------------------------------ | --------- |
| `id`                     | String  | Unique identifier for the ad                                                   | Yes       |
| `account_id`             | String  | ID of the ad account associated with the ad                                    | Yes       |
| `adset_id`               | String  | ID of the ad set that contains the ad                                          | Yes       |
| `campaign_id`            | String  | ID of the campaign that contains the ad                                        | Yes       |
| `name`                   | String  | Name of the ad                                                                 | No        |
| `status`                 | String  | Current status (ACTIVE, PAUSED, ARCHIVED, DELETED)                             | No        |
| `configured_status`      | String  | Status set by the user (ACTIVE, PAUSED, ARCHIVED, DELETED)                     | No        |
| `effective_status`       | String  | Effective status considering parent entities                                   | Yes       |
| `creative`               | Object  | Creative details (id, name, object_story_spec, thumbnail_url, asset_feed_spec) | No        |
| `bid_amount`             | Integer | Bid amount in cents                                                            | No        |
| `conversion_domain`      | String  | Conversion domain for the ad                                                   | No        |
| `created_time`           | String  | Time when the ad was created (ISO 8601)                                        | Yes       |
| `updated_time`           | String  | Time when the ad was last updated (ISO 8601)                                   | Yes       |
| `last_updated_by_app_id` | String  | ID of the app that last updated the ad                                         | Yes       |
| `issues_info`            | Array   | Information about issues with the ad                                           | Yes       |
| `preview_shareable_link` | String  | Shareable preview link for the ad                                              | Yes       |
| `recommendations`        | Array   | Recommendations for improving the ad's performance                             | Yes       |
| `tracking_specs`         | Array   | Tracking specifications for the ad                                             | No        |
| `adlabels`               | Array   | Labels associated with the ad                                                  | No        |
| `source_ad_id`           | String  | ID of the source ad if this is a copy                                          | Yes       |
| `source_ad`              | Object  | Source ad object if this is a copy                                             | Yes       |
| `ad_review_feedback`     | Object  | Review feedback for the ad                                                     | Yes       |
| `display_sequence`       | Integer | Display sequence for the ad                                                    | No        |
| `engagement_audience`    | Boolean | Whether engagement audience is enabled                                         | No        |
| `execution_options`      | Array   | Execution options for the ad                                                   | No        |
| `funding_source_id`      | String  | Funding source ID                                                              | Yes       |
| `object_story_id`        | String  | Object story ID                                                                | Yes       |
| `object_story_spec`      | Object  | Object story specification                                                     | No        |
| `recommendations`        | Array   | Recommendations for the ad                                                     | Yes       |
| `tracking_specs`         | Array   | Tracking specifications                                                        | No        |
| `adset`                  | Object  | Ad set object (when expanded)                                                  | Yes       |
| `campaign`               | Object  | Campaign object (when expanded)                                                | Yes       |

### Available Actions (API Operations)

| Action              | HTTP Method | Endpoint               | Description                             | Required Parameters                      |
| ------------------- | ----------- | ---------------------- | --------------------------------------- | ---------------------------------------- |
| **Create Ad**       | POST        | `/{ad_account_id}/ads` | Create a new ad within an ad set        | `name`, `adset_id`, `creative`, `status` |
| **Read Ad**         | GET         | `/{ad_id}`             | Retrieve details of a specific ad       | `access_token`                           |
| **Read Ads**        | GET         | `/{ad_account_id}/ads` | List all ads in an ad account           | `access_token`                           |
| **Update Ad**       | POST        | `/{ad_id}`             | Modify attributes of an existing ad     | `access_token`, fields to update         |
| **Delete Ad**       | DELETE      | `/{ad_id}`             | Remove an ad from the account           | `access_token`                           |
| **Get Ad Insights** | GET         | `/{ad_id}/insights`    | Retrieve performance metrics for the ad | `access_token`                           |

### Updateable Fields (via POST to /{ad_id})

-   `name` - Ad name
-   `status` - Ad status (ACTIVE, PAUSED, ARCHIVED, DELETED)
-   `creative` - Creative object
-   `bid_amount` - Bid amount in cents
-   `tracking_specs` - Tracking specifications
-   `adlabels` - Ad labels
-   `conversion_domain` - Conversion domain
-   `display_sequence` - Display sequence
-   `engagement_audience` - Engagement audience setting
    | `execution_options` - Execution options
-   `object_story_spec` - Object story specification

---

## Ad Sets

### Available Fields (Read Parameters)

| Field Name                         | Type    | Description                                                      | Read-Only |
| ---------------------------------- | ------- | ---------------------------------------------------------------- | --------- |
| `id`                               | String  | Unique identifier for the ad set                                 | Yes       |
| `account_id`                       | String  | ID of the ad account associated with the ad set                  | Yes       |
| `campaign_id`                      | String  | ID of the campaign that contains the ad set                      | Yes       |
| `name`                             | String  | Name of the ad set                                               | No        |
| `status`                           | String  | Current status (ACTIVE, PAUSED, ARCHIVED, DELETED)               | No        |
| `configured_status`                | String  | Status set by the user                                           | No        |
| `effective_status`                 | String  | Effective status considering parent entities                     | Yes       |
| `daily_budget`                     | Integer | Daily budget in cents                                            | No        |
| `lifetime_budget`                  | Integer | Lifetime budget in cents                                         | No        |
| `bid_strategy`                     | String  | Bidding strategy (LOWEST_COST_WITHOUT_CAP, COST_CAP, BID_CAP)    | No        |
| `bid_amount`                       | Integer | Bid amount in cents                                              | No        |
| `optimization_goal`                | String  | Optimization goal (APP_INSTALLS, CONVERSIONS, LINK_CLICKS, etc.) | No        |
| `billing_event`                    | String  | Billing event (IMPRESSIONS, LINK_CLICKS, etc.)                   | No        |
| `pacing_type`                      | Array   | Pacing type for ad delivery                                      | No        |
| `promoted_object`                  | Object  | Object being promoted by the ad set                              | No        |
| `targeting`                        | Object  | Targeting criteria (age, gender, location, interests, behaviors) | No        |
| `start_time`                       | String  | Start time for the ad set (ISO 8601)                             | No        |
| `end_time`                         | String  | End time for the ad set (ISO 8601)                               | No        |
| `created_time`                     | String  | Time when the ad set was created (ISO 8601)                      | Yes       |
| `updated_time`                     | String  | Time when the ad set was last updated (ISO 8601)                 | Yes       |
| `attribution_spec`                 | Array   | Attribution specification                                        | No        |
| `budget_remaining`                 | String  | Remaining budget                                                 | Yes       |
| `can_create_brand_lift_study`      | Boolean | Whether brand lift study can be created                          | Yes       |
| `can_use_spend_cap`                | Boolean | Whether spend cap can be used                                    | Yes       |
| `destination_type`                 | String  | Destination type                                                 | No        |
| `frequency_control_specs`          | Array   | Frequency control specifications                                 | No        |
| `lifetime_imps`                    | Integer | Lifetime impressions                                             | Yes       |
| `multi_optimization_goal_weight`   | String  | Multi-optimization goal weight                                   | No        |
| `promoted_object`                  | Object  | Promoted object                                                  | No        |
| `recommended_cpu_bid`              | Integer | Recommended CPU bid                                              | Yes       |
| `recurring_budget_semantics`       | Boolean | Recurring budget semantics                                       | No        |
| `review_feedback`                  | String  | Review feedback                                                  | Yes       |
| `source_adset`                     | Object  | Source ad set if copied                                          | Yes       |
| `source_adset_id`                  | String  | Source ad set ID if copied                                       | Yes       |
| `started_time`                     | String  | Actual start time                                                | Yes       |
| `targeting_optimization_types`     | String  | Targeting optimization types                                     | No        |
| `time_based_ad_rotation_id_blocks` | Array   | Time-based ad rotation ID blocks                                 | No        |
| `time_based_ad_rotation_intervals` | Array   | Time-based ad rotation intervals                                 | No        |
| `use_new_app_click`                | Boolean | Use new app click                                                | No        |
| `campaign`                         | Object  | Campaign object (when expanded)                                  | Yes       |
| `ads`                              | Array   | Ads in the ad set (when expanded)                                | Yes       |

### Available Actions (API Operations)

| Action                  | HTTP Method | Endpoint                  | Description                                 | Required Parameters                                                                                                     |
| ----------------------- | ----------- | ------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Create Ad Set**       | POST        | `/{ad_account_id}/adsets` | Create a new ad set within a campaign       | `name`, `campaign_id`, `daily_budget` or `lifetime_budget`, `billing_event`, `optimization_goal`, `targeting`, `status` |
| **Read Ad Set**         | GET         | `/{adset_id}`             | Retrieve details of a specific ad set       | `access_token`                                                                                                          |
| **Read Ad Sets**        | GET         | `/{ad_account_id}/adsets` | List all ad sets in an ad account           | `access_token`                                                                                                          |
| **Update Ad Set**       | POST        | `/{adset_id}`             | Modify attributes of an existing ad set     | `access_token`, fields to update                                                                                        |
| **Delete Ad Set**       | DELETE      | `/{adset_id}`             | Remove an ad set from the account           | `access_token`                                                                                                          |
| **Get Ad Set Insights** | GET         | `/{adset_id}/insights`    | Retrieve performance metrics for the ad set | `access_token`                                                                                                          |

### Updateable Fields (via POST to /{adset_id})

-   `name` - Ad set name
-   `status` - Ad set status (ACTIVE, PAUSED, ARCHIVED, DELETED)
-   `daily_budget` - Daily budget in cents
-   `lifetime_budget` - Lifetime budget in cents
-   `bid_strategy` - Bidding strategy
-   `bid_amount` - Bid amount in cents
-   `optimization_goal` - Optimization goal
-   `billing_event` - Billing event
-   `targeting` - Targeting criteria
-   `start_time` - Start time
-   `end_time` - End time
-   `pacing_type` - Pacing type
-   `promoted_object` - Promoted object
-   `attribution_spec` - Attribution specification
-   `destination_type` - Destination type
-   `frequency_control_specs` - Frequency control specifications
-   `multi_optimization_goal_weight` - Multi-optimization goal weight
-   `recurring_budget_semantics` - Recurring budget semantics
-   `targeting_optimization_types` - Targeting optimization types
-   `time_based_ad_rotation_id_blocks` - Time-based ad rotation ID blocks
-   `time_based_ad_rotation_intervals` - Time-based ad rotation intervals
-   `use_new_app_click` - Use new app click setting

---

## Campaigns

### Available Fields (Read Parameters)

| Field Name                    | Type    | Description                                                                        | Read-Only |
| ----------------------------- | ------- | ---------------------------------------------------------------------------------- | --------- |
| `id`                          | String  | Unique identifier for the campaign                                                 | Yes       |
| `account_id`                  | String  | ID of the ad account associated with the campaign                                  | Yes       |
| `name`                        | String  | Name of the campaign                                                               | No        |
| `status`                      | String  | Current status (ACTIVE, PAUSED, ARCHIVED, DELETED)                                 | No        |
| `objective`                   | String  | Campaign objective (BRAND_AWARENESS, CONVERSIONS, LINK_CLICKS, APP_INSTALLS, etc.) | No        |
| `buying_type`                 | String  | Buying type (AUCTION, RESERVED)                                                    | Yes       |
| `spend_cap`                   | Integer | Maximum spend cap in cents                                                         | No        |
| `created_time`                | String  | Time when the campaign was created (ISO 8601)                                      | Yes       |
| `updated_time`                | String  | Time when the campaign was last updated (ISO 8601)                                 | Yes       |
| `adlabels`                    | Array   | Labels associated with the campaign                                                | No        |
| `adset_bid_amount`            | Integer | Ad set bid amount                                                                  | Yes       |
| `adset_budget_type`           | String  | Ad set budget type                                                                 | Yes       |
| `bid_strategy`                | String  | Bid strategy                                                                       | No        |
| `boost_object_id`             | String  | Boost object ID                                                                    | No        |
| `brand_awareness_estimate`    | Integer | Brand awareness estimate                                                           | Yes       |
| `brand_lift_studies`          | Array   | Brand lift studies                                                                 | Yes       |
| `budget_rebalance_flag`       | Boolean | Budget rebalance flag                                                              | No        |
| `can_create_brand_lift_study` | Boolean | Whether brand lift study can be created                                            | Yes       |
| `can_use_spend_cap`           | Boolean | Whether spend cap can be used                                                      | Yes       |
| `configured_status`           | String  | Configured status                                                                  | No        |
| `effective_status`            | String  | Effective status                                                                   | Yes       |
| `issues_info`                 | Array   | Issues information                                                                 | Yes       |
| `last_budget_toggling_time`   | String  | Last budget toggling time                                                          | Yes       |
| `lifetime_budget`             | Integer | Lifetime budget in cents                                                           | No        |
| `recommended_cpu_bid`         | Integer | Recommended CPU bid                                                                | Yes       |
| `source_campaign`             | Object  | Source campaign if copied                                                          | Yes       |
| `source_campaign_id`          | String  | Source campaign ID if copied                                                       | Yes       |
| `special_ad_categories`       | Array   | Special ad categories                                                              | No        |
| `special_ad_category_country` | Array   | Special ad category countries                                                      | No        |
| `start_time`                  | String  | Start time                                                                         | No        |
| `stop_time`                   | String  | Stop time                                                                          | No        |
| `topline_id`                  | String  | Topline ID                                                                         | Yes       |
| `upstream_events`             | Object  | Upstream events                                                                    | Yes       |
| `adsets`                      | Array   | Ad sets in the campaign (when expanded)                                            | Yes       |
| `ads`                         | Array   | Ads in the campaign (when expanded)                                                | Yes       |

### Available Actions (API Operations)

| Action                    | HTTP Method | Endpoint                     | Description                                   | Required Parameters              |
| ------------------------- | ----------- | ---------------------------- | --------------------------------------------- | -------------------------------- |
| **Create Campaign**       | POST        | `/{ad_account_id}/campaigns` | Create a new campaign                         | `name`, `objective`, `status`    |
| **Read Campaign**         | GET         | `/{campaign_id}`             | Retrieve details of a specific campaign       | `access_token`                   |
| **Read Campaigns**        | GET         | `/{ad_account_id}/campaigns` | List all campaigns in an ad account           | `access_token`                   |
| **Update Campaign**       | POST        | `/{campaign_id}`             | Modify attributes of an existing campaign     | `access_token`, fields to update |
| **Delete Campaign**       | DELETE      | `/{campaign_id}`             | Remove a campaign from the account            | `access_token`                   |
| **Get Campaign Insights** | GET         | `/{campaign_id}/insights`    | Retrieve performance metrics for the campaign | `access_token`                   |

### Updateable Fields (via POST to /{campaign_id})

-   `name` - Campaign name
-   `status` - Campaign status (ACTIVE, PAUSED, ARCHIVED, DELETED)
-   `objective` - Campaign objective
-   `spend_cap` - Spend cap in cents
-   `adlabels` - Campaign labels
-   `bid_strategy` - Bid strategy
-   `boost_object_id` - Boost object ID
-   `budget_rebalance_flag` - Budget rebalance flag
-   `configured_status` - Configured status
-   `lifetime_budget` - Lifetime budget in cents
-   `special_ad_categories` - Special ad categories
-   `special_ad_category_country` - Special ad category countries
-   `start_time` - Start time
-   `stop_time` - Stop time

---

## Common Status Values

### Status Values (for Ads, Ad Sets, and Campaigns)

-   `ACTIVE` - Active and running
-   `PAUSED` - Paused by user
-   `ARCHIVED` - Archived
-   `DELETED` - Deleted
-   `DISAPPROVED` - Disapproved by Facebook
-   `PENDING_REVIEW` - Pending review
-   `PREAPPROVED` - Pre-approved
-   `PENDING_BILLING_INFO` - Pending billing information
-   `CAMPAIGN_PAUSED` - Paused due to parent campaign
-   `ADSET_PAUSED` - Paused due to parent ad set

### Effective Status Values

-   `ACTIVE` - Currently active
-   `PAUSED` - Currently paused
-   `DELETED` - Deleted
-   `ARCHIVED` - Archived
-   `DISAPPROVED` - Disapproved
-   `PENDING_REVIEW` - Pending review
-   `PREAPPROVED` - Pre-approved
-   `PENDING_BILLING_INFO` - Pending billing information
-   `CAMPAIGN_PAUSED` - Paused by parent campaign
-   `ADSET_PAUSED` - Paused by parent ad set
-   `WITH_ISSUES` - Has issues

---

## Notes

1. **API Version**: This reference is based on Facebook/Meta Graph API v21.0+. Some fields may vary by API version.

2. **Rate Limiting**: Facebook API has rate limits. It's recommended to add delays between API calls (1 second is safe) to avoid rate limiting errors.

3. **Required Fields**: When creating entities, certain fields are required:

    - **Ad**: `name`, `adset_id`, `creative`, `status`
    - **Ad Set**: `name`, `campaign_id`, `daily_budget` or `lifetime_budget`, `billing_event`, `optimization_goal`, `targeting`, `status`
    - **Campaign**: `name`, `objective`, `status`

4. **Read-Only Fields**: Fields marked as "Read-Only" cannot be updated via the API. They are set by Facebook or calculated automatically.

5. **Nested Objects**: Some fields like `creative`, `targeting`, `promoted_object` are complex objects with their own sub-fields. Refer to the official documentation for complete structure.

6. **Currency**: Budget and bid amounts are specified in cents (smallest currency unit).

7. **Time Formats**: All time fields use ISO 8601 format (e.g., "2024-01-15T10:30:00+0000").

---

## Official Documentation Links

-   [Meta Marketing API Overview](https://developers.facebook.com/docs/marketing-apis)
-   [Ad Object Reference](https://developers.facebook.com/docs/marketing-api/reference/adgroup)
-   [Ad Set Object Reference](https://developers.facebook.com/docs/marketing-api/reference/ad-campaign)
-   [Campaign Object Reference](https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group)
-   [Insights API Reference](https://developers.facebook.com/docs/marketing-api/insights)

---

_Last Updated: December 2024_
_API Version: v21.0+_
