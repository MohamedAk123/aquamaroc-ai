import 'package:material_ui/material_ui.dart';
import 'package:http/http.dart' as http;

import 'data/api_client.dart';
import 'data/local_store.dart';
import 'data/repository.dart';
import 'domain/models.dart';
import 'presentation/app.dart';
import 'presentation/app_controller.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    const baseUrl = String.fromEnvironment(
      'API_URL',
      defaultValue: 'http://127.0.0.1:8000',
    );
    const modeName = String.fromEnvironment('APP_MODE', defaultValue: 'official');
    final mode = parseMode(modeName);
    final api = ApiClient(baseUrl: baseUrl, mode: mode, client: http.Client());
    final controller = AppController(AquaRepository(api, PreferencesStore()));
    runApp(AquaMarocApp(controller: controller));
  } catch (_) {
    runApp(
      const MaterialApp(
        home: Scaffold(
          body: SafeArea(
            child: Center(
              child: Text(
                'Configuration invalide. Vérifiez API_URL et APP_MODE.',
              ),
            ),
          ),
        ),
      ),
    );
  }
}
