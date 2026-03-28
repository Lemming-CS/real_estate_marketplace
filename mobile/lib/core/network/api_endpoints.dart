class ApiEndpoints {
  static const authLogin = '/auth/login';
  static const authRegister = '/auth/register';
  static const authForgotPassword = '/auth/forgot-password';
  static const authMe = '/auth/me';
  static const authLogout = '/auth/logout';

  static const profileMe = '/profile/me';
  static const profileImage = '/profile/me/image';

  static const listings = '/listings';
  static const myListings = '/listings/me';
  static String listingDetail(String listingId) => '/listings/$listingId';
  static String publishListing(String listingId) =>
      '/listings/$listingId/publish';
  static String listingMedia(String listingId) => '/listings/$listingId/media';

  static const favorites = '/favorites';
  static String favorite(String listingId) => '/favorites/$listingId';

  static String publicUser(String userId) => '/public/users/$userId';
  static String publicUserListings(String userId) =>
      '/public/users/$userId/listings';

  static String media(String assetKey) => '/media/$assetKey';
}
