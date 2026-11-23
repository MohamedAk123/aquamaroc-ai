import 'package:shared_preferences/shared_preferences.dart';

abstract interface class LocalStore {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
}

class PreferencesStore implements LocalStore {
  final SharedPreferencesAsync preferences;
  PreferencesStore([SharedPreferencesAsync? preferences])
    : preferences = preferences ?? SharedPreferencesAsync();
  @override
  Future<String?> read(String key) => preferences.getString(key);
  @override
  Future<void> write(String key, String value) =>
      preferences.setString(key, value);
}
