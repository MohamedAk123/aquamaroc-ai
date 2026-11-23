import 'package:material_ui/material_ui.dart';

import '../domain/models.dart';
import 'reservoir_art.dart';

const navy = Color(0xff123a68);
const water = Color(0xff007c9f);

class MetricTile extends StatelessWidget {
  final IconData icon;
  final String label, value;
  const MetricTile({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
  });
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(
      color: const Color(0xffeaf6fd),
      borderRadius: BorderRadius.circular(13),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: water, size: 22),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 12)),
        Text(
          value,
          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
        ),
      ],
    ),
  );
}

class MetricPair extends StatelessWidget {
  final MetricTile first, second;
  const MetricPair({super.key, required this.first, required this.second});
  @override
  Widget build(BuildContext context) =>
      MediaQuery.textScalerOf(context).scale(14) > 20
      ? Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [first, const SizedBox(height: 8), second],
        )
      : Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: first),
            const SizedBox(width: 8),
            Expanded(child: second),
          ],
        );
}

class SectionCard extends StatelessWidget {
  final String title;
  final Widget child;
  final IconData? icon;
  const SectionCard({
    super.key,
    required this.title,
    required this.child,
    this.icon,
  });
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (icon != null) ...[
                Icon(icon, color: water),
                const SizedBox(width: 10),
              ],
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
    ),
  );
}

class Notice extends StatelessWidget {
  final String text;
  final bool warning;
  final Widget? action;
  const Notice(this.text, {super.key, this.warning = false, this.action});
  @override
  Widget build(BuildContext context) => Semantics(
    liveRegion: true,
    child: Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: warning ? const Color(0xfffff3dc) : const Color(0xffe9f5fc),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            text,
            style: TextStyle(color: warning ? const Color(0xff714600) : navy),
          ),
          ?action,
        ],
      ),
    ),
  );
}

class KindBadge extends StatelessWidget {
  final DataKind kind;
  const KindBadge(this.kind, {super.key});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    decoration: BoxDecoration(
      color: kind == DataKind.official
          ? const Color(0xffe2f6ef)
          : const Color(0xffffefce),
      borderRadius: BorderRadius.circular(6),
    ),
    child: Text(
      kind == DataKind.unverified ? 'UNVERIFIED · À vérifier' : kind.label,
      style: TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w700,
        color: kind == DataKind.official
            ? const Color(0xff136344)
            : const Color(0xff714600),
      ),
    ),
  );
}

class SyncNotice extends StatelessWidget {
  final Cached<dynamic> data;
  const SyncNotice(this.data, {super.key});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Notice(
      '${data.offline ? 'Cache local · actualisation indisponible' : 'Données synchronisées'}\nDernière synchronisation : ${instant(data.syncedAt)}'
      '${data.persisted ? '' : '\nStockage local indisponible : ces données ne seront pas conservées.'}',
      warning: data.offline || !data.persisted,
    ),
  );
}

class FavoriteButton extends StatelessWidget {
  final bool selected, busy, onDark;
  final VoidCallback onPressed;
  const FavoriteButton({
    super.key,
    required this.selected,
    required this.onPressed,
    this.busy = false,
    this.onDark = false,
  });
  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: selected ? 'Retirer des favoris' : 'Ajouter aux favoris',
    isSelected: selected,
    onPressed: busy ? null : onPressed,
    icon: Icon(
      selected ? Icons.star : Icons.star_border,
      color: onDark
          ? (selected ? const Color(0xffffcf54) : Colors.white)
          : (selected ? const Color(0xff916000) : navy),
    ),
  );
}

class ReservoirTile extends StatelessWidget {
  final Snapshot item;
  final bool favorite, busy;
  final VoidCallback onOpen, onFavorite;
  const ReservoirTile({
    super.key,
    required this.item,
    required this.favorite,
    required this.onOpen,
    required this.onFavorite,
    this.busy = false,
  });
  @override
  Widget build(BuildContext context) {
    final latest = item.latest;
    final filling = latest?.filling;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(
              width: 68,
              height: 82,
              child: ClipRRect(
                borderRadius: BorderRadius.all(Radius.circular(12)),
                child: ReservoirArt(),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Semantics(
                button: true,
                child: InkWell(
                  onTap: onOpen,
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.reservoir.name,
                          style: const TextStyle(
                            fontWeight: FontWeight.w800,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          item.basinName,
                          style: const TextStyle(color: navy, fontSize: 12),
                        ),
                        const SizedBox(height: 7),
                        Wrap(
                          spacing: 12,
                          runSpacing: 4,
                          children: [
                            Text(
                              number(filling, '%'),
                              style: const TextStyle(
                                fontWeight: FontWeight.w800,
                                color: water,
                                fontSize: 17,
                              ),
                            ),
                            Text(number(latest?.storage, 'Mm³')),
                          ],
                        ),
                        if (filling != null) ...[
                          const SizedBox(height: 5),
                          ExcludeSemantics(
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(8),
                              child: LinearProgressIndicator(
                                value: filling / 100,
                                minHeight: 7,
                                backgroundColor: const Color(0xffcde4f4),
                                color: water,
                              ),
                            ),
                          ),
                        ],
                        const SizedBox(height: 6),
                        Text(
                          '${day(item.latestDate)}${latest == null ? ' · Sources multiples' : ' · ${latest.kind.label}'}',
                          style: const TextStyle(fontSize: 11, color: navy),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            FavoriteButton(
              selected: favorite,
              onPressed: onFavorite,
              busy: busy,
            ),
          ],
        ),
      ),
    );
  }
}
