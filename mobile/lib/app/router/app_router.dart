import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/screens/forgot_password_screen.dart';
import 'package:electronics_marketplace_mobile/features/commerce/presentation/screens/commerce_history_screen.dart';
import 'package:electronics_marketplace_mobile/features/commerce/presentation/screens/promote_listing_screen.dart';
import 'package:electronics_marketplace_mobile/features/home/presentation/screens/home_screen.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/screens/login_screen.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/screens/register_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/favorites_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/listing_detail_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/listing_form_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/my_listings_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/public_user_listings_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/public_user_profile_screen.dart';
import 'package:electronics_marketplace_mobile/features/messaging/presentation/screens/conversation_detail_screen.dart';
import 'package:electronics_marketplace_mobile/features/messaging/presentation/screens/conversations_screen.dart';
import 'package:electronics_marketplace_mobile/features/notifications/presentation/screens/notifications_screen.dart';
import 'package:electronics_marketplace_mobile/features/profile/presentation/screens/profile_screen.dart';
import 'package:electronics_marketplace_mobile/features/reports/presentation/screens/my_reports_screen.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authControllerProvider);
  final isAuthenticated = authState.isAuthenticated;
  final sessionExpired =
      authState.error == 'Session expired, please sign in again';
  bool isAuthPage(String location) {
    return location == '/login' ||
        location == '/register' ||
        location == '/forgot-password';
  }

  bool shouldRedirectToLogin(String location) {
    return sessionExpired && !isAuthPage(location);
  }

  bool requiresAuth(String location) {
    return location == '/favorites' ||
        location == '/my-listings' ||
        location == '/create-listing' ||
        location == '/conversations' ||
        location == '/notifications' ||
        location == '/commerce-history' ||
        location == '/my-reports' ||
        location == '/profile' ||
        location.startsWith('/edit-listing/') ||
        location.startsWith('/conversations/') ||
        location.startsWith('/promote-listing/');
  }

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final location = state.matchedLocation;
      final authPages = {'/login', '/register'};

      if (shouldRedirectToLogin(location)) {
        return '/login';
      }

      if (location == '/forgot-password') {
        return null;
      }

      if (!isAuthenticated && requiresAuth(location)) {
        return '/login';
      }

      if (isAuthenticated && authPages.contains(location)) {
        return '/';
      }

      return null;
    },
    routes: <GoRoute>[
      GoRoute(
        path: '/',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/listing/:listingId',
        builder: (context, state) => ListingDetailScreen(
          listingId: state.pathParameters['listingId']!,
        ),
      ),
      GoRoute(
        path: '/seller/:userId',
        builder: (context, state) => PublicUserProfileScreen(
          userId: state.pathParameters['userId']!,
        ),
      ),
      GoRoute(
        path: '/seller/:userId/listings',
        builder: (context, state) => PublicUserListingsScreen(
          userId: state.pathParameters['userId']!,
        ),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/forgot-password',
        builder: (context, state) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: '/favorites',
        builder: (context, state) => const FavoritesScreen(),
      ),
      GoRoute(
        path: '/conversations',
        builder: (context, state) => const ConversationsScreen(),
      ),
      GoRoute(
        path: '/conversations/:conversationId',
        builder: (context, state) => ConversationDetailScreen(
          conversationId: state.pathParameters['conversationId']!,
        ),
      ),
      GoRoute(
        path: '/notifications',
        builder: (context, state) => const NotificationsScreen(),
      ),
      GoRoute(
        path: '/commerce-history',
        builder: (context, state) => const CommerceHistoryScreen(),
      ),
      GoRoute(
        path: '/my-reports',
        builder: (context, state) => const MyReportsScreen(),
      ),
      GoRoute(
        path: '/my-listings',
        builder: (context, state) => const MyListingsScreen(),
      ),
      GoRoute(
        path: '/create-listing',
        builder: (context, state) => const ListingFormScreen(),
      ),
      GoRoute(
        path: '/edit-listing/:listingId',
        builder: (context, state) => ListingFormScreen(
          listingId: state.pathParameters['listingId'],
        ),
      ),
      GoRoute(
        path: '/promote-listing/:listingId',
        builder: (context, state) => PromoteListingScreen(
          listingId: state.pathParameters['listingId']!,
        ),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) => const ProfileScreen(),
      ),
    ],
  );
});
