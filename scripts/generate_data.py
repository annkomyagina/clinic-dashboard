from faker import Faker
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

faker = Faker('ru_RU')
Faker.seed(42)
np.random.seed(42)
random.seed(42)

# Создаём папку data, если её нет
os.makedirs('data', exist_ok=True)

# 1. Генерируем пациентов
num_patients = 5000
patients = []
for i in range(1, num_patients + 1):
    gender = random.choice(['M', 'F'])
    if gender == 'M':
        first_name = faker.first_name_male()
        middle_name = faker.middle_name_male()
        last_name = faker.last_name_male()
    else:
        first_name = faker.first_name_female()
        middle_name = faker.middle_name_female()
        last_name = faker.last_name_female()
    
    birth_date = faker.date_of_birth(minimum_age=0, maximum_age=90)
    patients.append({
        'patient_id': i,
        'last_name': last_name,
        'first_name': first_name,
        'middle_name': middle_name,
        'birth_date': birth_date,
        'gender': gender,
        'phone': faker.phone_number(),
        'email': faker.email()
    })

df_patients = pd.DataFrame(patients)
df_patients.to_csv('data/patients.csv', index=False)
print(f"Сгенерировано {len(df_patients)} пациентов")

# 2. Генерируем врачей
specializations = {
    'Терапевт': 1500,
    'Кардиолог': 2500,
    'Невролог': 2500,
    'Педиатр': 1800,
    'Офтальмолог': 2000
}

doctors = []
doc_id = 1
for spec, price in specializations.items():
    for _ in range(4):
        gender = random.choice(['M', 'F'])
        if gender == 'M':
            first_name = faker.first_name_male()
            middle_name = faker.middle_name_male()
            last_name = faker.last_name_male()
        else:
            first_name = faker.first_name_female()
            middle_name = faker.middle_name_female()
            last_name = faker.last_name_female()
        
        doctors.append({
            'doctor_id': doc_id,
            'last_name': last_name,
            'first_name': first_name,
            'middle_name': middle_name,
            'specialization': spec,
            'base_price': price
        })
        doc_id += 1

df_doctors = pd.DataFrame(doctors)
df_doctors.to_csv('data/doctors.csv', index=False)
print(f"Сгенерировано {len(df_doctors)} врачей")
print("Файлы patients.csv и doctors.csv созданы в папке data/")

# 3. Генерируем расписание врачей и записи на приём
start_date = datetime(2025, 1, 1)
end_date = datetime(2026, 12, 31)
work_start = 8
work_end = 18
slot_duration = 30  # минут

# МКБ-10 по специализациям
mkb = {
    'Терапевт': [('J06', 'Острая инфекция верхних дыхательных путей'),
                 ('J20', 'Острый бронхит'), ('I10', 'Гипертоническая болезнь'),
                 ('E11', 'Сахарный диабет 2 типа'), ('K29', 'Гастрит'),
                 ('M54', 'Дорсалгия'), ('N39', 'Инфекция мочевыводящих путей')],
    'Кардиолог': [('I10', 'Гипертоническая болезнь'), ('I20', 'Стенокардия'),
                  ('I25', 'Хроническая ишемическая болезнь сердца'),
                  ('I48', 'Фибрилляция предсердий'), ('I50', 'Сердечная недостаточность')],
    'Невролог': [('G43', 'Мигрень'), ('G44', 'Головная боль напряжения'),
                 ('M51', 'Поражение межпозвоночных дисков'), ('G40', 'Эпилепсия'),
                 ('F41', 'Тревожное расстройство')],
    'Педиатр': [('J06', 'Острая инфекция верхних дыхательных путей'),
                ('J20', 'Острый бронхит'), ('A08', 'Вирусная кишечная инфекция'),
                ('L20', 'Атопический дерматит'), ('H66', 'Средний отит')],
    'Офтальмолог': [('H52', 'Нарушения рефракции'), ('H40', 'Глаукома'),
                    ('H25', 'Катаракта'), ('H10', 'Конъюнктивит'),
                    ('H35', 'Заболевания сетчатки')]
}

appointments = []
appt_id = 1

# Вероятность, что слот будет занят
booking_prob = 0.75

current_date = start_date
while current_date <= end_date:
    # Пропускаем субботу (5) и воскресенье (6)
    if current_date.weekday() >= 5:
        current_date += timedelta(days=1)
        continue
    
    for _, doctor in df_doctors.iterrows():
        doc_id = doctor['doctor_id']
        spec = doctor['specialization']
        base_price = doctor['base_price']
        
        current_time = datetime(current_date.year, current_date.month, current_date.day, work_start, 0)
        while current_time.hour < work_end:
            if random.random() < booking_prob:
                # Выбираем пациента
                patient = df_patients.sample(1).iloc[0]
                
                # Статус записи
                status = random.choices(
                    ['состоялся', 'неявка', 'отмена'],
                    weights=[0.85, 0.10, 0.05]
                )[0]
                
                # Диагноз (только для состоявшихся)
                diagnosis_code = None
                diagnosis_name = None
                if status == 'состоялся':
                    diagnosis_code, diagnosis_name = random.choice(mkb[spec])
                
                # Стоимость с вариацией
                final_price = round(base_price * random.uniform(0.8, 1.2), 2) if status == 'состоялся' else 0
                
                appointments.append({
                    'appointment_id': appt_id,
                    'patient_id': patient['patient_id'],
                    'doctor_id': doc_id,
                    'appointment_datetime': current_time,
                    'status': status,
                    'diagnosis_code': diagnosis_code,
                    'diagnosis_name': diagnosis_name,
                    'price': final_price
                })
                appt_id += 1
            
            current_time += timedelta(minutes=slot_duration)
    
    # Прогресс каждые 100 дней
    days_passed = (current_date - start_date).days
    if days_passed % 100 == 0 and days_passed > 0:
        print(f"Обработано {days_passed} дней из 730, создано {len(appointments)} записей")
    
    current_date += timedelta(days=1)

df_appointments = pd.DataFrame(appointments)
df_appointments.to_csv('data/appointments.csv', index=False)
print(f"\nГотово! Сгенерировано {len(df_appointments)} записей на приём")
print(f"Файл appointments.csv создан в папке data/")