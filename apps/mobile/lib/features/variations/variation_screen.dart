import 'package:material_ui/material_ui.dart';

import '../../data/api_client.dart';
import '../../domain/models.dart';
import '../../presentation/widgets.dart';

class VariationScreen extends StatefulWidget {
  final ApiClient api;
  const VariationScreen({super.key, required this.api});

  @override
  State<VariationScreen> createState() => _VariationScreenState();
}

class _VariationScreenState extends State<VariationScreen> {
  late Future<_Study?> load = _load();

  Future<_Study?> _load() async {
    final payload = await widget.api.get('/data/variation-review');
    widget.api.checkMode(payload);
    if (payload['status'] != 'available') return null;
    return _Study.fromJson(payload['report'] as Map<String, dynamic>);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Variations inhabituelles · IA')),
    body: SafeArea(
      child: FutureBuilder<_Study?>(
        future: load,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Notice(
                  'Analyse momentanément inaccessible.',
                  warning: true,
                  action: TextButton(
                    onPressed: () => setState(() => load = _load()),
                    child: const Text('Réessayer'),
                  ),
                ),
              ),
            );
          }
          final study = snapshot.data;
          if (study == null) {
            return const Padding(
              padding: EdgeInsets.all(16),
              child: Notice(
                'Aucun rapport IA ne correspond aux relevés du jeu actif.',
              ),
            );
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              SectionCard(
                title: 'Étude rétrospective · Isolation Forest',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${study.findings.length} variations à examiner sur ${study.analysedSamples} relevés officiels analysés.',
                    ),
                    Text('Du ${day(study.start)} au ${day(study.end)}'),
                    const SizedBox(height: 8),
                    const Text(
                      'Les écarts sur 1 et 7 jours sont comparés à l’historique du même barrage. Chaque signalement appelle une vérification des relevés et du contexte.',
                    ),
                  ],
                ),
              ),
              if (study.findings.isEmpty)
                const Notice('Aucun relevé au-delà du seuil de tri.'),
              for (final item in study.findings)
                SectionCard(
                  title: item.name,
                  child: Text(
                    '${day(item.observedAt)}\n'
                    'Réserve : ${number(item.storage, 'Mm³')}\n'
                    'Écart sur 1 j : ${number(item.daily, 'Mm³')}\n'
                    'Écart sur 7 j : ${number(item.weekly, 'Mm³')}',
                  ),
                ),
            ],
          );
        },
      ),
    ),
  );
}

class _Study {
  final DateTime start, end;
  final int analysedSamples;
  final List<_Finding> findings;
  _Study.fromJson(Map<String, dynamic> json)
    : start = DateTime.parse(json['analysed_start'] as String),
      end = DateTime.parse(json['analysed_end'] as String),
      analysedSamples = json['analysed_samples'] as int,
      findings = (json['findings'] as List<dynamic>)
          .map((row) => _Finding.fromJson(row as Map<String, dynamic>))
          .toList();
}

class _Finding {
  final String name;
  final DateTime observedAt;
  final double storage, daily, weekly;
  _Finding.fromJson(Map<String, dynamic> json)
    : name = json['reservoir_name'] as String,
      observedAt = DateTime.parse(json['observation_date'] as String),
      storage = double.parse(json['storage_mm3'] as String),
      daily = double.parse(json['delta_1d_mm3'] as String),
      weekly = double.parse(json['delta_7d_mm3'] as String);
}
