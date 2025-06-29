import React, { useState } from 'react';
import { Check, X, CreditCard, Calendar, Clock, AlertCircle } from 'lucide-react';
import { useStore } from '@/store/store';

interface SubscriptionFeature {
  name: string;
  freeTrialDays: number;
  proValue: string;
  description: string;
}

const features: SubscriptionFeature[] = [
  {
    name: 'Historical Data Access',
    freeTrialDays: 7,
    proValue: '365 days',
    description: 'Access to wildlife sighting history'
  },
  {
    name: 'Table View',
    freeTrialDays: 7,
    proValue: 'Unlimited',
    description: 'View sightings in a sortable table format'
  },
  {
    name: 'Enhanced Map Tools',
    freeTrialDays: 7,
    proValue: 'All tools',
    description: 'Advanced filtering and visualization options'
  },
  {
    name: 'Full Sighting Details',
    freeTrialDays: 7,
    proValue: 'Complete info',
    description: 'See all details including exact locations'
  },
  {
    name: 'Multi-Filtering',
    freeTrialDays: 7,
    proValue: 'Advanced filters',
    description: 'Filter by multiple criteria simultaneously'
  },
  {
    name: 'Saved Searches',
    freeTrialDays: 7,
    proValue: '50 searches',
    description: 'Save and quickly access your favorite searches'
  },
  {
    name: 'Offline GPS Data',
    freeTrialDays: 7,
    proValue: 'Download enabled',
    description: 'Download sighting data for offline use'
  }
];

export const SubscriptionPage: React.FC = () => {
  const { user } = useStore();
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');
  const [loading, setLoading] = useState(false);

  // Mock subscription status - replace with actual check
  const isTrialing = true;
  const trialDaysLeft = 5;
  const currentPlan = 'free_trial';

  const handleSubscribe = async () => {
    if (!user) {
      // Redirect to login
      return;
    }

    setLoading(true);
    try {
      // Handle subscription with Stripe
      console.log('Subscribing to:', billingPeriod);
    } catch (error) {
      console.error('Subscription error:', error);
    } finally {
      setLoading(false);
    }
  };

  const monthlyPrice = 15;
  const yearlyPrice = 149.99;
  const yearlySavings = (monthlyPrice * 12) - yearlyPrice;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
            <CreditCard className="w-8 h-8 mr-3 text-green-600" />
            Subscription
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage your subscription and access to premium features
          </p>
        </div>

        {/* Current Status */}
        {isTrialing && (
          <div className="mb-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
            <div className="flex items-start">
              <AlertCircle className="w-6 h-6 text-blue-600 mr-3 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">Free Trial Active</h3>
                <p className="mt-1 text-blue-700 dark:text-blue-300">
                  You have <strong>{trialDaysLeft} days</strong> remaining in your free trial.
                  Subscribe now to maintain access to all features after your trial ends.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Pricing Cards */}
        <div className="mb-12">
          <div className="flex justify-center mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-1 inline-flex">
              <button
                onClick={() => setBillingPeriod('monthly')}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  billingPeriod === 'monthly'
                    ? 'bg-green-600 text-white'
                    : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingPeriod('yearly')}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  billingPeriod === 'yearly'
                    ? 'bg-green-600 text-white'
                    : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
              >
                Yearly
                <span className="ml-1 text-xs">Save ${yearlySavings.toFixed(0)}</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Free Plan */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">Free</h3>
              <div className="mb-4">
                <span className="text-3xl font-bold">$0</span>
                <span className="text-gray-600 dark:text-gray-400">/month</span>
              </div>
              <p className="text-gray-600 dark:text-gray-400 mb-6">Basic access to wildlife sightings</p>
              
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">View recent sightings (5 days)</span>
                </li>
                <li className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">Basic map view</span>
                </li>
                <li className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">Simple filtering</span>
                </li>
                <li className="flex items-start">
                  <X className="w-5 h-5 text-gray-400 mr-2 flex-shrink-0" />
                  <span className="text-gray-500 dark:text-gray-400">Historical data</span>
                </li>
                <li className="flex items-start">
                  <X className="w-5 h-5 text-gray-400 mr-2 flex-shrink-0" />
                  <span className="text-gray-500 dark:text-gray-400">Advanced features</span>
                </li>
              </ul>

              <button
                disabled
                className="w-full py-2 px-4 bg-gray-200 text-gray-500 font-medium rounded-md cursor-not-allowed"
              >
                Current Plan
              </button>
            </div>

            {/* Pro Plan */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border-2 border-green-500 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                  Recommended
                </span>
              </div>
              
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">Pro</h3>
              <div className="mb-4">
                <span className="text-3xl font-bold">
                  ${billingPeriod === 'monthly' ? monthlyPrice : yearlyPrice}
                </span>
                <span className="text-gray-600 dark:text-gray-400">
                  /{billingPeriod === 'monthly' ? 'month' : 'year'}
                </span>
                {billingPeriod === 'yearly' && (
                  <p className="text-sm text-green-600 mt-1">
                    Save ${yearlySavings.toFixed(0)} per year
                  </p>
                )}
              </div>
              <p className="text-gray-600 dark:text-gray-400 mb-6">Full access to all features</p>
              
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">365 days of historical data</span>
                </li>
                <li className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">Table view & data export</span>
                </li>
                <li className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">Enhanced map tools</span>
                </li>
                <li className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">Multi-filtering & saved searches</span>
                </li>
                <li className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">Download for offline GPS</span>
                </li>
                <li className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">Email notifications</span>
                </li>
                <li className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">Priority support</span>
                </li>
              </ul>

              <button
                onClick={handleSubscribe}
                disabled={loading}
                className="w-full py-2 px-4 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Processing...' : 'Subscribe to Pro'}
              </button>
            </div>
          </div>
        </div>

        {/* Feature Comparison */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
          <div className="p-6 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Feature Comparison</h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              See what's included in each plan
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Feature
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Free Trial
                    <span className="block text-xs font-normal normal-case mt-1">
                      ({trialDaysLeft} days left)
                    </span>
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Free
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Pro
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {features.map((feature) => (
                  <tr key={feature.name}>
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {feature.name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {feature.description}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Check className="w-5 h-5 text-green-500 mx-auto" />
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {feature.freeTrialDays} days
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <X className="w-5 h-5 text-gray-400 mx-auto" />
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Check className="w-5 h-5 text-green-500 mx-auto" />
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {feature.proValue}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* FAQ */}
        <div className="mt-12 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            Questions about billing? Contact us at{' '}
            <a href="mailto:support@wildlifesightings.com" className="text-green-600 hover:text-green-700">
              support@wildlifesightings.com
            </a>
          </p>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            All payments are processed securely through Stripe. Cancel anytime.
          </p>
        </div>
      </div>
    </div>
  );
};