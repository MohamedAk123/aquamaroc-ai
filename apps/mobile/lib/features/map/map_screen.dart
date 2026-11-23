import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:material_ui/material_ui.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../domain/models.dart';
import '../../presentation/widgets.dart';

class MapScreen extends StatefulWidget {
  final Catalog catalog;
  final ValueChanged<Snapshot> onOpen;
  const MapScreen({super.key, required this.catalog, required this.onOpen});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  static const center = LatLng(31.55, -8.4);
  static const initialZoom = 6.0;
  static const tileUrl = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
  final controller = MapController();
  bool tileError = false;
  int tileAttempt = 0;

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  void zoom(double delta) {
    final camera = controller.camera;
    controller.move(camera.center, camera.zoom + delta);
  }

  Future<void> showAttribution() async {
    final opened = await launchUrl(
      Uri.https('www.openstreetmap.org', '/copyright'),
    );
    if (!opened && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Licence : openstreetmap.org/copyright')),
      );
    }
  }

  void showReservoirs(List<Snapshot> reservoirs) {
    showModalBottomSheet<void>(
      context: context,
      builder: (sheetContext) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            for (final item in reservoirs)
              ListTile(
                title: Text(item.reservoir.name),
                subtitle: Text('Source : ${item.reservoir.coordinatesSource}'),
                onTap: () {
                  Navigator.of(sheetContext).pop();
                  widget.onOpen(item);
                },
              ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final located = widget.catalog.overview.reservoirs
        .where(
          (item) =>
              item.reservoir.hasVerifiedCoordinates &&
              item.reservoir.latitude!.abs() <= 85.0511,
        )
        .toList(growable: false);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Stack(
              fit: StackFit.expand,
              children: [
                Semantics(
                  label: 'Fond cartographique interactif',
                  child: FlutterMap(
                    mapController: controller,
                    options: const MapOptions(
                      initialCenter: center,
                      initialZoom: initialZoom,
                      minZoom: 4,
                      maxZoom: 17,
                      backgroundColor: Color(0xffdfedf7),
                      interactionOptions: InteractionOptions(
                        flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
                      ),
                    ),
                    children: [
                      TileLayer(
                        key: ValueKey(tileAttempt),
                        urlTemplate: tileUrl,
                        userAgentPackageName: 'ma.aquamaroc.aquamaroc_mobile',
                        panBuffer: 0,
                        errorTileCallback: (_, _, _) {
                          if (mounted && !tileError) {
                            setState(() => tileError = true);
                          }
                        },
                      ),
                      MarkerLayer(
                        markers: [
                          for (final item in located)
                            Marker(
                              point: LatLng(
                                item.reservoir.latitude!,
                                item.reservoir.longitude!,
                              ),
                              width: 48,
                              height: 48,
                              child: IconButton(
                                tooltip: item.reservoir.name,
                                color: navy,
                                icon: const Icon(Icons.location_pin, size: 32),
                                onPressed: () => widget.onOpen(item),
                              ),
                            ),
                        ],
                      ),
                    ],
                  ),
                ),
                Positioned(
                  top: 8,
                  right: 8,
                  child: Card(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          tooltip: 'Zoom avant',
                          onPressed: () => zoom(1),
                          icon: const Icon(Icons.add),
                        ),
                        IconButton(
                          tooltip: 'Zoom arrière',
                          onPressed: () => zoom(-1),
                          icon: const Icon(Icons.remove),
                        ),
                        IconButton(
                          tooltip: 'Recentrer la carte',
                          onPressed: () => controller.move(center, initialZoom),
                          icon: const Icon(Icons.center_focus_strong),
                        ),
                      ],
                    ),
                  ),
                ),
                Positioned(
                  right: 8,
                  bottom: 4,
                  child: Card(
                    child: TextButton(
                      onPressed: showAttribution,
                      child: const Text('© OpenStreetMap'),
                    ),
                  ),
                ),
                if (tileError)
                  Positioned(
                    bottom: 56,
                    left: 8,
                    right: 8,
                    child: Notice(
                      'Certaines tuiles sont indisponibles.',
                      warning: true,
                      action: TextButton(
                        onPressed: () => setState(() {
                          tileError = false;
                          tileAttempt++;
                        }),
                        child: const Text('Réessayer'),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
        if (located.isEmpty)
          const Padding(
            padding: EdgeInsets.only(top: 8),
            child: Text(
              'Coordonnées vérifiées non disponibles pour les barrages suivis.',
            ),
          )
        else
          TextButton.icon(
            onPressed: () => showReservoirs(located),
            icon: const Icon(Icons.list),
            label: Text('${located.length} barrages localisés'),
          ),
      ],
    );
  }
}
