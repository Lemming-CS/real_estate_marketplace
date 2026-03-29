import 'package:flutter/material.dart';

class BadgeIconButton extends StatelessWidget {
  const BadgeIconButton({
    super.key,
    required this.icon,
    required this.onPressed,
    this.count = 0,
    this.tooltip,
  });

  final IconData icon;
  final VoidCallback? onPressed;
  final int count;
  final String? tooltip;

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        IconButton(
          onPressed: onPressed,
          icon: Icon(icon),
          tooltip: tooltip,
        ),
        if (count > 0)
          Positioned(
            right: 8,
            top: 8,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.error,
                borderRadius: BorderRadius.circular(999),
              ),
              constraints: const BoxConstraints(minWidth: 18),
              child: Text(
                count > 99 ? '99+' : '$count',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Theme.of(context).colorScheme.onError,
                    ),
              ),
            ),
          ),
      ],
    );
  }
}
