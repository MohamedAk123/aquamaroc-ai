typedef Json = Map<String, dynamic>;

enum AppMode { demo, official }

enum DataKind {
  demo,
  official,
  unverified;

  String get label => name.toUpperCase();
  static DataKind parse(String value) => switch (value) {
    'DEMO' => demo,
    'OFFICIAL' => official,
    'UNVERIFIED' => unverified,
    _ => throw const FormatException('Provenance inconnue'),
  };
}

AppMode parseMode(Object? value) => switch (value) {
  'demo' => AppMode.demo,
  'official' => AppMode.official,
  _ => throw const FormatException('Mode inconnu'),
};

double? decimal(Object? value) {
  if (value == null) return null;
  final number = double.parse(value.toString());
  if (!number.isFinite) throw const FormatException('Nombre non fini');
  return number;
}

DateTime? date(Object? value) =>
    value == null ? null : DateTime.parse(value as String);

class Basin {
  final String id, name;
  Basin.fromJson(Json json)
    : id = json['id'] as String,
      name = json['name'] as String;
}

class Reservoir {
  final String id, basinId, name;
  final double? capacity, latitude, longitude;
  final String? capacitySource, coordinatesSource;
  Reservoir.fromJson(Json json)
    : id = json['id'] as String,
      basinId = json['basin_id'] as String,
      name = json['name'] as String,
      capacity = decimal(json['capacity_mm3']),
      latitude = decimal(json['latitude']),
      longitude = decimal(json['longitude']),
      capacitySource = json['capacity_source'] as String?,
      coordinatesSource = json['coordinates_source'] as String?;
  bool get hasVerifiedCoordinates =>
      latitude != null &&
      longitude != null &&
      latitude! >= -90 &&
      latitude! <= 90 &&
      longitude! >= -180 &&
      longitude! <= 180 &&
      (coordinatesSource?.trim().isNotEmpty ?? false);
  bool get hasVerifiedCapacity =>
      capacity != null &&
      capacity! > 0 &&
      (capacitySource?.trim().isNotEmpty ?? false);
}

class Measurement {
  final String id, reservoirId, sourceId, ingestionRunId, quality;
  final DateTime observedAt, ingestedAt;
  final DateTime? publishedAt;
  final double? storage, filling;
  final DataKind kind;
  Measurement.fromJson(Json json)
    : id = json['id'] as String,
      reservoirId = json['reservoir_id'] as String,
      sourceId = json['source_id'] as String,
      ingestionRunId = json['ingestion_run_id'] as String,
      quality = json['quality_status'] as String,
      observedAt = DateTime.parse(json['observation_date'] as String),
      ingestedAt = DateTime.parse(json['ingested_at'] as String),
      publishedAt = date(json['published_at']),
      storage = decimal(json['storage_mm3']),
      filling = decimal(json['filling_rate_pct']),
      kind = DataKind.parse(json['data_kind'] as String) {
    if ((storage != null && storage! < 0) ||
        (filling != null && (filling! < 0 || filling! > 100))) {
      throw const FormatException('Mesure hors bornes');
    }
  }
  bool allowedIn(AppMode mode) =>
      mode == AppMode.demo ? kind == DataKind.demo : kind != DataKind.demo;
}

class Source {
  final String id, title, status;
  final String? producer, url, license;
  final DateTime? observedAt, publishedAt, ingestedAt;
  Source.fromJson(Json json)
    : id = json['source_id'] as String,
      title = json['title'] as String,
      status = json['verification_status'] as String,
      producer = json['producer'] as String?,
      url = json['dataset_url'] as String?,
      license = json['license'] as String?,
      observedAt = date(json['latest_observation_date']),
      publishedAt = date(json['latest_published_at']),
      ingestedAt = date(json['latest_ingested_at']);
}

class Snapshot {
  final Reservoir reservoir;
  final String basinName;
  final DateTime latestDate;
  final Measurement? latest;
  final int sourceCount;
  Snapshot.fromJson(Json json)
    : reservoir = Reservoir.fromJson(json['reservoir'] as Json),
      basinName = json['basin_name'] as String,
      latestDate = DateTime.parse(json['latest_date'] as String),
      latest = json['latest'] == null
          ? null
          : Measurement.fromJson(json['latest'] as Json),
      sourceCount = json['source_count'] as int;
}

class Overview {
  final AppMode mode;
  final List<Snapshot> reservoirs;
  final DateTime? latestDate;
  final double? storage, filling;
  final String storageStatus, fillingStatus;
  final int count, comparableCount;
  Overview.fromJson(Json json)
    : mode = parseMode(json['mode']),
      reservoirs = (json['reservoirs'] as List<dynamic>)
          .map((e) => Snapshot.fromJson(e as Json))
          .toList(),
      latestDate = date(json['latest_observation_date']),
      storage = decimal(json['storage_mm3']),
      filling = decimal(json['weighted_filling_rate_pct']),
      storageStatus = json['storage_status'] as String,
      fillingStatus = json['filling_status'] as String,
      count = json['reservoir_count'] as int,
      comparableCount = json['comparable_count'] as int {
    for (final item in reservoirs) {
      if (item.latest != null &&
          (!item.latest!.allowedIn(mode) ||
              item.latest!.reservoirId != item.reservoir.id)) {
        throw const FormatException('Provenance de synthèse incohérente');
      }
    }
  }
}

class Catalog {
  final Overview overview;
  final List<Basin> basins;
  final List<Source> sources;
  Catalog.fromJson(Json json)
    : overview = Overview.fromJson(json['overview'] as Json),
      basins = (json['basins'] as List<dynamic>)
          .map((e) => Basin.fromJson(e as Json))
          .toList(),
      sources = (json['sources'] as List<dynamic>)
          .map((e) => Source.fromJson(e as Json))
          .toList();
  Source? source(String id) {
    for (final source in sources) {
      if (source.id == id) return source;
    }
    return null;
  }
}

class Cached<T> {
  final T value;
  final DateTime syncedAt;
  final bool offline;
  final bool persisted;
  const Cached(
    this.value,
    this.syncedAt, {
    this.offline = false,
    this.persisted = true,
  });
}

String number(double? value, [String unit = '']) => value == null
    ? 'Non disponible'
    : '${value.toStringAsFixed(1).replaceAll('.', ',')}${unit.isEmpty ? '' : ' $unit'}';
String day(DateTime? value) => value == null
    ? 'Non renseignée'
    : '${value.day.toString().padLeft(2, '0')}/${value.month.toString().padLeft(2, '0')}/${value.year}';
String instant(DateTime? value) => value == null
    ? 'Non renseignée'
    : '${day(value.toLocal())} ${value.toLocal().hour.toString().padLeft(2, '0')}:${value.toLocal().minute.toString().padLeft(2, '0')}';

String aggregateReason(String status) => switch (status) {
  'unverified_capacities' => 'Capacités non vérifiées',
  'different_dates' => 'Dates non comparables',
  'multiple_sources' => 'Plusieurs sources à comparer',
  'missing_storage' => 'Réserves incomplètes',
  'no_data' => 'Aucun relevé disponible',
  'available' => 'Relevés comparables',
  _ => 'Calcul indisponible ($status)',
};
