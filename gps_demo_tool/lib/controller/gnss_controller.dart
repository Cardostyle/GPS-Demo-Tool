import 'dart:io';

import 'package:geolocator/geolocator.dart';

import 'experiment_models.dart';

class GnssController {
  Future<String?> ensureLocationReady() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return 'Standortdienste sind deaktiviert. Bitte GPS aktivieren.';
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    if (permission == LocationPermission.denied) {
      return 'Standort-Berechtigung wurde abgelehnt.';
    }

    if (permission == LocationPermission.deniedForever) {
      return 'Standort-Berechtigung ist dauerhaft abgelehnt. Bitte in den Android-Einstellungen aktivieren.';
    }

    return null;
  }

  Future<GnssMeasurement> takeMeasurement({
    required String experimentId,
    required int sequenceNumber,
    required EnvironmentType environmentType,
    required int offsetSeconds,
    String? note,
  }) async {
    final error = await ensureLocationReady();
    if (error != null) {
      throw GnssException(error);
    }

    final position = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.best,
      timeLimit: const Duration(seconds: 15),
    );

    final measuredAt = DateTime.now().toUtc();
    final timestamp = position.timestamp.toUtc();

    return GnssMeasurement(
      id: '${experimentId}_m$sequenceNumber',
      experimentId: experimentId,
      sequenceNumber: sequenceNumber,
      latitude: position.latitude,
      longitude: position.longitude,
      altitude: position.altitude,
      timestampUtc: timestamp,
      measuredAtUtc: measuredAt,
      deviceModel: _deviceLabel(),
      environmentType: environmentType,
      locationAccuracyMeters: position.accuracy,
      altitudeAccuracyMeters: position.altitudeAccuracy,
      heading: position.heading,
      speed: position.speed,
      offsetSeconds: offsetSeconds,
      note: note,
      // Geolocator liefert diese Roh-GNSS-Werte auf Android nicht direkt.
      // Die Felder bleiben bewusst in der JSON-Struktur, damit sie später
      // durch einen Android-GNSS-Status-Channel ergänzt werden können.
      visibleSatellites: null,
      usedSatellites: null,
      cn0DbHz: null,
      hdop: null,
      pdop: null,
    );
  }

  String _deviceLabel() {
    return '${Platform.operatingSystem} ${Platform.operatingSystemVersion}';
  }
}

class GnssException implements Exception {
  const GnssException(this.message);
  final String message;

  @override
  String toString() => message;
}
