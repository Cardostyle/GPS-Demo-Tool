import 'experiment_models.dart';
import 'gnss_controller.dart';

class GnssTestingController {
  GnssTestingController({GnssController? gnssController})
      : _gnss = gnssController ?? GnssController();

  final GnssController _gnss;

  Future<String> getCurrentLocationText() async {
    try {
      final measurement = await _gnss.takeMeasurement(
        experimentId: 'GNSS_Test_${utcTimestampForFile(DateTime.now())}',
        sequenceNumber: 1,
        environmentType: EnvironmentType.openArea,
        offsetSeconds: 0,
      );

      return 'Latitude: ${measurement.latitude}\n'
          'Longitude: ${measurement.longitude}\n'
          'Höhe: ${measurement.altitude.toStringAsFixed(2)} m\n'
          'Genauigkeit: ${measurement.locationAccuracyMeters.toStringAsFixed(2)} m\n'
          'Sichtbare Satelliten: ${measurement.visibleSatellites ?? 'null'}\n'
          'Verwendete Satelliten: ${measurement.usedSatellites ?? 'null'}\n'
          'C/N0 Ø: ${measurement.cn0DbHz?.toStringAsFixed(1) ?? 'null'} dB-Hz\n'
          'HDOP: ${measurement.hdop?.toStringAsFixed(2) ?? 'null'}\n'
          'PDOP: ${measurement.pdop?.toStringAsFixed(2) ?? 'null'}\n'
          'Gerät: ${measurement.deviceModel}\n'
          'Android: ${measurement.androidVersion ?? 'null'}\n'
          'UTC: ${measurement.timestampUtc.toIso8601String()}';
    } on GnssException catch (error) {
      return error.message;
    } catch (error) {
      return 'Position konnte nicht gelesen werden: $error';
    }
  }
}
