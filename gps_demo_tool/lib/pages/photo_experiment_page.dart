import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'package:gps_demo_tool/controller/experiment_models.dart';
import 'package:gps_demo_tool/controller/photo_experiment_controller.dart';

class PhotoExperimentPage extends StatefulWidget {
  const PhotoExperimentPage({super.key});

  @override
  State<PhotoExperimentPage> createState() => _PhotoExperimentPageState();
}

class _PhotoExperimentPageState extends State<PhotoExperimentPage> {
  final controller = PhotoExperimentController();
  final noteController = TextEditingController();
  final referenceLatitudeController = TextEditingController();
  final referenceLongitudeController = TextEditingController();
  final referenceAltitudeController = TextEditingController();

  EnvironmentType environmentType = EnvironmentType.openArea;
  bool isRunning = false;
  String status = 'Noch kein Foto-Experiment gestartet.';
  PhotoExperimentRecord? lastRecord;
  XFile? photo;
  XFile? referencePhoto;

  Future<void> takePhoto() async {
    final picked = await controller.takePhoto();
    if (!mounted || picked == null) return;
    setState(() {
      photo = picked;
      status = 'Foto aufgenommen: ${picked.name}';
    });
  }

  Future<void> takeReferencePhoto() async {
    final picked = await controller.takePhoto();
    if (!mounted || picked == null) return;
    setState(() {
      referencePhoto = picked;
      status = 'Referenzfoto aufgenommen: ${picked.name}';
    });
  }

  Future<void> startExperiment() async {
    final selectedPhoto = photo;
    if (selectedPhoto == null) {
      setState(() => status = 'Bitte zuerst ein Foto aufnehmen. Danach kann die Messung gestartet werden.');
      return;
    }

    setState(() {
      isRunning = true;
      status = 'Foto-Experiment wird vorbereitet...';
      lastRecord = null;
    });

    try {
      final record = await controller.runPhotoExperiment(
        environmentType: environmentType,
        photo: selectedPhoto,
        referencePhoto: referencePhoto,
        readCurrentNote: () => noteController.text,
        readCurrentReferenceData: readReferenceData,
        onStatus: (value) {
          if (!mounted) return;
          setState(() => status = value);
        },
      );

      if (!mounted) return;
      setState(() {
        lastRecord = record;
        photo = null;
        referencePhoto = null;
        status = 'Fertig. ${record.measurements.length} Messungen gespeichert. Foto wurde von der Seite entfernt.';
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => status = 'Fehler: $error');
    } finally {
      if (mounted) {
        setState(() => isRunning = false);
      }
    }
  }

  ReferenceData readReferenceData() {
    return ReferenceData(
      latitude: double.tryParse(referenceLatitudeController.text.trim().replaceAll(',', '.')),
      longitude: double.tryParse(referenceLongitudeController.text.trim().replaceAll(',', '.')),
      altitude: double.tryParse(referenceAltitudeController.text.trim().replaceAll(',', '.')),
    );
  }

  @override
  void dispose() {
    noteController.dispose();
    referenceLatitudeController.dispose();
    referenceLongitudeController.dispose();
    referenceAltitudeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final canStart = !isRunning && photo != null;

    return Scaffold(
      appBar: AppBar(title: const Text('Foto-Experiment')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              DropdownButtonFormField<EnvironmentType>(
                value: environmentType,
                decoration: const InputDecoration(
                  labelText: 'Umgebungstyp',
                  border: OutlineInputBorder(),
                ),
                items: EnvironmentType.values
                    .map(
                      (type) => DropdownMenuItem(
                        value: type,
                        child: Text(type.label),
                      ),
                    )
                    .toList(),
                onChanged: isRunning
                    ? null
                    : (value) {
                        if (value != null) {
                          setState(() => environmentType = value);
                        }
                      },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: noteController,
                enabled: true,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Bemerkungen / Notizen',
                  helperText: 'Kann auch während der Messung weiter bearbeitet werden.',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Referenzdaten',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: referenceLatitudeController,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                      decoration: const InputDecoration(
                        labelText: 'Ref. Lat',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: referenceLongitudeController,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                      decoration: const InputDecoration(
                        labelText: 'Ref. Long',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: referenceAltitudeController,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                      decoration: const InputDecoration(
                        labelText: 'Ref. Alt',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: isRunning ? null : takePhoto,
                icon: const Icon(Icons.photo_camera),
                label: Text(photo == null ? 'Foto aufnehmen' : 'Foto ersetzen: ${photo!.name}'),
              ),
              OutlinedButton.icon(
                onPressed: isRunning ? null : takeReferencePhoto,
                icon: const Icon(Icons.fact_check),
                label: Text(referencePhoto == null
                    ? 'Referenzgerät fotografieren'
                    : 'Referenzfoto ersetzen: ${referencePhoto!.name}'),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: canStart ? startExperiment : null,
                icon: const Icon(Icons.play_arrow),
                label: const Text('5 GNSS-Messungen starten'),
              ),
              if (photo == null && !isRunning) ...[
                const SizedBox(height: 8),
                const Text('Start erst möglich, wenn ein Foto hinterlegt ist.'),
              ],
              const SizedBox(height: 20),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(status),
                ),
              ),
              if (lastRecord != null) ...[
                const SizedBox(height: 16),
                Text(
                  'Datensatz: ${lastRecord!.id}\n'
                  'Messungen: ${lastRecord!.measurements.length}\n'
                  'Foto: ${lastRecord!.photoRelativePath ?? '-'}\n'
                  'Referenzfoto: ${lastRecord!.referencePhotoRelativePath ?? '-'}',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
