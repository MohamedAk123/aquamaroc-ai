import 'dart:math' as math;

import 'package:material_ui/material_ui.dart';

import '../../domain/history_series.dart';
import '../../domain/models.dart';
import '../../presentation/widgets.dart';

class HistoryChart extends StatelessWidget {
  final List<Measurement> values;
  final Catalog catalog;
  final bool filling;
  const HistoryChart({
    super.key,
    required this.values,
    required this.catalog,
    required this.filling,
  });
  static const colors = [
    Color(0xff087fb4),
    Color(0xffa94300),
    Color(0xff703bac),
    Color(0xff08745a),
  ];
  @override
  Widget build(BuildContext context) {
    final series = buildSeries(values, filling: filling);
    final points = series.expand((e) => e.segments).expand((e) => e).toList();
    if (points.isEmpty) {
      return const Notice('Aucune valeur disponible pour ce graphique.');
    }
    final first = points
        .map((e) => e.date)
        .reduce((a, b) => a.isBefore(b) ? a : b);
    final last = points
        .map((e) => e.date)
        .reduce((a, b) => a.isAfter(b) ? a : b);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '${filling ? 'Remplissage (%)' : 'Réserves (Mm³)'} · ${day(first)} – ${day(last)}',
        ),
        Semantics(
          image: true,
          label:
              'Historique ${filling ? 'du remplissage' : 'des réserves'}. ${points.length} valeurs. Alternative détaillée dans les relevés ci-dessous.',
          child: ExcludeSemantics(
            child: SizedBox(
              height: 210,
              width: double.infinity,
              child: CustomPaint(painter: _HistoryPainter(series, filling)),
            ),
          ),
        ),
        for (var i = 0; i < series.length; i++)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 14,
                  height: 14,
                  margin: const EdgeInsets.only(top: 3, right: 8),
                  color: colors[i % colors.length],
                ),
                Expanded(
                  child: Text(
                    '${i + 1}. ${catalog.source(series[i].sourceId)?.title ?? 'Source ${series[i].sourceId}'} · ${series[i].kind.label}',
                  ),
                ),
              ],
            ),
          ),
        const SizedBox(height: 8),
        const Text(
          'Les intervalles suivent les dates réelles. Aucun relevé manquant n’est remplacé par zéro.',
          style: TextStyle(fontSize: 12),
        ),
      ],
    );
  }
}

class _HistoryPainter extends CustomPainter {
  final List<HistorySeries> series;
  final bool filling;
  _HistoryPainter(this.series, this.filling);
  void label(Canvas canvas, String text, Offset at) {
    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: const TextStyle(color: navy, fontSize: 11),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    painter.paint(canvas, at);
  }

  @override
  void paint(Canvas canvas, Size size) {
    final points = series.expand((e) => e.segments).expand((e) => e).toList();
    if (points.isEmpty) return;
    final dates = points.map((e) => e.date.millisecondsSinceEpoch.toDouble());
    final minX = dates.reduce(math.min), maxX = dates.reduce(math.max);
    var minY = filling ? 0.0 : points.map((e) => e.value).reduce(math.min);
    var maxY = filling ? 100.0 : points.map((e) => e.value).reduce(math.max);
    if (maxY == minY) {
      minY = math.max(0, minY - 1);
      maxY += 1;
    }
    final plot = Rect.fromLTRB(52, 16, size.width - 12, size.height - 28);
    Offset position(HistoryPoint p) => Offset(
      maxX == minX
          ? plot.center.dx
          : plot.left +
                (p.date.millisecondsSinceEpoch - minX) /
                    (maxX - minX) *
                    plot.width,
      plot.bottom - (p.value - minY) / (maxY - minY) * plot.height,
    );
    for (var i = 0; i <= 4; i++) {
      final y = plot.bottom - i / 4 * plot.height;
      canvas.drawLine(
        Offset(plot.left, y),
        Offset(plot.right, y),
        Paint()..color = const Color(0xffdce8f4),
      );
      label(canvas, number(minY + (maxY - minY) * i / 4), Offset(0, y - 7));
    }
    label(
      canvas,
      day(DateTime.fromMillisecondsSinceEpoch(minX.toInt())).substring(0, 5),
      Offset(plot.left, plot.bottom + 8),
    );
    label(
      canvas,
      day(DateTime.fromMillisecondsSinceEpoch(maxX.toInt())).substring(0, 5),
      Offset(plot.right - 34, plot.bottom + 8),
    );
    for (var i = 0; i < series.length; i++) {
      final color = HistoryChart.colors[i % HistoryChart.colors.length];
      for (final segment in series[i].segments) {
        final path = Path();
        if (series.length == 1 && segment.length > 1) {
          final first = position(segment.first);
          final last = position(segment.last);
          final area = Path()..moveTo(first.dx, plot.bottom);
          for (final point in segment) {
            final at = position(point);
            area.lineTo(at.dx, at.dy);
          }
          area.lineTo(last.dx, plot.bottom);
          area.close();
          canvas.drawPath(
            area,
            Paint()
              ..shader = LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  color.withValues(alpha: .35),
                  color.withValues(alpha: .05),
                ],
              ).createShader(plot),
          );
        }
        for (var j = 0; j < segment.length; j++) {
          final at = position(segment[j]);
          if (j == 0) {
            path.moveTo(at.dx, at.dy);
          } else {
            path.lineTo(at.dx, at.dy);
          }
          canvas.drawCircle(at, 3.5, Paint()..color = color);
          // A number makes overlapping series identifiable without color alone.
          label(canvas, '${i + 1}', at + const Offset(4, -14));
        }
        canvas.drawPath(
          path,
          Paint()
            ..color = color
            ..style = PaintingStyle.stroke
            ..strokeWidth = 2.5,
        );
      }
    }
  }

  @override
  bool shouldRepaint(_HistoryPainter oldDelegate) =>
      oldDelegate.series != series || oldDelegate.filling != filling;
}
