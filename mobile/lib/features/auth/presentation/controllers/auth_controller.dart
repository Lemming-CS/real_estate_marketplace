import 'dart:async';

import 'package:electronics_marketplace_mobile/app/providers.dart';
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
  });

  final AuthSession? session;
  final bool isLoading;
  final String? error;
  final String? resetMessage;

  bool get isAuthenticated => session != null;

  AuthState copyWith({
    AuthSession? session,
    bool? isLoading,
    String? error,
    String? resetMessage,
    bool clearSession = false,
    bool clearError = false,
    bool clearResetMessage = false,
  }) {
    return AuthState(
      session: clearSession ? null : (session ?? this.session),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      resetMessage:
          clearResetMessage ? null : (resetMessage ?? this.resetMessage),
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
  AuthController(this._repository, this._storage) : super(const AuthState()) {
    unawaited(_restoreSession());
  }

  final AuthRepository _repository;
  final AuthSessionStorage _storage;

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
      await signOut(silent: true);
      state = state.copyWith(error: error.message);
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(
        isLoading: true, clearError: true, clearResetMessage: true);
    try {
      final session = await _repository.login(email: email, password: password);
      await _storage.write(session);
      state = state.copyWith(session: session, isLoading: false);
      return true;
    } on ApiException catch (error) {
      state = state.copyWith(isLoading: false, error: error.message);
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
        isLoading: true, clearError: true, clearResetMessage: true);
    try {
      final message = await _repository.forgotPassword(email);
      state = state.copyWith(isLoading: false, resetMessage: message);
    } on ApiException catch (error) {
      state = state.copyWith(isLoading: false, error: error.message);
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
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(
    ref.watch(authRepositoryProvider),
    ref.watch(authSessionStorageProvider),
  );
});
