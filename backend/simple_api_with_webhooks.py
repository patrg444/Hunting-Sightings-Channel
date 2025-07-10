from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os
import stripe
import json
from dotenv import load_dotenv
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@app.get("/")
def read_root():
    return {"message": "Wildlife Sightings API", "version": "1.1.0"}

@app.get("/api/v1/sightings")
def get_sightings(
    limit: int = 20, 
    offset: int = 0,
    page: int = 1,
    page_size: int = 20,
    start_date: str = None,
    end_date: str = None,
    species: str = None,
    gmu: int = None
):
    try:
        # Use page_size as limit if provided
        if page_size != 20:  # Non-default page_size
            limit = page_size
        
        # Calculate offset from page
        if page > 1:
            offset = (page - 1) * limit
            
        # Build query
        query = supabase.table('sightings').select("*", count='exact')
        
        # Apply filters
        if start_date:
            query = query.gte('sighting_date', start_date)
        if end_date:
            query = query.lte('sighting_date', end_date)
        if species:
            query = query.ilike('species', f'%{species}%')
        if gmu:
            query = query.eq('gmu_unit', gmu)
            
        # Execute with pagination
        response = query.order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Transform to expected format
        return {
            "sightings": response.data,
            "total": response.count if hasattr(response, 'count') else len(response.data),
            "page": page,
            "pageSize": page_size,
            "totalPages": (response.count // page_size) + 1 if hasattr(response, 'count') else 1
        }
    except Exception as e:
        return {"error": str(e), "sightings": [], "total": 0}

@app.get("/api/v1/sightings/count")
def get_count():
    try:
        response = supabase.table('sightings').select("*", count='exact').execute()
        return {"count": response.count}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/sightings/stats")
def get_stats(days: int = 30):
    try:
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get sightings in date range
        response = supabase.table('sightings') \
            .select("*") \
            .gte('created_at', start_date.isoformat()) \
            .execute()
        
        # Calculate stats
        species_counts = {}
        source_counts = {}
        
        for sighting in response.data:
            # Count species
            species = sighting.get('species', 'unknown')
            species_counts[species] = species_counts.get(species, 0) + 1
            
            # Count sources
            source = sighting.get('source_type', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            "total_sightings": len(response.data),
            "species_counts": species_counts,
            "source_counts": source_counts,
            "days": days
        }
    except Exception as e:
        return {"error": str(e), "total_sightings": 0, "species_counts": {}, "source_counts": {}}

@app.post("/api/v1/subscriptions/checkout-session")
async def create_checkout_session(request: Request):
    """Create a Stripe checkout session for subscription"""
    try:
        data = await request.json()
        price_id = data.get('price_id')
        success_url = data.get('success_url')
        cancel_url = data.get('cancel_url')
        
        # Get auth header to identify user
        auth_header = request.headers.get('authorization')
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization required")
        
        # Extract token (Bearer token)
        token = auth_header.replace('Bearer ', '')
        
        # Get user from Supabase auth
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        user_email = user.user.email
        user_id = user.user.id
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(user_id),
            customer_email=user_email,
            metadata={
                'user_id': str(user_id)
            },
            subscription_data={
                'trial_period_days': 7,  # 7-day free trial
                'metadata': {
                    'user_id': str(user_id),
                }
            }
        )
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@app.get("/api/v1/subscriptions/current")
async def get_subscription_status(request: Request):
    """Get current user's subscription status"""
    try:
        # Get auth header
        auth_header = request.headers.get('authorization')
        if not auth_header:
            return {"status": "no_subscription", "trialDaysRemaining": 7}
        
        # Extract token
        token = auth_header.replace('Bearer ', '')
        
        # Get user from Supabase auth
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            return {"status": "no_subscription", "trialDaysRemaining": 7}
        
        user_email = user.user.email
        
        # Search for customer by email
        customers = stripe.Customer.list(email=user_email, limit=1)
        
        if not customers.data:
            return {"status": "no_subscription", "trialDaysRemaining": 7}
        
        customer = customers.data[0]
        
        # Get active subscriptions
        subscriptions = stripe.Subscription.list(
            customer=customer.id,
            status="all",
            limit=1
        )
        
        if not subscriptions.data:
            return {"status": "no_subscription", "trialDaysRemaining": 7}
        
        subscription = subscriptions.data[0]
        
        # Calculate trial days remaining if in trial
        trial_days_remaining = 0
        if subscription.status == "trialing" and subscription.trial_end:
            trial_end = datetime.fromtimestamp(subscription.trial_end)
            now = datetime.now()
            trial_days_remaining = max(0, (trial_end - now).days)
        
        return {
            "status": subscription.status,
            "trialDaysRemaining": trial_days_remaining,
            "currentPeriodEnd": subscription.current_period_end,
            "cancelAtPeriodEnd": subscription.cancel_at_period_end,
        }
        
    except Exception as e:
        logger.error(f"Error fetching subscription status: {e}")
        return {"status": "error", "trialDaysRemaining": 0}

@app.post("/api/v1/subscriptions/cancel")
async def cancel_subscription(request: Request):
    """Cancel the current subscription at period end"""
    try:
        # Get auth header
        auth_header = request.headers.get('authorization')
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization required")
        
        # Extract token
        token = auth_header.replace('Bearer ', '')
        
        # Get user from Supabase auth
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        user_email = user.user.email
        
        # Search for customer by email
        customers = stripe.Customer.list(email=user_email, limit=1)
        
        if not customers.data:
            raise HTTPException(status_code=404, detail="No subscription found")
        
        customer = customers.data[0]
        
        # Get active subscriptions
        subscriptions = stripe.Subscription.list(
            customer=customer.id,
            status="active",
            limit=1
        )
        
        if not subscriptions.data:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        subscription = subscriptions.data[0]
        
        # Cancel at period end
        updated_subscription = stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=True
        )
        
        return {
            "success": True,
            "message": "Subscription will be canceled at period end",
            "current_period_end": subscription.current_period_end
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    if not sig_header:
        logger.error("No Stripe signature header found")
        raise HTTPException(status_code=400, detail="No signature header")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        logger.error("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Log the event
    logger.info(f"Received webhook event: {event['type']}")
    
    # Handle the event
    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            logger.info(f"Checkout completed for customer: {session.get('customer')}")
            # TODO: Update user subscription status in database
            
        elif event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            logger.info(f"Subscription created: {subscription['id']}")
            # TODO: Create subscription record
            
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            logger.info(f"Subscription updated: {subscription['id']}")
            # TODO: Update subscription record
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            logger.info(f"Subscription deleted: {subscription['id']}")
            # TODO: Mark subscription as canceled
            
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            logger.info(f"Payment succeeded for invoice: {invoice['id']}")
            # TODO: Update payment status
            
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            logger.info(f"Payment failed for invoice: {invoice['id']}")
            # TODO: Handle failed payment
            
        else:
            logger.info(f"Unhandled event type: {event['type']}")
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        # Don't raise exception - return 200 to acknowledge receipt
    
    return {"status": "success"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "webhook_enabled": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)