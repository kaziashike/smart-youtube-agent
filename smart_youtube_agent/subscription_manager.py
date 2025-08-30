#!/usr/bin/env python3
"""
Subscription and Billing Management System
Handles subscription tiers, billing, and usage tracking for the SaaS platform
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from pydantic import BaseModel
import secrets

# Configure logging
logger = logging.getLogger(__name__)

class SubscriptionTier(BaseModel):
    name: str
    price_monthly: float
    price_yearly: float
    video_limit: int
    features: List[str]
    max_team_members: int
    priority_support: bool
    custom_branding: bool
    api_access: bool

class Subscription(BaseModel):
    user_id: str
    tier: str
    status: str  # active, cancelled, expired, trial
    start_date: str
    end_date: str
    billing_cycle: str  # monthly, yearly
    payment_method: Optional[str] = None
    auto_renew: bool = True
    trial_ends: Optional[str] = None

class BillingHistory(BaseModel):
    user_id: str
    invoice_id: str
    amount: float
    currency: str = "USD"
    status: str  # paid, pending, failed
    date: str
    description: str
    payment_method: Optional[str] = None

class UsageMetrics(BaseModel):
    user_id: str
    month: str  # YYYY-MM format
    videos_created: int
    videos_uploaded: int
    api_calls: int
    storage_used: int  # MB
    team_members: int

class SubscriptionManager:
    def __init__(self):
        self.subscriptions_file = os.path.join(os.path.dirname(__file__), "subscriptions.json")
        self.billing_file = os.path.join(os.path.dirname(__file__), "billing.json")
        self.usage_file = os.path.join(os.path.dirname(__file__), "usage.json")
        self.ensure_files()
        
        # Define subscription tiers
        self.tiers = {
            "Free": SubscriptionTier(
                name="Free",
                price_monthly=0.0,
                price_yearly=0.0,
                video_limit=3,
                features=["Basic video creation", "YouTube upload", "Email support"],
                max_team_members=1,
                priority_support=False,
                custom_branding=False,
                api_access=False
            ),
            "Starter": SubscriptionTier(
                name="Starter",
                price_monthly=29.0,
                price_yearly=290.0,
                video_limit=20,
                features=["Advanced video creation", "YouTube upload", "Priority support", "Custom thumbnails"],
                max_team_members=3,
                priority_support=True,
                custom_branding=False,
                api_access=False
            ),
            "Professional": SubscriptionTier(
                name="Professional",
                price_monthly=79.0,
                price_yearly=790.0,
                video_limit=100,
                features=["Unlimited video creation", "YouTube upload", "Priority support", "Custom branding", "API access"],
                max_team_members=10,
                priority_support=True,
                custom_branding=True,
                api_access=True
            ),
            "Enterprise": SubscriptionTier(
                name="Enterprise",
                price_monthly=199.0,
                price_yearly=1990.0,
                video_limit=-1,  # Unlimited
                features=["Everything in Professional", "Dedicated support", "Custom integrations", "White-label solution"],
                max_team_members=-1,  # Unlimited
                priority_support=True,
                custom_branding=True,
                api_access=True
            )
        }
    
    def ensure_files(self):
        """Ensure necessary files exist."""
        for file_path in [self.subscriptions_file, self.billing_file, self.usage_file]:
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f)
    
    def load_subscriptions(self) -> Dict[str, Any]:
        """Load subscriptions from JSON file."""
        try:
            with open(self.subscriptions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading subscriptions: {e}")
            return {}
    
    def save_subscriptions(self, subscriptions: Dict[str, Any]) -> None:
        """Save subscriptions to JSON file."""
        try:
            with open(self.subscriptions_file, "w", encoding="utf-8") as f:
                json.dump(subscriptions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving subscriptions: {e}")
            raise HTTPException(status_code=500, detail="Failed to save subscription data")
    
    def load_billing(self) -> Dict[str, Any]:
        """Load billing history from JSON file."""
        try:
            with open(self.billing_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading billing: {e}")
            return {}
    
    def save_billing(self, billing: Dict[str, Any]) -> None:
        """Save billing history to JSON file."""
        try:
            with open(self.billing_file, "w", encoding="utf-8") as f:
                json.dump(billing, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving billing: {e}")
            raise HTTPException(status_code=500, detail="Failed to save billing data")
    
    def load_usage(self) -> Dict[str, Any]:
        """Load usage metrics from JSON file."""
        try:
            with open(self.usage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading usage: {e}")
            return {}
    
    def save_usage(self, usage: Dict[str, Any]) -> None:
        """Save usage metrics to JSON file."""
        try:
            with open(self.usage_file, "w", encoding="utf-8") as f:
                json.dump(usage, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving usage: {e}")
            raise HTTPException(status_code=500, detail="Failed to save usage data")
    
    def create_free_subscription(self, user_id: str) -> Subscription:
        """Create a free subscription for new users."""
        now = datetime.utcnow()
        trial_end = now + timedelta(days=14)  # 14-day trial
        
        subscription = Subscription(
            user_id=user_id,
            tier="Free",
            status="trial",
            start_date=now.isoformat(),
            end_date=trial_end.isoformat(),
            billing_cycle="monthly",
            auto_renew=True,
            trial_ends=trial_end.isoformat()
        )
        
        subscriptions = self.load_subscriptions()
        subscriptions[user_id] = subscription.dict()
        self.save_subscriptions(subscriptions)
        
        logger.info(f"Created free subscription for user: {user_id}")
        return subscription
    
    def upgrade_subscription(self, user_id: str, tier: str, billing_cycle: str = "monthly") -> Subscription:
        """Upgrade user subscription."""
        if tier not in self.tiers:
            raise HTTPException(status_code=400, detail="Invalid subscription tier")
        
        subscriptions = self.load_subscriptions()
        now = datetime.utcnow()
        
        if billing_cycle == "yearly":
            end_date = now + timedelta(days=365)
        else:
            end_date = now + timedelta(days=30)
        
        subscription = Subscription(
            user_id=user_id,
            tier=tier,
            status="active",
            start_date=now.isoformat(),
            end_date=end_date.isoformat(),
            billing_cycle=billing_cycle,
            auto_renew=True
        )
        
        subscriptions[user_id] = subscription.dict()
        self.save_subscriptions(subscriptions)
        
        # Create billing record
        self.create_billing_record(user_id, tier, billing_cycle)
        
        logger.info(f"Upgraded subscription for user {user_id} to {tier}")
        return subscription
    
    def cancel_subscription(self, user_id: str) -> Subscription:
        """Cancel user subscription."""
        subscriptions = self.load_subscriptions()
        if user_id not in subscriptions:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        subscription_data = subscriptions[user_id]
        subscription_data["status"] = "cancelled"
        subscription_data["auto_renew"] = False
        
        subscriptions[user_id] = subscription_data
        self.save_subscriptions(subscriptions)
        
        logger.info(f"Cancelled subscription for user: {user_id}")
        return Subscription(**subscription_data)
    
    def get_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user subscription."""
        subscriptions = self.load_subscriptions()
        if user_id in subscriptions:
            return Subscription(**subscriptions[user_id])
        return None
    
    def get_tier_info(self, tier_name: str) -> Optional[SubscriptionTier]:
        """Get subscription tier information."""
        return self.tiers.get(tier_name)
    
    def get_all_tiers(self) -> Dict[str, SubscriptionTier]:
        """Get all available subscription tiers."""
        return self.tiers
    
    def check_video_limit(self, user_id: str) -> bool:
        """Check if user can create more videos."""
        subscription = self.get_subscription(user_id)
        if not subscription:
            return False
        
        tier_info = self.get_tier_info(subscription.tier)
        if not tier_info:
            return False
        
        # Unlimited videos
        if tier_info.video_limit == -1:
            return True
        
        # Check current usage
        current_month = datetime.utcnow().strftime("%Y-%m")
        usage = self.get_usage_metrics(user_id, current_month)
        videos_created = usage.videos_created if usage else 0
        
        return videos_created < tier_info.video_limit
    
    def create_billing_record(self, user_id: str, tier: str, billing_cycle: str) -> BillingHistory:
        """Create a billing record."""
        tier_info = self.get_tier_info(tier)
        if not tier_info:
            raise HTTPException(status_code=400, detail="Invalid tier")
        
        amount = tier_info.price_yearly if billing_cycle == "yearly" else tier_info.price_monthly
        invoice_id = f"inv_{secrets.token_hex(8)}"
        
        billing_record = BillingHistory(
            user_id=user_id,
            invoice_id=invoice_id,
            amount=amount,
            status="paid",
            date=datetime.utcnow().isoformat(),
            description=f"{tier} subscription - {billing_cycle} billing"
        )
        
        billing = self.load_billing()
        if user_id not in billing:
            billing[user_id] = []
        billing[user_id].append(billing_record.dict())
        self.save_billing(billing)
        
        return billing_record
    
    def get_billing_history(self, user_id: str) -> List[BillingHistory]:
        """Get user billing history."""
        billing = self.load_billing()
        if user_id in billing:
            return [BillingHistory(**record) for record in billing[user_id]]
        return []
    
    def update_usage_metrics(self, user_id: str, metric_type: str, value: int = 1) -> None:
        """Update usage metrics for a user."""
        current_month = datetime.utcnow().strftime("%Y-%m")
        usage = self.load_usage()
        
        if user_id not in usage:
            usage[user_id] = {}
        
        if current_month not in usage[user_id]:
            usage[user_id][current_month] = {
                "user_id": user_id,
                "month": current_month,
                "videos_created": 0,
                "videos_uploaded": 0,
                "api_calls": 0,
                "storage_used": 0,
                "team_members": 0
            }
        
        if metric_type in usage[user_id][current_month]:
            usage[user_id][current_month][metric_type] += value
        
        self.save_usage(usage)
    
    def get_usage_metrics(self, user_id: str, month: str = None) -> Optional[UsageMetrics]:
        """Get usage metrics for a user."""
        if month is None:
            month = datetime.utcnow().strftime("%Y-%m")
        
        usage = self.load_usage()
        if user_id in usage and month in usage[user_id]:
            return UsageMetrics(**usage[user_id][month])
        return None
    
    def get_all_usage_metrics(self, user_id: str) -> List[UsageMetrics]:
        """Get all usage metrics for a user."""
        usage = self.load_usage()
        if user_id in usage:
            return [UsageMetrics(**metrics) for metrics in usage[user_id].values()]
        return []
    
    def check_subscription_status(self, user_id: str) -> str:
        """Check and update subscription status."""
        subscription = self.get_subscription(user_id)
        if not subscription:
            return "no_subscription"
        
        now = datetime.utcnow()
        end_date = datetime.fromisoformat(subscription.end_date)
        
        if subscription.status == "trial" and subscription.trial_ends:
            trial_end = datetime.fromisoformat(subscription.trial_ends)
            if now > trial_end:
                # Trial expired, downgrade to free
                subscription.status = "expired"
                subscription.tier = "Free"
                subscription.end_date = (now + timedelta(days=30)).isoformat()
                
                subscriptions = self.load_subscriptions()
                subscriptions[user_id] = subscription.dict()
                self.save_subscriptions(subscriptions)
        
        elif subscription.status == "active" and now > end_date:
            if subscription.auto_renew:
                # Auto-renew subscription
                if subscription.billing_cycle == "yearly":
                    new_end_date = end_date + timedelta(days=365)
                else:
                    new_end_date = end_date + timedelta(days=30)
                
                subscription.end_date = new_end_date.isoformat()
                subscriptions = self.load_subscriptions()
                subscriptions[user_id] = subscription.dict()
                self.save_subscriptions(subscriptions)
                
                # Create new billing record
                self.create_billing_record(user_id, subscription.tier, subscription.billing_cycle)
            else:
                # Subscription expired
                subscription.status = "expired"
                subscriptions = self.load_subscriptions()
                subscriptions[user_id] = subscription.dict()
                self.save_subscriptions(subscriptions)
        
        return subscription.status
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get overall subscription statistics."""
        subscriptions = self.load_subscriptions()
        
        total_users = len(subscriptions)
        active_subscriptions = 0
        trial_subscriptions = 0
        cancelled_subscriptions = 0
        tier_counts = {}
        monthly_revenue = 0
        yearly_revenue = 0
        
        for user_id, sub_data in subscriptions.items():
            subscription = Subscription(**sub_data)
            tier_info = self.get_tier_info(subscription.tier)
            
            if subscription.status == "active":
                active_subscriptions += 1
                if subscription.billing_cycle == "monthly":
                    monthly_revenue += tier_info.price_monthly
                else:
                    yearly_revenue += tier_info.price_yearly / 12  # Monthly equivalent
            elif subscription.status == "trial":
                trial_subscriptions += 1
            elif subscription.status == "cancelled":
                cancelled_subscriptions += 1
            
            tier_counts[subscription.tier] = tier_counts.get(subscription.tier, 0) + 1
        
        return {
            "total_users": total_users,
            "active_subscriptions": active_subscriptions,
            "trial_subscriptions": trial_subscriptions,
            "cancelled_subscriptions": cancelled_subscriptions,
            "tier_distribution": tier_counts,
            "monthly_revenue": monthly_revenue,
            "yearly_revenue": yearly_revenue,
            "total_monthly_revenue": monthly_revenue + yearly_revenue
        }

# Global instance
subscription_manager = SubscriptionManager() 