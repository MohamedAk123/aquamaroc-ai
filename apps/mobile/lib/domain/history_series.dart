import 'models.dart';

class HistoryPoint {
  final DateTime date;
  final double value;
  const HistoryPoint(this.date, this.value);
}

class HistorySeries {
  final String sourceId;
  final DataKind kind;
  final List<List<HistoryPoint>> segments;
  const HistorySeries(this.sourceId, this.kind, this.segments);
}

// Never connect sources/categories; missing values break lines instead of becoming zero.
List<HistorySeries> buildSeries(
  List<Measurement> values, {
  required bool filling,
}) {
  final groups = <(String, DataKind), List<Measurement>>{};
  for (final item in values) {
    groups.putIfAbsent((item.sourceId, item.kind), () => []).add(item);
  }
  return groups.entries.map((entry) {
    final ordered = [...entry.value]
      ..sort((a, b) => a.observedAt.compareTo(b.observedAt));
    final segments = <List<HistoryPoint>>[];
    var current = <HistoryPoint>[];
    for (final item in ordered) {
      final value = filling ? item.filling : item.storage;
      if (value == null) {
        if (current.isNotEmpty) segments.add(current);
        current = [];
      } else {
        current.add(HistoryPoint(item.observedAt, value));
      }
    }
    if (current.isNotEmpty) segments.add(current);
    return HistorySeries(entry.key.$1, entry.key.$2, segments);
  }).toList();
}
