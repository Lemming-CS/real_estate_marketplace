import 'package:electronics_marketplace_mobile/core/config/app_config.dart';
import 'package:electronics_marketplace_mobile/core/network/api_endpoints.dart';
import 'package:flutter/material.dart';

class NetworkMediaImage extends StatelessWidget {
  const NetworkMediaImage({
    super.key,
    required this.assetKey,
    this.fit = BoxFit.cover,
    this.height,
    this.width,
    this.borderRadius,
  });

  final String assetKey;
  final BoxFit fit;
  final double? height;
  final double? width;
  final BorderRadius? borderRadius;

  @override
  Widget build(BuildContext context) {
    final uri = Uri.parse(AppConfig.apiBaseUrl);
    final baseOrigin =
        '${uri.scheme}://${uri.host}${uri.hasPort ? ':${uri.port}' : ''}';
    final imageUrl = '$baseOrigin/api/v1${ApiEndpoints.media(assetKey)}';
    final image = Image.network(
      imageUrl,
      fit: fit,
      height: height,
      width: width,
      errorBuilder: (context, error, stackTrace) => _placeholder(context),
      loadingBuilder: (context, child, loadingProgress) {
        if (loadingProgress == null) {
          return child;
        }
        return _placeholder(context, loading: true);
      },
    );
    if (borderRadius == null) {
      return image;
    }
    return ClipRRect(borderRadius: borderRadius!, child: image);
  }

  Widget _placeholder(BuildContext context, {bool loading = false}) {
    return Container(
      height: height,
      width: width,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: borderRadius,
      ),
      child: loading
          ? const CircularProgressIndicator()
          : const Icon(Icons.image_not_supported_outlined),
    );
  }
}
