import 'dart:async';

import 'package:electronics_marketplace_mobile/app/providers.dart';
import 'package:electronics_marketplace_mobile/core/auth/session_expiry_notifier.dart';
import 'package:electronics_marketplace_mobile/core/network/api_client.dart';
import 'package:electronics_marketplace_mobile/core/localization/app_locale_controller.dart';
import 'package:electronics_marketplace_mobile/core/storage/auth_session_storage.dart';
import 'package:electronics_marketplace_mobile/features/auth/data/auth_repository.dart';
import 'package:electronics_marketplace_mobile/features/auth/domain/auth_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AuthState {
  const AuthState({
    this.session,
    this.isLoading = false,
    this.error,
    this.resetMessage,
    this.debugResetToken,
  });

  final AuthSession? session;
  final bool isLoading;
  final String? error;
  final String? resetMessage;
  final String? debugResetToken;

  bool get isAuthenticated => session != null;

  AuthState copyWith({
    AuthSession? session,
    bool? isLoading,
    String? error,
    String? resetMessage,
    String? debugResetToken,
    bool clearSession = false,
    bool clearError = false,
    bool clearResetMessage = false,
    bool clearDebugResetToken = false,
  }) {
    return AuthState(
      session: clearSession ? null : (session ?? this.session),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      resetMessage:
          clearResetMessage ? null : (resetMessage ?? this.resetMessage),
      debugResetToken: clearDebugResetToken
          ? null
          : (debugResetToken ?? this.debugResetToken),
    );
  }
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(apiClientProvider));
});

final authSessionStorageProvider = Provider<AuthSessionStorage>((ref) {
  return AuthSessionStorage(ref.watch(sharedPreferencesProvider));
});

class AuthController extends StateNotifier<AuthState> {
  AuthController(
    this._repository,
    this._storage,
    SessionExpiryNotifier sessionExpiryNotifier,
  ) : super(const AuthState()) {
    _sessionExpirySubscription = sessionExpiryNotifier.stream.listen((_) {
      unawaited(
        _clearLocalSession(
          errorMessage: 'Session expired, please sign in again',
        ),
      );
    });
    unawaited(_restoreSession());
  }

  final AuthRepository _repository;
  final AuthSessionStorage _storage;
  late final StreamSubscription<void> _sessionExpirySubscription;

  String? get accessToken => state.session?.accessToken;
  AuthUser? get currentUser => state.session?.user;

  Future<void> _restoreSession() async {
    final saved = _storage.read();
    if (saved == null) {
      return;
    }
    state = state.copyWith(session: saved);
    try {
      final freshUser = await _repository.fetchCurrentUser(saved.accessToken);
      final session = AuthSession(
        accessToken: saved.accessToken,
        refreshToken: saved.refreshToken,
        user: freshUser,
      );
      await _storage.write(session);
      state = state.copyWith(session: session, clearError: true);
    } on ApiException catch (error) {
      if (error.statusCode == 401) {
        await _clearLocalSession();
        return;
      }
      await _clearLocalSession(errorMessage: error.message);
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(
      isLoading: true,
      clearError: true,
      clearResetMessage: true,
      clearSession: true,
    );
    try {
      final session = await _repository.login(email: email, password: password);
      if (session.user.roles.contains('admin')) {
        await _storage.clear();
        state = state.copyWith(
          isLoading: false,
          error: 'Admin accounts must use admin panel',
          clearSession: true,
        );
        return false;
      }
      await _storage.write(session);
      state = state.copyWith(session: session, isLoading: false);
      return true;
    } on ApiException catch (error) {
      await _storage.clear();
      state = state.copyWith(
        isLoading: false,
        error: error.message,
        clearSession: true,
      );
      return false;
    }
  }

  Future<bool> register({
    required String email,
    required String username,
    required String fullName,
    required String password,
    required String locale,
  }) async {
    state = state.copyWith(
        isLoading: true, clearError: true, clearResetMessage: true);
    try {
      final session = await _repository.register(
        email: email,
        username: username,
        fullName: fullName,
        password: password,
        locale: locale,
      );
      await _storage.write(session);
      state = state.copyWith(session: session, isLoading: false);
      return true;
    } on ApiException catch (error) {
      state = state.copyWith(isLoading: false, error: error.message);
      return false;
    }
  }

  Future<void> forgotPassword(String email) async {
    state = state.copyWith(
      isLoading: true,
      clearError: true,
      clearResetMessage: true,
      clearDebugResetToken: true,
    );
    try {
      final response = await _repository.forgotPassword(email);
      state = state.copyWith(
        isLoading: false,
        resetMessage: response.message,
        debugResetToken: response.debugResetToken,
      );
    } on ApiException catch (error) {
      state = state.copyWith(isLoading: false, error: error.message);
    }
  }

  Future<bool> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    state = state.copyWith(
      isLoading: true,
      clearError: true,
      clearResetMessage: true,
    );
    try {
      final message = await _repository.resetPassword(
        token: token,
        newPassword: newPassword,
      );
      state = state.copyWith(
        isLoading: false,
        resetMessage: message,
        clearDebugResetToken: true,
      );
      return true;
    } on ApiException catch (error) {
      state = state.copyWith(isLoading: false, error: error.message);
      return false;
    }
  }

  Future<void> signOut({bool silent = false}) async {
    final session = state.session;
    if (session != null) {
      try {
        await _repository.logout(
          accessToken: session.accessToken,
          refreshToken: session.refreshToken,
        );
      } catch (_) {}
    }
    await _storage.clear();
    state = const AuthState();
    if (!silent) {
      state = state.copyWith(clearError: true, clearResetMessage: true);
    }
  }

  Future<void> _clearLocalSession({String? errorMessage}) async {
    await _storage.clear();
    state = const AuthState();
    if (errorMessage != null && errorMessage.isNotEmpty) {
      state = state.copyWith(
        error: errorMessage,
        clearResetMessage: true,
        clearDebugResetToken: true,
      );
    }
  }

  @override
  void dispose() {
    _sessionExpirySubscription.cancel();
    super.dispose();
  }
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(
    ref.watch(authRepositoryProvider),
    ref.watch(authSessionStorageProvider),
    ref.watch(sessionExpiryNotifierProvider),
  );
});
