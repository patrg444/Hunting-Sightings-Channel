export const oauthProviders = {
  google: {
    enabled: false, // Set to true when Google OAuth is configured in Supabase
    clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
  },
};

export const isOAuthConfigured = (provider: keyof typeof oauthProviders): boolean => {
  const config = oauthProviders[provider];
  return config.enabled && !!config.clientId;
};