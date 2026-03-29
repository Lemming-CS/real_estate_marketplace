import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/reports/data/reports_repository.dart';
import 'package:electronics_marketplace_mobile/features/reports/domain/report_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final myReportsProvider = FutureProvider.autoDispose<ReportPage>((ref) async {
  final token = ref.watch(authControllerProvider).session?.accessToken;
  if (token == null) {
    throw StateError('Authentication required.');
  }
  return ref.watch(reportsRepositoryProvider).getMyReports(accessToken: token);
});
