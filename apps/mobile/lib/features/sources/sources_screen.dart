import 'package:material_ui/material_ui.dart';

import '../../domain/models.dart';
import '../../presentation/widgets.dart';

class SourcesScreen extends StatelessWidget {
  final Catalog catalog;
  const SourcesScreen({super.key, required this.catalog});
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      const SectionCard(
        title: 'Comment lire les données ?',
        icon: Icons.info_outline,
        child: Text(
          'La date de relevé décrit la mesure. La publication correspond à sa mise à disposition ; l’import à son intégration au serveur. '
          'La synchronisation correspond à sa récupération sur cet appareil. Aucun de ces horodatages ne garantit le temps réel.\n\n'
          'DEMO : jeu synthétique. OFFICIAL : provenance officielle validée. UNVERIFIED : données à vérifier, distinctes des séries officielles. '
          'Les sources et catégories restent séparées dans l’historique.\n\n'
          'Les favoris et le cache restent sur cet appareil, sans compte ni notifications. Le cache est séparé par serveur et mode. '
          'La synchronisation est manuelle ou au démarrage, sans tâche en arrière-plan.',
        ),
      ),
      if (catalog.sources.isEmpty)
        const Notice('Aucune source disponible dans le mode actif.'),
      for (final source in catalog.sources)
        SectionCard(
          title: source.title,
          icon: Icons.source_outlined,
          child: SelectableText(
            'Statut : ${source.status}\nProducteur : ${source.producer ?? 'Non renseigné'}\n'
            'Licence : ${source.license ?? 'À vérifier'}\nURL : ${source.url ?? 'Non renseignée'}\n'
            'Dernier relevé : ${day(source.observedAt)}\nPublication : ${instant(source.publishedAt)}\nImport : ${instant(source.ingestedAt)}',
          ),
        ),
      const SectionCard(
        title: 'Limites',
        child: Text(
          'Aucun modèle prédictif n’a été approuvé. Les données officielles restent soumises à audit. '
          'L’application ne délivre aucune alerte de risque hydrologique ni recommandation de sécurité.',
        ),
      ),
    ],
  );
}
