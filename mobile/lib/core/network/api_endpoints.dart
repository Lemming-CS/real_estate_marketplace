class ApiEndpoints {
  static const authLogin = '/auth/login';
  static const authRegister = '/auth/register';
  static const authForgotPassword = '/auth/forgot-password';
  static const authResetPassword = '/auth/reset-password';
  static const authMe = '/auth/me';
  static const authLogout = '/auth/logout';

  static const profileMe = '/profile/me';
  static const profileImage = '/profile/me/image';

  static const listings = '/listings';
  static const myListings = '/listings/me';
  static String listingDetail(String listingId) => '/listings/$listingId';
  static String publishListing(String listingId) =>
      '/listings/$listingId/publish';
  static String markListingSold(String listingId) =>
      '/listings/$listingId/mark-sold';
  static String listingMedia(String listingId) => '/listings/$listingId/media';
  static String listingMediaItem(String listingId, String mediaId) =>
      '/listings/$listingId/media/$mediaId';
  static String listingMediaPrimary(String listingId, String mediaId) =>
      '/listings/$listingId/media/$mediaId/primary';
  static String listingMediaOrder(String listingId) =>
      '/listings/$listingId/media/order';

  static const favorites = '/favorites';
  static String favorite(String listingId) => '/favorites/$listingId';

  static const conversations = '/conversations';
  static String conversation(String conversationId) =>
      '/conversations/$conversationId';
  static String conversationFromListing(String listingId) =>
      '/conversations/from-listing/$listingId';
  static String conversationMessages(String conversationId) =>
      '/conversations/$conversationId/messages';
  static String conversationRead(String conversationId) =>
      '/conversations/$conversationId/read';

  static const notifications = '/notifications';
  static const notificationUnreadCount = '/notifications/unread-count';
  static String notificationRead(int notificationId) =>
      '/notifications/$notificationId/read';

  static const payments = '/payments';
  static const paymentPromotionInitiate = '/payments/promotions/initiate';
  static String paymentSimulate(String paymentId) =>
      '/payments/$paymentId/simulate';
  static const promotionsMe = '/promotions/me';
  static const promotionPackages = '/promotion-packages';

  static const reports = '/reports';
  static const myReports = '/reports/me';

  static String publicUser(String userId) => '/public/users/$userId';
  static String publicUserListings(String userId) =>
      '/public/users/$userId/listings';

  static String media(String assetKey) => '/media/$assetKey';
}
