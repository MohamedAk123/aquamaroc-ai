import 'package:material_ui/material_ui.dart';

import '../../data/api_client.dart';
import '../../domain/models.dart';
import '../../presentation/app_controller.dart';
import '../../presentation/widgets.dart';
import '../../presentation/reservoir_art.dart';
import 'history_chart.dart';

class DetailScreen extends StatefulWidget {
  final Snapshot item;
  final AppController controller;
  final Catalog catalog;
  final DateTime catalogSyncedAt;
  const DetailScreen({
    super.key,
    required this.item,
    required this.controller,
    required this.catalog,
    required this.catalogSyncedAt,
  });
  @override
  State<DetailScreen> createState() => _DetailScreenState();
}

class _DetailScreenState extends State<DetailScreen> {
  Cached<List<Measurement>>? data;
  String? error;
  bool loading = true, filling = true;
  int section = 0;
  String source = '', kind = '';
  DateTimeRange? range;
  int shown = 20;
  bool refreshing = false;
  @override
  void initState() {
    super.initState();
    initialize();
  }

  Future<void> initialize() async {
    final cached = await widget.controller.repository.cachedHistory(
      widget.item.reservoir.id,
    );
    if (!mounted) return;
    setState(() => data = cached);
    await refresh();
  }

  Future<void> refresh() async {
    if (refreshing || !mounted) return;
    refreshing = true;
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final result = await widget.controller.repository.history(
        widget.item.reservoir.id,
      );
      if (mounted) setState(() => data = result);
    } catch (e) {
      if (mounted) {
        setState(() {
          error = e is ApiException
              ? e.message
              : 'Historique reçu incompatible.';
          if ((e is ApiException && e.incompatible) ||
              e is FormatException ||
              e is TypeError) {
            data = null;
          } else if (data != null) {
            data = Cached(data!.value, data!.syncedAt, offline: true);
          }
        });
      }
    } finally {
      refreshing = false;
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> pickRange() async {
    if (data == null || data!.value.isEmpty) return;
    final ordered = data!.value;
    final selected = await showDateRangePicker(
      context: context,
      firstDate: ordered.first.observedAt,
      lastDate: ordered.last.observedAt,
      initialDateRange:
          range != null &&
              !range!.start.isBefore(ordered.first.observedAt) &&
              !range!.end.isAfter(ordered.last.observedAt)
          ? range
          : null,
      helpText: 'Filtrer les relevés disponibles',
      locale: const Locale('fr'),
    );
    if (selected != null && mounted) {
      setState(() {
        range = selected;
        shown = 20;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    final values = (data?.value ?? <Measurement>[])
        .where(
          (m) =>
              (source.isEmpty || m.sourceId == source) &&
              (kind.isEmpty || m.kind.label == kind) &&
              (range == null ||
                  (!m.observedAt.isBefore(range!.start) &&
                      !m.observedAt.isAfter(range!.end))),
        )
        .toList();
    final sourceIds = (data?.value ?? <Measurement>[])
        .map((m) => m.sourceId)
        .toSet();
    final kinds = (data?.value ?? <Measurement>[]).map((m) => m.kind).toSet();
    final recent = values.reversed.take(shown).toList();
    return ListenableBuilder(
      listenable: widget.controller,
      builder: (context, _) => Scaffold(
        appBar: AppBar(
          title: const Text('Détail barrage'),
          actions: [
            FavoriteButton(
              selected: widget.controller.favorites.contains(item.reservoir.id),
              busy: widget.controller.savingFavorite,
              onPressed: () =>
                  widget.controller.toggleFavorite(item.reservoir.id),
            ),
          ],
        ),
        body: SafeArea(
          child: RefreshIndicator(
            onRefresh: refresh,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const ReservoirBanner(),
                const SizedBox(height: 8),
                Notice(
                  widget.catalog.overview.mode == AppMode.demo
                      ? 'DEMO · Données synthétiques'
                      : 'Mode officiel · Provenance indiquée par relevé',
                  warning: widget.catalog.overview.mode == AppMode.demo,
                ),
                const SizedBox(height: 16),
                Text(
                  item.reservoir.name,
                  style: Theme.of(context).textTheme.headlineSmall
                      ?.copyWith(fontWeight: FontWeight.bold, color: navy),
                ),
                Text(item.basinName),
                Text(
                  'Synthèse synchronisée : ${instant(widget.catalogSyncedAt)}',
                ),
                if (widget.controller.localError != null)
                  Notice(widget.controller.localError!, warning: true),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  children: [
                    ChoiceChip(
                      label: const Text('Aperçu'),
                      selected: section == 0,
                      onSelected: (_) => setState(() => section = 0),
                    ),
                    ChoiceChip(
                      label: const Text('Historique'),
                      selected: section == 1,
                      onSelected: (_) => setState(() => section = 1),
                    ),
                    ChoiceChip(
                      label: const Text('Prévisions IA'),
                      selected: section == 2,
                      onSelected: (_) => setState(() => section = 2),
                    ),
                  ],
                ),
                if (section == 2)
                  const Notice('Aucune prévision validée disponible.'),
                if (section == 0)
                  MetricPair(
                    first: MetricTile(
                      icon: Icons.water_drop_outlined,
                      label: 'Réserve actuelle',
                      value: number(item.latest?.storage, 'Mm³'),
                    ),
                    second: MetricTile(
                      icon: Icons.waves,
                      label: 'Taux de remplissage',
                      value: number(item.latest?.filling, '%'),
                    ),
                  ),
                if (section == 0 && data != null)
                  SectionCard(
                    title: 'Évolution du taux de remplissage',
                    child: HistoryChart(
                      values: data!.value,
                      catalog: widget.catalog,
                      filling: true,
                    ),
                  ),
                if (section == 0)
                  SectionCard(
                    title: 'Dernier relevé',
                    icon: Icons.water_drop_outlined,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Relevé : ${day(item.latestDate)}'),
                        if (item.latest != null) ...[
                          const SizedBox(height: 8),
                          KindBadge(item.latest!.kind),
                          Text(
                            'Réserve : ${number(item.latest!.storage, 'Mm³')}',
                          ),
                          Text(
                            'Remplissage : ${number(item.latest!.filling, '%')}',
                          ),
                          Text(
                            'Source : ${widget.catalog.source(item.latest!.sourceId)?.title ?? item.latest!.sourceId}',
                          ),
                        ] else
                          Text(
                            '${item.sourceCount} sources : dernières valeurs à consulter séparément.',
                          ),
                        Text(
                          'Capacité : ${item.reservoir.hasVerifiedCapacity ? number(item.reservoir.capacity, 'Mm³') : 'Non vérifiée'}',
                        ),
                        if (item.reservoir.hasVerifiedCapacity)
                          Text(
                            'Source de capacité : ${item.reservoir.capacitySource}',
                          ),
                      ],
                    ),
                  ),
                if (data != null) SyncNotice(data!),
                if (error != null) Notice(error!, warning: true),
                if (loading)
                  const LinearProgressIndicator(
                    semanticsLabel: 'Chargement de l’historique',
                  ),
                Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton.icon(
                    onPressed: loading ? null : refresh,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Actualiser l’historique'),
                  ),
                ),
                if (data != null && section == 1) ...[
                  SectionCard(
                    title: 'Historique',
                    icon: Icons.show_chart,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        DropdownButtonFormField<String>(
                          key: ValueKey('source-$source-${sourceIds.length}'),
                          initialValue: source,
                          isExpanded: true,
                          decoration: const InputDecoration(
                            labelText: 'Source',
                          ),
                          items: [
                            const DropdownMenuItem(
                              value: '',
                              child: Text(
                                'Toutes les sources (séries séparées)',
                              ),
                            ),
                            if (source.isNotEmpty &&
                                !sourceIds.contains(source))
                              DropdownMenuItem(
                                value: source,
                                child: const Text('Source indisponible'),
                              ),
                            for (final id in sourceIds)
                              DropdownMenuItem(
                                value: id,
                                child: Text(
                                  widget.catalog.source(id)?.title ?? id,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                          ],
                          onChanged: (value) => setState(() {
                            source = value ?? '';
                            shown = 20;
                          }),
                        ),
                        const SizedBox(height: 12),
                        DropdownButtonFormField<String>(
                          key: ValueKey('kind-$kind-${kinds.length}'),
                          initialValue: kind,
                          isExpanded: true,
                          decoration: const InputDecoration(
                            labelText: 'Provenance',
                          ),
                          items: [
                            const DropdownMenuItem(
                              value: '',
                              child: Text('Toutes (séries séparées)'),
                            ),
                            if (kind.isNotEmpty &&
                                !kinds.any((e) => e.label == kind))
                              DropdownMenuItem(
                                value: kind,
                                child: Text('$kind (indisponible)'),
                              ),
                            for (final item in kinds)
                              DropdownMenuItem(
                                value: item.label,
                                child: Text(item.label),
                              ),
                          ],
                          onChanged: (value) => setState(() {
                            kind = value ?? '';
                            shown = 20;
                          }),
                        ),
                        Wrap(
                          spacing: 8,
                          children: [
                            TextButton.icon(
                              onPressed: pickRange,
                              icon: const Icon(Icons.date_range),
                              label: Text(
                                range == null
                                    ? 'Choisir les dates'
                                    : '${day(range!.start)} – ${day(range!.end)}',
                              ),
                            ),
                            if (range != null)
                              TextButton(
                                onPressed: () => setState(() {
                                  range = null;
                                  shown = 20;
                                }),
                                child: const Text('Toutes les dates'),
                              ),
                          ],
                        ),
                        Wrap(
                          spacing: 8,
                          children: [
                            ChoiceChip(
                              label: const Text('Réserves (Mm³)'),
                              selected: !filling,
                              onSelected: (_) =>
                                  setState(() => filling = false),
                            ),
                            ChoiceChip(
                              label: const Text('Remplissage (%)'),
                              selected: filling,
                              onSelected: (_) => setState(() => filling = true),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        HistoryChart(
                          values: values,
                          catalog: widget.catalog,
                          filling: filling,
                        ),
                      ],
                    ),
                  ),
                  SectionCard(
                    title: 'Relevés et provenance (${values.length})',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        if (values.isEmpty)
                          const Text('Aucun relevé dans cette sélection.'),
                        for (final m in recent)
                          ExpansionTile(
                            tilePadding: EdgeInsets.zero,
                            title: Text(
                              '${day(m.observedAt)} · ${number(m.storage, 'Mm³')}',
                            ),
                            subtitle: Text(
                              '${number(m.filling, '%')} · ${m.kind.label}\n${widget.catalog.source(m.sourceId)?.title ?? m.sourceId}',
                            ),
                            children: [
                              Padding(
                                padding: const EdgeInsets.symmetric(
                                  vertical: 8,
                                ),
                                child: SelectableText(
                                  'Qualité : ${m.quality}\nPublication : ${instant(m.publishedAt)}\nImport : ${instant(m.ingestedAt)}\n'
                                  'Source : ${m.sourceId}\nImport ID : ${m.ingestionRunId}\nMesure ID : ${m.id}',
                                ),
                              ),
                            ],
                          ),
                        if (shown < values.length)
                          TextButton(
                            onPressed: () => setState(() => shown += 20),
                            child: const Text(
                              'Afficher 20 relevés supplémentaires',
                            ),
                          ),
                      ],
                    ),
                  ),
                ],
                const SectionCard(
                  title: 'Comment lire cet historique ?',
                  child: Text(
                    'Les unités sont Mm³ pour les réserves et % pour le remplissage. '
                    'Chaque source et catégorie de provenance reste une série distincte. Le cache peut contenir des relevés anciens ; la synchronisation n’est pas la date de mesure. Aucune prévision validée disponible.',
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
