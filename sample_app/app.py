# sample_app/app.py

class PatientRecord:
    def __init__(self, patient_id, age):
        self.patient_id = patient_id
        self.age = age
        self.medications = []

    def add_medication(self, name, dose_mg):
        if dose_mg <= 0:
            raise ValueError("Dose must be positive")
        self.medications.append({"name": name, "dose_mg": dose_mg})
        return self.medications

    def remove_medication(self, name):
        self.medications = [m for m in self.medications if m["name"] != name]
        return self.medications

    def is_pediatric(self):
        return self.age < 18
