import 'experiment_models.dart';
import 'gnss_controller.dart';

class WalkingController {
  WalkingController({GnssController? gnssController})
      : _gnss = gnssController ?? GnssController();

  final GnssController _gnss;

  Future<String> getCurrentLocationText() async {
    try {
      final measurement = await _gnss.takeMeasurement(
        experimentId: newExperimentId('single'),
        sequenceNumber: 1,
        environmentType: EnvironmentType.openArea,
        offsetSeconds: 0,
      );

      return 'Latitude: ${measurement.latitude}\n'
          'Longitude: ${measurement.longitude}\n'
          'Höhe: ${measurement.altitude.toStringAsFixed(2)} m\n'
          'Genauigkeit: ${measurement.locationAccuracyMeters.toStringAsFixed(2)} m\n'
          'UTC: ${measurement.timestampUtc.toIso8601String()}';
    } on GnssException catch (error) {
      return error.message;
    } catch (error) {
      return 'Position konnte nicht gelesen werden: $error';
    }
  }
}
