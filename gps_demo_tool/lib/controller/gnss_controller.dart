import 'package:geolocator/geolocator.dart';

import 'device_info_controller.dart';
import 'experiment_models.dart';
import 'gnss_auxiliary_data_controller.dart';

class GnssController {
  GnssController({
    DeviceInfoController? deviceInfoController,
    GnssAuxiliaryDataController? auxiliaryDataController,
  })  : _deviceInfoController = deviceInfoController ?? DeviceInfoController(),
        _auxiliaryDataController =
            auxiliaryDataController ?? GnssAuxiliaryDataController();

  final DeviceInfoController _deviceInfoController;
  final GnssAuxiliaryDataController _auxiliaryDataController;

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

    final auxiliaryDataFuture = _auxiliaryDataController.captureAuxiliaryData();

    final position = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.best,
      timeLimit: const Duration(seconds: 15),
    );

    final auxiliaryData = await auxiliaryDataFuture;
    final deviceInfo = await _deviceInfoController.readDeviceInfo();
    final measuredAt = DateTime.now().toUtc();
    final timestamp = position.timestamp.toUtc();

    return GnssMeasurement(
      id: '${experimentId}_M$sequenceNumber',
      experimentId: experimentId,
      sequenceNumber: sequenceNumber,
      latitude: position.latitude,
      longitude: position.longitude,
      altitude: position.altitude,
      timestampUtc: timestamp,
      measuredAtUtc: measuredAt,
      deviceModel: deviceInfo.deviceModel,
      androidVersion: deviceInfo.androidVersion,
      environmentType: environmentType,
      locationAccuracyMeters: position.accuracy,
      altitudeAccuracyMeters: position.altitudeAccuracy,
      heading: position.heading,
      speed: position.speed,
      offsetSeconds: offsetSeconds,
      note: note,
      visibleSatellites: auxiliaryData.visibleSatellites,
      usedSatellites: auxiliaryData.usedSatellites,
      cn0DbHz: auxiliaryData.cn0DbHz,
      hdop: auxiliaryData.hdop,
      pdop: auxiliaryData.pdop,
      vdop: auxiliaryData.vdop,
    );
  }
}

class GnssException implements Exception {
  const GnssException(this.message);
  final String message;

  @override
  String toString() => message;
}
