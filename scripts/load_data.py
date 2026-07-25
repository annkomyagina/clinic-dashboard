import pandas as pd
from sqlalchemy import create_engine

# Подключение к PostgreSQL
engine = create_engine('postgresql://clinic_user:clinic_pass@localhost:5432/clinic_db')

# Загружаем пациентов
df_patients = pd.read_csv('data/patients.csv')
df_patients.to_sql('patients', engine, if_exists='append', index=False)
print(f"Загружено {len(df_patients)} пациентов")

# Загружаем врачей
df_doctors = pd.read_csv('data/doctors.csv')
df_doctors.to_sql('doctors', engine, if_exists='append', index=False)
print(f"Загружено {len(df_doctors)} врачей")

# Загружаем записи на приём (чанками по 10 000, чтобы не перегружать память)
chunk_size = 10000
total = 0
for chunk in pd.read_csv('data/appointments.csv', chunksize=chunk_size):
    # Преобразуем дату
    chunk['appointment_datetime'] = pd.to_datetime(chunk['appointment_datetime'])
    chunk.to_sql('appointments', engine, if_exists='append', index=False)
    total += len(chunk)
    print(f"Загружено {total} записей на приём...")

print("Все данные загружены!")