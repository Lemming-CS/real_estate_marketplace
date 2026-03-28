import 'package:flutter/material.dart';

class AsyncStateView extends StatelessWidget {
  const AsyncStateView({
    super.key,
    required this.isLoading,
    required this.error,
    required this.child,
    this.emptyMessage,
    this.isEmpty = false,
  });

  final bool isLoading;
  final String? error;
  final bool isEmpty;
  final String? emptyMessage;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(error!, textAlign: TextAlign.center),
        ),
      );
    }
    if (isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(emptyMessage ?? 'Nothing here yet.',
              textAlign: TextAlign.center),
        ),
      );
    }
    return child;
  }
}
