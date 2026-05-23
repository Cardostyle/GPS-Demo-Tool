import 'dart:io';

import 'package:device_info_plus/device_info_plus.dart';

class DeviceInfoSnapshot {
  const DeviceInfoSnapshot({
    required this.deviceModel,
    required this.androidVersion,
  });

  final String deviceModel;
  final String? androidVersion;
}

class DeviceInfoController {
  DeviceInfoController({DeviceInfoPlugin? plugin})
      : _plugin = plugin ?? DeviceInfoPlugin();

  final DeviceInfoPlugin _plugin;

  Future<DeviceInfoSnapshot> readDeviceInfo() async {
    if (Platform.isAndroid) {
      final androidInfo = await _plugin.androidInfo;
      final manufacturer = androidInfo.manufacturer.trim();
      final model = androidInfo.model.trim();
      final deviceModel = manufacturer.isEmpty
          ? model
          : model.toLowerCase().contains(manufacturer.toLowerCase())
              ? model
              : '$manufacturer $model';

      return DeviceInfoSnapshot(
        deviceModel: deviceModel,
        androidVersion: androidInfo.version.release,
      );
    }

    return DeviceInfoSnapshot(
      deviceModel: '${Platform.operatingSystem} ${Platform.operatingSystemVersion}',
      androidVersion: Platform.isAndroid ? Platform.operatingSystemVersion : null,
    );
  }
}
