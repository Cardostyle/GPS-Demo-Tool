import 'dart:async';

import 'package:gnss_diagnostics/gnss_diagnostics.dart';
import 'package:nmea_plugin/nmea_plugin.dart';

class GnssAuxiliaryData {
  const GnssAuxiliaryData({
    this.visibleSatellites,
    this.usedSatellites,
    this.cn0DbHz,
    this.hdop,
    this.pdop,
    this.vdop,
  });

  final int? visibleSatellites;
  final int? usedSatellites;
  final double? cn0DbHz;
  final double? hdop;
  final double? pdop;
  final double? vdop;

  static const empty = GnssAuxiliaryData();
}

class GnssAuxiliaryDataController {
  GnssAuxiliaryDataController({NmeaPlugin? nmeaPlugin})
      : _nmeaPlugin = nmeaPlugin ?? NmeaPlugin();

  final NmeaPlugin _nmeaPlugin;

  Future<GnssAuxiliaryData> captureAuxiliaryData({
    Duration duration = const Duration(seconds: 2),
  }) async {
    final gnssSnapshotFuture = _readGnssDiagnosticsSnapshot(duration);
    final nmeaSnapshotFuture = _readNmeaSnapshot(duration);

    final gnss = await gnssSnapshotFuture;
    final nmea = await nmeaSnapshotFuture;

    return GnssAuxiliaryData(
      visibleSatellites: _positiveOrNull(nmea.visibleSatellites) ??
          _positiveOrNull(gnss.visibleSatellites),
      usedSatellites: _positiveOrNull(nmea.usedSatellites) ??
          _positiveOrNull(gnss.usedSatellites),
      cn0DbHz: nmea.cn0DbHz,
      hdop: nmea.hdop,
      pdop: nmea.pdop,
      vdop: nmea.vdop,
    );
  }

  int? _positiveOrNull(int? value) {
    if (value == null || value <= 0) return null;
    return value;
  }

  Future<_GnssDiagnosticsValues> _readGnssDiagnosticsSnapshot(
    Duration timeout,
  ) async {
    try {
      final dynamic snapshot = await GnssDiagnostics.statusStream.first.timeout(
        timeout,
      );

      return _GnssDiagnosticsValues(
        visibleSatellites: _asIntOrNull(snapshot.totalInView),
        usedSatellites: _asIntOrNull(snapshot.totalUsedInFix),
      );
    } catch (_) {
      return const _GnssDiagnosticsValues();
    }
  }

  int? _asIntOrNull(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse('$value');
  }

  Future<_NmeaValues> _readNmeaSnapshot(Duration duration) async {
    final values = _MutableNmeaValues();
    StreamSubscription<NmeaMessage>? subscription;

    try {
      subscription = _nmeaPlugin.getNmeaMessageStream().listen(
        values.addMessage,
        onError: (_) {},
        cancelOnError: false,
      );

      await Future<void>.delayed(duration);
    } catch (_) {
      // Einige Geräte liefern keine NMEA-Sätze oder verweigern den Zugriff.
      // In diesem Fall bleiben die Zusatzfelder null statt die Messung abzubrechen.
    } finally {
      await subscription?.cancel();
    }

    return values.toSnapshot();
  }
}

class _GnssDiagnosticsValues {
  const _GnssDiagnosticsValues({
    this.visibleSatellites,
    this.usedSatellites,
  });

  final int? visibleSatellites;
  final int? usedSatellites;
}

class _NmeaValues {
  const _NmeaValues({
    this.visibleSatellites,
    this.usedSatellites,
    this.cn0DbHz,
    this.hdop,
    this.pdop,
    this.vdop,
  });

  final int? visibleSatellites;
  final int? usedSatellites;
  final double? cn0DbHz;
  final double? hdop;
  final double? pdop;
  final double? vdop;
}

class _MutableNmeaValues {
  int? visibleSatellites;
  int? usedSatellites;
  double? hdop;
  double? pdop;
  double? vdop;
  final List<int> _snrValues = <int>[];

  void addMessage(NmeaMessage message) {
    if (message is GgaMessage) {
      final hasFix = (message.fixQuality ?? 0) > 0;
      if (hasFix) {
        usedSatellites = message.numberOfSatellites ?? usedSatellites;
      }
      hdop = message.hdop ?? hdop;
    } else if (message is GsaMessage) {
      final usedPrns = message.prnNumbers.where((prn) => prn > 0).length;
      if (usedPrns > 0) {
        usedSatellites = usedPrns;
      }
      hdop = message.hdop ?? hdop;
      pdop = message.pdop ?? pdop;
      vdop = message.vdop ?? vdop;
    } else if (message is GsvMessage) {
      final satellitesInView = message.satellitesInView;
      if (satellitesInView > 0) {
        visibleSatellites = satellitesInView;
      }
      for (final satellite in message.satellites) {
        final snr = satellite.snr;
        if (snr != null && snr > 0) {
          _snrValues.add(snr);
        }
      }
    }
  }

  _NmeaValues toSnapshot() {
    final averageSnr = _snrValues.isEmpty
        ? null
        : _snrValues.reduce((a, b) => a + b) / _snrValues.length;

    return _NmeaValues(
      visibleSatellites: visibleSatellites,
      usedSatellites: usedSatellites,
      cn0DbHz: averageSnr,
      hdop: hdop,
      pdop: pdop,
      vdop: vdop,
    );
  }
}
