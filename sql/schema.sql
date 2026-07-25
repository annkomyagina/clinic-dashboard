CREATE TABLE patients (
    patient_id INT PRIMARY KEY,
    last_name VARCHAR(100),
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    birth_date DATE,
    gender CHAR(1),
    phone VARCHAR(50),
    email VARCHAR(100)
);

CREATE TABLE doctors (
    doctor_id INT PRIMARY KEY,
    last_name VARCHAR(100),
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    specialization VARCHAR(100),
    base_price DECIMAL(10, 2)
);

CREATE TABLE appointments (
    appointment_id INT PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id),
    doctor_id INT REFERENCES doctors(doctor_id),
    appointment_datetime TIMESTAMP,
    status VARCHAR(50),
    diagnosis_code VARCHAR(10),
    diagnosis_name VARCHAR(200),
    price DECIMAL(10, 2)
);

CREATE INDEX idx_appointments_date ON appointments(appointment_datetime);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_status ON appointments(status);