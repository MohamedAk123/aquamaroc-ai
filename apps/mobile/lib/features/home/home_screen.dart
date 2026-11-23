import 'package:material_ui/material_ui.dart';

import '../../domain/models.dart';
import '../../presentation/app_controller.dart';
import '../../presentation/reservoir_art.dart';
import '../../presentation/widgets.dart';

class HomeScreen extends StatelessWidget {
  final Catalog catalog;
  final AppController controller;
  final ValueChanged<Snapshot> onOpen;
  final VoidCallback onBrowse, onMap, onFavorites, onSources, onVariations;
  final VoidCallback onForecasts;
  final DateTime syncedAt;
  const HomeScreen({
    super.key,
    required this.catalog,
    required this.controller,
    required this.onOpen,
    required this.onBrowse,
    required this.onMap,
    required this.onFavorites,
    required this.onSources,
    required this.onVariations,
    required this.onForecasts,
    required this.syncedAt,
  });

  @override
  Widget build(BuildContext context) {
    final overview = catalog.overview;
    final favorites = overview.reservoirs.where(
      (item) => controller.favorites.contains(item.reservoir.id),
    );
    final actions = <(String, IconData, VoidCallback)>[
      ('Barrages', Icons.bar_chart, onBrowse),
      ('Analyse IA', Icons.timeline, onVariations),
      ('Prévisions IA', Icons.psychology_outlined, onForecasts),
      ('Carte', Icons.location_on_outlined, onMap),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const ReservoirBanner(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Bonjour !',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 30,
                  fontWeight: FontWeight.w800,
                ),
              ),
              Text(
                'Découvrez la situation des barrages et leurs dernières mesures publiées.',
                style: TextStyle(color: Colors.white, fontSize: 15),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        LayoutBuilder(
          builder: (context, constraints) {
            final columns =
                MediaQuery.textScalerOf(context).scale(14) > 19 ||
                    constraints.maxWidth < 310
                ? 2
                : 4;
            return Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                for (final (label, icon, action) in actions)
                  SizedBox(
                    width: (constraints.maxWidth - 6 * (columns - 1)) / columns,
                    child: Card(
                      clipBehavior: Clip.antiAlias,
                      child: InkWell(
                        onTap: action,
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                            vertical: 12,
                            horizontal: 4,
                          ),
                          child: Column(
                            children: [
                              Icon(icon, color: water, size: 28),
                              const SizedBox(height: 5),
                              Text(
                                label,
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            );
          },
        ),
        SectionCard(
          title: 'Situation globale',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${overview.count} barrages suivis · Relevé : ${day(overview.latestDate)}',
              ),
              const SizedBox(height: 10),
              MetricPair(
                first: MetricTile(
                  icon: Icons.water_drop_outlined,
                  label: 'Réserve totale',
                  value: number(overview.storage, 'Mm³'),
                ),
                second: MetricTile(
                  icon: Icons.waves,
                  label: 'Remplissage pondéré',
                  value: number(overview.filling, '%'),
                ),
              ),
              if (overview.storage == null)
                Text(aggregateReason(overview.storageStatus)),
              if (overview.filling == null)
                Text(aggregateReason(overview.fillingStatus)),
            ],
          ),
        ),
        const SizedBox(height: 6),
        Notice(
          'Dernière synchronisation : ${instant(syncedAt)}',
          warning: true,
          action: TextButton(
            onPressed: onSources,
            child: const Text('Sources et dates'),
          ),
        ),
        Row(
          children: [
            Expanded(
              child: Text(
                'Mes barrages favoris',
                style: Theme.of(context).textTheme.titleLarge
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
            ),
            TextButton(onPressed: onFavorites, child: const Text('Voir tout')),
          ],
        ),
        if (favorites.isEmpty)
          const Text(
            'Touchez une étoile dans la liste pour enregistrer un barrage.',
          ),
        for (final item in favorites.take(3))
          ReservoirTile(
            item: item,
            favorite: true,
            busy: controller.savingFavorite,
            onOpen: () => onOpen(item),
            onFavorite: () => controller.toggleFavorite(item.reservoir.id),
          ),
      ],
    );
  }
}
