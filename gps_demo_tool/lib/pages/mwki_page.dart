import 'package:flutter/material.dart';
import 'package:gps_demo_tool/controller/mwki.dart';

class MWKIPage extends StatefulWidget {
  const MWKIPage({super.key});

  @override
  State<MWKIPage> createState() => _MWKIPageState();
}

class _MWKIPageState extends State<MWKIPage> {
  final formKey = GlobalKey<FormState>();
  final controller = MwkiController();

  final nameController = TextEditingController();
  final emailController = TextEditingController();
  final streetController = TextEditingController();
  final cityController = TextEditingController();
  final noteController = TextEditingController();

  void submitForm() {
    if (!(formKey.currentState?.validate() ?? false)) {
      return;
    }

    final formData = controller.createFormData(
      name: nameController.text,
      email: emailController.text,
      street: streetController.text,
      city: cityController.text,
      note: noteController.text,
    );

    showDialog<void>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Formular abgeschickt'),
          content: Text(controller.buildSubmitMessage(formData)),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
  }

  @override
  void dispose() {
    nameController.dispose();
    emailController.dispose();
    streetController.dispose();
    cityController.dispose();
    noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('MeineWaldKI Formular'),
      ),
      body: SafeArea(
        child: Form(
          key: formKey,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: nameController,
                  decoration: const InputDecoration(
                    labelText: 'Name',
                    border: OutlineInputBorder(),
                  ),
                  validator: controller.validateName,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'E-Mail',
                    border: OutlineInputBorder(),
                  ),
                  validator: controller.validateEmail,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: streetController,
                  decoration: const InputDecoration(
                    labelText: 'Straße',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: cityController,
                  decoration: const InputDecoration(
                    labelText: 'Stadt',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: noteController,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Notiz',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 32),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 50),
                  ),
                  onPressed: submitForm,
                  child: const Text('Formular absenden'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
