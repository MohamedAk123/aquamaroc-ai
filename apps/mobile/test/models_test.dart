import 'package:aquamaroc_mobile/domain/models.dart';
import 'package:aquamaroc_mobile/domain/history_series.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support.dart';

void main() {
  test('Decimal strings, nulls and three timestamps retain meaning', () {
    final m = Measurement.fromJson(measurement(storage: null));
    expect(m.storage, isNull);
    expect(m.filling, 25.6);
    expect(m.publishedAt, isNull);
    expect(instant(m.publishedAt), 'Non renseignée');
    expect(m.observedAt, DateTime(2026, 1, 1));
    expect(m.ingestedAt, DateTime.utc(2026, 1, 3, 9));
    expect(number(null, 'Mm³'), 'Non disponible');
  });
  test(
    'Invalid provenance and non finite/out of range numbers are rejected',
    () {
      expect(
        () => Measurement.fromJson(measurement(kind: 'UNKNOWN')),
        throwsFormatException,
      );
      expect(
        () => Measurement.fromJson(measurement(storage: 'NaN')),
        throwsFormatException,
      );
      expect(
        () => Measurement.fromJson(measurement(storage: '-1')),
        throwsFormatException,
      );
      expect(
        () => Measurement.fromJson(measurement(filling: '101')),
        throwsFormatException,
      );
      expect(() => parseMode('unknown'), throwsFormatException);
    },
  );
  test('Official overview cannot contain DEMO observations', () {
    expect(
      () => Overview.fromJson(overview()..['mode'] = 'official'),
      throwsFormatException,
    );
  });
  test('Coordinates require bounds and a nonempty source', () {
    expect(Reservoir.fromJson(reservoir()).hasVerifiedCoordinates, isFalse);
    final raw = reservoir()
      ..['latitude'] = '31'
      ..['longitude'] = '-8';
    expect(Reservoir.fromJson(raw).hasVerifiedCoordinates, isFalse);
    raw['coordinates_source'] = 'Synthetic coordinate validation fixture';
    expect(Reservoir.fromJson(raw).hasVerifiedCoordinates, isTrue);
    raw['latitude'] = '100';
    expect(Reservoir.fromJson(raw).hasVerifiedCoordinates, isFalse);
  });
  test(
    'Chart sorts chronologically, breaks nulls, keeps source/category separate',
    () {
      final series = buildSeries([
        Measurement.fromJson(
          measurement(id: '3', observed: '2026-01-10', storage: '3'),
        ),
        Measurement.fromJson(
          measurement(id: '2', observed: '2026-01-04', storage: null),
        ),
        Measurement.fromJson(measurement()),
        Measurement.fromJson(measurement(id: '4', source: 's2')),
        Measurement.fromJson(measurement(id: '5', kind: 'UNVERIFIED')),
      ], filling: false);
      expect(series.length, 3);
      expect(series.first.segments.length, 2);
      expect(series.first.segments.first.single.date, DateTime(2026, 1, 1));
      expect(series.first.segments.last.single.date, DateTime(2026, 1, 10));
      expect(series.last.kind, DataKind.unverified);
    },
  );
}
