class MwkiFormData {
  const MwkiFormData({
    required this.name,
    required this.email,
    required this.street,
    required this.city,
    required this.note,
  });

  final String name;
  final String email;
  final String street;
  final String city;
  final String note;
}

class MwkiController {
  String? validateName(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Bitte gib einen Namen ein.';
    }
    return null;
  }

  String? validateEmail(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Bitte gib eine E-Mail ein.';
    }

    return null;
  }


  MwkiFormData createFormData({
    required String name,
    required String email,
    required String street,
    required String city,
    required String note,
  }) {
    return MwkiFormData(
      name: name.trim(),
      email: email.trim(),
      street: street.trim(),
      city: city.trim(),
      note: note.trim(),
    );
  }



  String buildSubmitMessage(MwkiFormData data) {
    return 'Name: ${data.name}\n'
        'E-Mail: ${data.email}\n'
        'Straße: ${data.street}\n'
        'Stadt: ${data.city}\n'
        'Notiz: ${data.note}';
  }
}
