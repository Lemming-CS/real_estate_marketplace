import 'package:electronics_marketplace_mobile/features/auth/presentation/screens/login_screen.dart';
import 'package:electronics_marketplace_mobile/features/home/presentation/screens/home_screen.dart';
import 'package:go_router/go_router.dart';

class AppRouter {
  static final GoRouter router = GoRouter(
    routes: <GoRoute>[
      GoRoute(
        path: '/',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
    ],
  );
}

