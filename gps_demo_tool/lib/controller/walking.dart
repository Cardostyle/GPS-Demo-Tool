import 'package:geolocator/geolocator.dart';

class WalkingController {
  Future<String> getCurrentLocationText() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();

    if (!serviceEnabled) {
      return 'Standortdienste sind deaktiviert.';
    }

    var permission = await Geolocator.checkPermission();

    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();

      if (permission == LocationPermission.denied) {
        return 'Standort-Berechtigung wurde abgelehnt.';
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return 'Standort-Berechtigung dauerhaft abgelehnt.';
    }

    final position = await Geolocator.getCurrentPosition();

    return 'Latitude: ${position.latitude}\nLongitude: ${position.longitude}';
  }
}
