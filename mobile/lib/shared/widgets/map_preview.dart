import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class MapPreview extends StatelessWidget {
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
  Widget build(BuildContext context) {
    final point = LatLng(latitude ?? 42.8746, longitude ?? 74.5698);
    return ClipRRect(
      borderRadius: BorderRadius.circular(18),
      child: SizedBox(
        height: height,
        child: FlutterMap(
          options: MapOptions(
            initialCenter: point,
            initialZoom: 14,
            onTap: onTap == null
                ? null
                : (tapPosition, tappedPoint) =>
                    onTap!(tappedPoint.latitude, tappedPoint.longitude),
            interactionOptions: InteractionOptions(
              flags: interactive ? InteractiveFlag.all : InteractiveFlag.none,
            ),
          ),
          children: [
            TileLayer(
              urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
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
      ),
    );
  }
}
