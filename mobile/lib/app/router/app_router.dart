import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/screens/forgot_password_screen.dart';
import 'package:electronics_marketplace_mobile/features/home/presentation/screens/home_screen.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/screens/login_screen.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/screens/register_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/favorites_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/listing_detail_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/listing_form_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/my_listings_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/public_user_listings_screen.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/screens/public_user_profile_screen.dart';
import 'package:electronics_marketplace_mobile/features/profile/presentation/screens/profile_screen.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final isAuthenticated = ref.watch(
    authControllerProvider.select((state) => state.isAuthenticated),
  );
  bool requiresAuth(String location) {
    return location == '/favorites' ||
        location == '/my-listings' ||
        location == '/create-listing' ||
        location == '/profile' ||
        location.startsWith('/edit-listing/');
  }

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final location = state.matchedLocation;
      final authPages = {'/login', '/register'};

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
        path: '/profile',
        builder: (context, state) => const ProfileScreen(),
      ),
    ],
  );
});
