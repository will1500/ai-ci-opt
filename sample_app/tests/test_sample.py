import pytest
from sample_app.app import PatientRecord

def test_add_medication():
    record = PatientRecord("123", 25)
    meds = record.add_medication("Aspirin", 100)
    assert meds == [{"name": "Aspirin", "dose_mg": 100}]

def test_add_invalid_dose():
    record = PatientRecord("123", 25)
    with pytest.raises(ValueError):
        record.add_medication("Ibuprofen", 0)

def test_remove_medication():
    record = PatientRecord("123", 25)
    record.add_medication("Aspirin", 100)
    meds = record.remove_medication("Aspirin")
    assert meds == []

def test_pediatric_true():
    record = PatientRecord("456", 10)
    assert record.is_pediatric() is True

def test_pediatric_false():
    record = PatientRecord("789", 30)
    assert record.is_pediatric() is False

def test_flaky_external_lab():
    import random
    if random.random() < 0.3:
        pytest.skip("flaky lab result service")
    record = PatientRecord("101", 40)
    record.add_medication("Vitamin D", 50)
    assert len(record.medications) == 1

def test_slow_patient_processing():
    import time
    time.sleep(1)
    record = PatientRecord("102", 22)
    record.add_medication("Paracetamol", 500)
    assert len(record.medications) == 1
