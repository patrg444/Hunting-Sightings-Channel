/**
 * Feature flags service to control feature availability based on subscription status
 */

interface FeatureFlags {
  multiFiltering: boolean;
  exportData: boolean;
  emailNotifications: boolean;
  historicalData: boolean;
  apiAccess: boolean;
  enableLocationClustering: boolean;
  enableAdvancedFilters: boolean;
  fullSightingDetails: boolean;
  tableView: boolean;
}

class FeatureFlagsService {
  private userSubscription: string | null = null;

  setUserSubscription(subscriptionType: string | null) {
    this.userSubscription = subscriptionType;
  }

  getFeatures(): FeatureFlags {
    const isPro = this.userSubscription === 'pro_monthly' || this.userSubscription === 'pro_yearly';

    return {
      multiFiltering: isPro,
      exportData: isPro,
      emailNotifications: isPro,
      historicalData: isPro,
      apiAccess: this.userSubscription === 'pro_yearly',
      enableLocationClustering: true,
      enableAdvancedFilters: true,
      fullSightingDetails: isPro,
      tableView: isPro,
    };
  }

  hasFeature(feature: keyof FeatureFlags): boolean {
    return this.getFeatures()[feature];
  }
}

export const featureFlags = new FeatureFlagsService();