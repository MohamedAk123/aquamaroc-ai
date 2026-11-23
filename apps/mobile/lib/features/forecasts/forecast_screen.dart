import 'package:material_ui/material_ui.dart';

import '../../data/api_client.dart';
import '../../domain/models.dart';
import '../../presentation/widgets.dart';

class ForecastScreen extends StatefulWidget {
  final ApiClient api;
  const ForecastScreen({super.key, required this.api});

  @override
  State<ForecastScreen> createState() => _ForecastScreenState();
}

class _ForecastScreenState extends State<ForecastScreen> {
  late Future<_Forecast?> forecast = _load();

  Future<_Forecast?> _load() async {
    final json = await widget.api.get('/demo/forecast');
    if (json['status'] == 'unavailable') return null;
    return _Forecast.fromJson(json);
  }

  void _retry() {
    final next = _load();
    setState(() {
      forecast = next;
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Prévisions de remplissage')),
    body: SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Notice(
            'Prévisions officielles J+7 et J+30 indisponibles. L’historique publié est encore insuffisant pour les valider.',
          ),
          const SizedBox(height: 12),
          const Notice(
            'DEMO · Simulation à J+7 · Barrages fictifs',
            warning: true,
          ),
          const SizedBox(height: 12),
          FutureBuilder<_Forecast?>(
            future: forecast,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return Notice(
                  'La prévision DEMO est momentanément inaccessible.',
                  warning: true,
                  action: TextButton(
                    onPressed: _retry,
                    child: const Text('Réessayer'),
                  ),
                );
              }
              final result = snapshot.data;
              if (result == null) {
                return const Notice('Résultat DEMO indisponible.');
              }
              return _ForecastResult(result);
            },
          ),
        ],
      ),
    ),
  );
}

String _decimal(double value, String unit) =>
    '${value.toStringAsFixed(2).replaceAll('.', ',')} $unit';

class _ForecastResult extends StatelessWidget {
  final _Forecast result;
  const _ForecastResult(this.result);

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      SectionCard(
        title: 'Résultats pour le ${day(result.targetDate)}',
        child: Text('Prévision archivée, émise le ${day(result.issuedDate)}.'),
      ),
      for (final item in result.reservoirs)
        SectionCard(
          title: item.name,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              MetricPair(
                first: MetricTile(
                  icon: Icons.waves,
                  label: 'Taux prévu à J+7',
                  value: _decimal(item.predicted, '%'),
                ),
                second: MetricTile(
                  icon: Icons.water_drop_outlined,
                  label: 'Réserve prévue',
                  value: _decimal(item.storage, 'Mm³'),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Taux initial supposé : ${_decimal(item.initial, '%')}. '
                'Capacité fictive : ${number(item.capacity, 'Mm³')}.',
              ),
              if (!result.h2oSelected)
                Text('Candidat H2O : ${_decimal(item.candidate, '%')}.'),
            ],
          ),
        ),
      SectionCard(
        title: 'Météo utilisée',
        child: Text(
          'Prévisions Open-Meteo pour ${result.mountainPoint}.\n'
          'Pluie sur sept jours : ${number(result.rain, 'mm')}.\n'
          'Neige : ${number(result.snow, 'mm')} d’équivalent eau.\n'
          'Température moyenne : ${number(result.temperature, '°C')}.',
        ),
      ),
      SectionCard(
        title: 'Hypothèses du scénario',
        child: Text(
          'Stock de neige initial supposé : ${number(result.initialSnow, 'mm')} d’équivalent eau. '
          'Fonte simulée : ${number(result.melt, 'mm')} d’équivalent eau.',
        ),
      ),
      SectionCard(
        title: 'Évaluation sur données synthétiques',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Modèle retenu : ${result.h2oSelected ? 'H2O AutoML' : 'Persistance'}.\n'
              'Candidat H2O : ${result.candidate}.\n'
              'Erreur sur le test : ${_decimal(result.modelError, 'points de pourcentage')}, '
              'contre ${_decimal(result.persistenceError, 'points')} en conservant le dernier taux.',
            ),
            const SizedBox(height: 8),
            Text('Run MLflow : ${result.runId}'),
          ],
        ),
      ),
    ],
  );
}

class _Forecast {
  final DateTime targetDate, issuedDate;
  final String mountainPoint, candidate, runId;
  final double rain,
      snow,
      temperature,
      initialSnow,
      melt,
      modelError,
      persistenceError;
  final bool h2oSelected;
  final List<_ReservoirForecast> reservoirs;

  factory _Forecast.fromJson(Json json) {
    final weather = json['weather'] as Json;
    if (json['data_kind'] != 'DEMO' ||
        json['status'] != 'experimental_synthetic_training' ||
        json['horizon_days'] != 7 ||
        json['target_kind'] != 'filling_rate_pct' ||
        weather['provider'] != 'Open-Meteo' ||
        weather['kind'] != 'weather_model_forecast') {
      throw const FormatException('Contrat de prévision DEMO incompatible.');
    }
    return _Forecast._(
      json,
      weather,
      json['conditions'] as Json,
      json['metrics_synthetic_only'] as Json,
    );
  }

  _Forecast._(Json json, Json weather, Json scenario, Json metrics)
    : targetDate = DateTime.parse(json['target_date'] as String),
      issuedDate = DateTime.parse(weather['issue_date'] as String),
      mountainPoint = weather['mountain_point'] as String,
      rain = (scenario['forecast_rain_mm'] as num).toDouble(),
      snow = (scenario['forecast_snow_water_mm'] as num).toDouble(),
      temperature = (scenario['forecast_temperature_c'] as num).toDouble(),
      initialSnow = (scenario['snow_water_mm'] as num).toDouble(),
      melt = (scenario['forecast_melt_mm'] as num).toDouble(),
      h2oSelected = json['selected_on_synthetic_validation'] == 'h2o_automl',
      candidate = json['h2o_candidate'] as String,
      runId = json['mlflow_run_id'] as String,
      modelError = ((metrics['test_selected'] as Json)['mae_pp'] as num)
          .toDouble(),
      persistenceError =
          ((metrics['test_persistence'] as Json)['mae_pp'] as num).toDouble(),
      reservoirs = (json['reservoirs'] as List)
          .map((item) => _ReservoirForecast.fromJson(item as Json))
          .toList(growable: false);
}

class _ReservoirForecast {
  final String name;
  final double predicted, initial, capacity, storage, candidate;

  _ReservoirForecast.fromJson(Json json)
    : name = json['name'] as String,
      predicted = (json['predicted_filling_pct_demo'] as num).toDouble(),
      initial = (json['initial_filling_pct_demo'] as num).toDouble(),
      capacity = (json['capacity_mm3_demo'] as num).toDouble(),
      storage = (json['predicted_storage_mm3_demo'] as num).toDouble(),
      candidate = (json['h2o_filling_pct_demo'] as num).toDouble();
}
