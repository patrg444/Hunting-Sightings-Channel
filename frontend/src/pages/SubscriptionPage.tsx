import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/store';
import { authService } from '../services/auth';
import { Check, X, Loader2, CreditCard, Calendar, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../config/constants';

interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  interval: 'month' | 'year';
  features: string[];
  highlighted?: boolean;
}

interface UserSubscription {
  plan: string;
  status: 'active' | 'canceled' | 'past_due';
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
}

const PLANS: SubscriptionPlan[] = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    interval: 'month',
    features: [
      'View wildlife sightings',
      'Basic map features',
      'Single filter at a time',
      'Last 30 days of data'
    ]
  },
  {
    id: 'pro_monthly',
    name: 'Pro Monthly',
    price: 9.99,
    interval: 'month',
    highlighted: true,
    features: [
      'Everything in Free',
      'Advanced filtering',
      'Multiple filters at once',
      'Historical data (1 year)',
      'Email notifications',
      'Export sightings data',
      'Priority support'
    ]
  },
  {
    id: 'pro_yearly',
    name: 'Pro Yearly',
    price: 99.99,
    interval: 'year',
    features: [
      'Everything in Pro Monthly',
      'Save 17% compared to monthly',
      'Early access to new features',
      'API access (coming soon)'
    ]
  }
];

export function SubscriptionPage() {
  const navigate = useNavigate();
  const { user } = useStore();
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subscription, setSubscription] = useState<UserSubscription | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }

    fetchSubscription();
  }, [user, navigate]);

  const fetchSubscription = async () => {
    try {
      setLoading(true);
      const token = await authService.getAccessToken();
      const response = await axios.get(`${API_URL}/api/v1/users/${user?.id}/subscription`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSubscription(response.data);
    } catch (error) {
      console.error('Failed to fetch subscription:', error);
      // Assume free plan if fetch fails
      setSubscription(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planId: string) => {
    if (planId === 'free') return;

    try {
      setProcessing(true);
      setError(null);
      
      const token = await authService.getAccessToken();
      const response = await axios.post(
        `${API_URL}/api/v1/subscriptions/create-checkout`, 
        { planId },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Redirect to Stripe checkout
      if (response.data.checkoutUrl) {
        window.location.href = response.data.checkoutUrl;
      }
    } catch (error) {
      console.error('Failed to create checkout:', error);
      setError('Failed to start subscription process. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will retain access until the end of your billing period.')) {
      return;
    }

    try {
      setProcessing(true);
      setError(null);
      
      const token = await authService.getAccessToken();
      await axios.post(
        `${API_URL}/api/v1/subscriptions/cancel`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      await fetchSubscription();
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      setError('Failed to cancel subscription. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const currentPlanId = subscription?.plan || 'free';

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Choose Your Plan</h1>
          <p className="text-xl text-gray-600">
            Unlock advanced features and support wildlife conservation
          </p>
        </div>

        {/* Current Subscription Status */}
        {subscription && subscription.status === 'active' && (
          <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-900 font-medium">
                  Current Plan: {PLANS.find(p => p.id === subscription.plan)?.name}
                </p>
                <p className="text-sm text-blue-700">
                  {subscription.cancelAtPeriodEnd
                    ? `Cancels on ${new Date(subscription.currentPeriodEnd).toLocaleDateString()}`
                    : `Renews on ${new Date(subscription.currentPeriodEnd).toLocaleDateString()}`
                  }
                </p>
              </div>
              {subscription.plan !== 'free' && !subscription.cancelAtPeriodEnd && (
                <button
                  onClick={handleCancelSubscription}
                  disabled={processing}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Cancel Subscription
                </button>
              )}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8">
          {PLANS.map((plan) => {
            const isCurrentPlan = plan.id === currentPlanId;
            const isDowngrade = PLANS.findIndex(p => p.id === plan.id) < PLANS.findIndex(p => p.id === currentPlanId);
            
            return (
              <div
                key={plan.id}
                className={`bg-white rounded-lg shadow-lg overflow-hidden ${
                  plan.highlighted ? 'ring-2 ring-blue-500' : ''
                }`}
              >
                {plan.highlighted && (
                  <div className="bg-blue-500 text-white text-center py-2 text-sm font-medium">
                    Most Popular
                  </div>
                )}
                
                <div className="p-6">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  
                  <div className="mb-6">
                    <span className="text-4xl font-bold text-gray-900">
                      ${plan.price}
                    </span>
                    <span className="text-gray-600">/{plan.interval}</span>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {isCurrentPlan ? (
                    <button
                      disabled
                      className="w-full py-3 px-4 bg-gray-100 text-gray-600 rounded-lg font-medium cursor-not-allowed"
                    >
                      Current Plan
                    </button>
                  ) : isDowngrade ? (
                    <button
                      disabled
                      className="w-full py-3 px-4 bg-gray-100 text-gray-600 rounded-lg font-medium cursor-not-allowed"
                    >
                      Downgrade Not Available
                    </button>
                  ) : (
                    <button
                      onClick={() => handleSubscribe(plan.id)}
                      disabled={processing}
                      className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                        plan.highlighted
                          ? 'bg-blue-600 text-white hover:bg-blue-700'
                          : 'bg-gray-900 text-white hover:bg-gray-800'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {processing ? (
                        <span className="flex items-center justify-center">
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Processing...
                        </span>
                      ) : (
                        'Upgrade Now'
                      )}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* FAQ Section */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            Frequently Asked Questions
          </h2>
          
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                Can I cancel my subscription anytime?
              </h3>
              <p className="text-gray-600">
                Yes! You can cancel your subscription at any time. You'll retain access to Pro features until the end of your billing period.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                What payment methods do you accept?
              </h3>
              <p className="text-gray-600">
                We accept all major credit cards and debit cards through our secure payment processor, Stripe.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                Is my payment information secure?
              </h3>
              <p className="text-gray-600">
                Absolutely. We use Stripe for payment processing and never store your credit card information on our servers.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                How does the yearly plan save money?
              </h3>
              <p className="text-gray-600">
                The yearly plan costs $99.99 per year, which works out to about $8.33 per month - saving you 17% compared to the monthly plan.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center">
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 hover:text-blue-700"
          >
            ← Back to Map
          </button>
        </div>
      </div>
    </div>
  );
}