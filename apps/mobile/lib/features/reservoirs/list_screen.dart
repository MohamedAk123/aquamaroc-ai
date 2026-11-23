import 'package:material_ui/material_ui.dart';

import '../../domain/models.dart';
import '../../presentation/app_controller.dart';
import '../../presentation/widgets.dart';

class ReservoirListScreen extends StatefulWidget {
  final Catalog catalog;
  final AppController controller;
  final ValueChanged<Snapshot> onOpen;
  final bool favoritesOnly;
  const ReservoirListScreen({
    super.key,
    required this.catalog,
    required this.controller,
    required this.onOpen,
    this.favoritesOnly = false,
  });
  @override
  State<ReservoirListScreen> createState() => _ReservoirListScreenState();
}

class _ReservoirListScreenState extends State<ReservoirListScreen> {
  final search = TextEditingController();
  String basin = '';
  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final items = widget.catalog.overview.reservoirs
        .where(
          (item) =>
              (!widget.favoritesOnly ||
                  widget.controller.favorites.contains(item.reservoir.id)) &&
              (basin.isEmpty || item.reservoir.basinId == basin) &&
              item.reservoir.name.toLowerCase().contains(
                search.text.trim().toLowerCase(),
              ),
        )
        .toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: search,
          onChanged: (_) => setState(() {}),
          maxLength: 200,
          decoration: InputDecoration(
            labelText: 'Rechercher un barrage',
            prefixIcon: const Icon(Icons.search),
            counterText: '',
            suffixIcon: IconButton(
              tooltip: 'Effacer la recherche',
              onPressed: () => setState(search.clear),
              icon: const Icon(Icons.close),
            ),
          ),
        ),
        const SizedBox(height: 12),
        if (widget.catalog.basins.length <= 4)
          Wrap(
            spacing: 7,
            runSpacing: 4,
            children: [
              ChoiceChip(
                label: const Text('Tous les bassins'),
                selected: basin.isEmpty,
                onSelected: (_) => setState(() => basin = ''),
              ),
              if (basin.isNotEmpty &&
                  !widget.catalog.basins.any((item) => item.id == basin))
                const Chip(label: Text('Bassin indisponible')),
              for (final item in widget.catalog.basins)
                ChoiceChip(
                  label: Text(item.name),
                  selected: basin == item.id,
                  onSelected: (_) => setState(() => basin = item.id),
                ),
            ],
          )
        else
          DropdownButtonFormField<String>(
            key: ValueKey(basin),
            initialValue: basin,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Bassin'),
            items: [
              const DropdownMenuItem(
                value: '',
                child: Text('Tous les bassins'),
              ),
              if (basin.isNotEmpty &&
                  !widget.catalog.basins.any((item) => item.id == basin))
                DropdownMenuItem(
                  value: basin,
                  child: const Text('Bassin indisponible'),
                ),
              for (final item in widget.catalog.basins)
                DropdownMenuItem(value: item.id, child: Text(item.name)),
            ],
            onChanged: (value) => setState(() => basin = value ?? ''),
          ),
        const SizedBox(height: 12),
        Text('${items.length} résultat(s) · sélection locale'),
        if (items.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Notice(
              widget.favoritesOnly
                  ? 'Aucun favori dans cette sélection. Les favoris sont propres au serveur et au mode actifs.'
                  : 'Aucun barrage dans cette sélection.',
            ),
          ),
        for (final item in items)
          ReservoirTile(
            item: item,
            favorite: widget.controller.favorites.contains(item.reservoir.id),
            busy: widget.controller.savingFavorite,
            onOpen: () => widget.onOpen(item),
            onFavorite: () =>
                widget.controller.toggleFavorite(item.reservoir.id),
          ),
      ],
    );
  }
}
