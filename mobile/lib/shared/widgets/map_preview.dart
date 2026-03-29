import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class MapPreview extends StatefulWidget {
  const MapPreview({
    super.key,
    this.latitude,
    this.longitude,
    this.interactive = false,
    this.height = 220,
    this.onTap,
  });

  final double? latitude;
  final double? longitude;
  final bool interactive;
  final double height;
  final void Function(double latitude, double longitude)? onTap;

  @override
  State<MapPreview> createState() => _MapPreviewState();
}

class _MapPreviewState extends State<MapPreview> {
  static const LatLng _defaultPoint = LatLng(42.8746, 74.5698);
  static const double _defaultZoom = 14;

  late final MapController _mapController;

  @override
  void initState() {
    super.initState();
    _mapController = MapController();
  }

  @override
  void didUpdateWidget(covariant MapPreview oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.latitude != widget.latitude ||
        oldWidget.longitude != widget.longitude) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) {
          return;
        }
        _mapController.move(_point, _defaultZoom);
      });
    }
  }

  LatLng get _point => LatLng(
        widget.latitude ?? _defaultPoint.latitude,
        widget.longitude ?? _defaultPoint.longitude,
      );

  @override
  Widget build(BuildContext context) {
    final point = _point;
    return RepaintBoundary(
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: SizedBox(
          height: widget.height,
          child: Stack(
            children: [
              FlutterMap(
                mapController: _mapController,
                options: MapOptions(
                  initialCenter: point,
                  initialZoom: _defaultZoom,
                  onTap: widget.onTap == null
                      ? null
                      : (tapPosition, tappedPoint) => widget.onTap!(
                            tappedPoint.latitude,
                            tappedPoint.longitude,
                          ),
                  interactionOptions: InteractionOptions(
                    flags: widget.interactive
                        ? InteractiveFlag.all
                        : InteractiveFlag.none,
                  ),
                ),
                children: [
                  TileLayer(
                    urlTemplate:
                        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    userAgentPackageName: 'electronics_marketplace_mobile',
                  ),
                  MarkerLayer(
                    markers: [
                      Marker(
                        point: point,
                        width: 40,
                        height: 40,
                        child: const Icon(Icons.location_pin,
                            color: Colors.red, size: 36),
                      ),
                    ],
                  ),
                ],
              ),
              if (widget.interactive)
                Positioned(
                  right: 12,
                  top: 12,
                  child: FloatingActionButton.small(
                    heroTag: null,
                    onPressed: () => _mapController.move(point, _defaultZoom),
                    child: const Icon(Icons.my_location_outlined),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
