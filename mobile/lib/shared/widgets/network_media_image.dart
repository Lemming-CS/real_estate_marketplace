import 'package:electronics_marketplace_mobile/core/config/app_config.dart';
import 'package:electronics_marketplace_mobile/core/network/api_endpoints.dart';
import 'package:flutter/material.dart';

class NetworkMediaImage extends StatelessWidget {
  const NetworkMediaImage({
    super.key,
    this.assetKey,
    this.requestPath,
    this.accessToken,
    this.fit = BoxFit.cover,
    this.height,
    this.width,
    this.borderRadius,
  }) : assert(assetKey != null || requestPath != null);

  final String? assetKey;
  final String? requestPath;
  final String? accessToken;
  final BoxFit fit;
  final double? height;
  final double? width;
  final BorderRadius? borderRadius;

  @override
  Widget build(BuildContext context) {
    final uri = Uri.parse(AppConfig.apiBaseUrl);
    final baseOrigin =
        '${uri.scheme}://${uri.host}${uri.hasPort ? ':${uri.port}' : ''}';
    final imageUrl = _resolveUrl(baseOrigin);
    return LayoutBuilder(
      builder: (context, constraints) {
        final devicePixelRatio = MediaQuery.devicePixelRatioOf(context);
        final resolvedWidth = _resolveDimension(width, constraints.maxWidth);
        final resolvedHeight = _resolveDimension(height, constraints.maxHeight);
        final cacheWidth = resolvedWidth == null
            ? null
            : (resolvedWidth * devicePixelRatio).round();
        final cacheHeight = resolvedHeight == null
            ? null
            : (resolvedHeight * devicePixelRatio).round();

        final image = Image.network(
          imageUrl,
          headers: accessToken == null
              ? null
              : {'Authorization': 'Bearer $accessToken'},
          fit: fit,
          height: height,
          width: width,
          cacheWidth: cacheWidth,
          cacheHeight: cacheHeight,
          filterQuality: FilterQuality.medium,
          errorBuilder: (context, error, stackTrace) => _placeholder(context),
          loadingBuilder: (context, child, loadingProgress) {
            if (loadingProgress == null) {
              return child;
            }
            return _placeholder(context, loading: true);
          },
        );
        final content = borderRadius == null
            ? image
            : ClipRRect(borderRadius: borderRadius!, child: image);
        return RepaintBoundary(child: content);
      },
    );
  }

  String _resolveUrl(String baseOrigin) {
    if (requestPath != null && requestPath!.isNotEmpty) {
      if (requestPath!.startsWith('http://') ||
          requestPath!.startsWith('https://')) {
        return requestPath!;
      }
      if (requestPath!.startsWith('/')) {
        return '$baseOrigin$requestPath';
      }
      return '$baseOrigin/$requestPath';
    }
    return '$baseOrigin/api/v1${ApiEndpoints.media(assetKey!)}';
  }

  double? _resolveDimension(double? preferred, double maxConstraint) {
    if (preferred != null && preferred.isFinite) {
      return preferred;
    }
    if (maxConstraint.isFinite && maxConstraint > 0) {
      return maxConstraint;
    }
    return null;
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
