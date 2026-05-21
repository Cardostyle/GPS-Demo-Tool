import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'package:gps_demo_tool/controller/exporting.dart';

class PhotoExperimentPage extends StatefulWidget {
  const PhotoExperimentPage({super.key});

  @override
  State<PhotoExperimentPage> createState() => _PhotoExperimentPageState();
}

class _PhotoExperimentPageState extends State<PhotoExperimentPage> {
  final controller = PhotoExperimentController();
  final noteController = TextEditingController();

  EnvironmentType environmentType = EnvironmentType.openArea;
  bool keepImageFile = true;
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
    setState(() {
      isRunning = true;
      status = 'Foto-Experiment wird vorbereitet...';
      lastRecord = null;
    });

    try {
      final record = await controller.runPhotoExperiment(
        environmentType: environmentType,
        keepImageFile: keepImageFile,
        note: noteController.text.trim().isEmpty ? null : noteController.text.trim(),
        photo: photo,
        referencePhoto: referencePhoto,
        onStatus: (value) {
          if (!mounted) return;
          setState(() => status = value);
        },
      );

      if (!mounted) return;
      setState(() {
        lastRecord = record;
        status = 'Fertig. ${record.measurements.length} Messungen gespeichert.';
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

  @override
  void dispose() {
    noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
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
                enabled: !isRunning,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Bemerkungen / Notizen',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Bilddatei speichern'),
                subtitle: const Text('Aus: nur EXIF-/Fotometadaten im JSON speichern'),
                value: keepImageFile,
                onChanged: isRunning ? null : (value) => setState(() => keepImageFile = value),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: isRunning ? null : takePhoto,
                icon: const Icon(Icons.photo_camera),
                label: Text(photo == null ? 'Foto aufnehmen' : 'Foto ersetzen'),
              ),
              OutlinedButton.icon(
                onPressed: isRunning ? null : takeReferencePhoto,
                icon: const Icon(Icons.fact_check),
                label: Text(referencePhoto == null
                    ? 'Referenzgerät fotografieren'
                    : 'Referenzfoto ersetzen'),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: isRunning ? null : startExperiment,
                icon: const Icon(Icons.play_arrow),
                label: const Text('5 GNSS-Messungen starten'),
              ),
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
                  'Datensatz: ${lastRecord!.id}\nMessungen: ${lastRecord!.measurements.length}',
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
