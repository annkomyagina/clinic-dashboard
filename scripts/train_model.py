import pandas as pd
from sqlalchemy import create_engine
from prophet import Prophet

engine = create_engine('postgresql://clinic_user:clinic_pass@localhost:5432/clinic_db')

# Загружаем дневную агрегацию
query = """
SELECT
    DATE(appointment_datetime) AS ds,
    COUNT(*) AS y
FROM appointments
WHERE status = 'состоялся'
GROUP BY ds
ORDER BY ds
"""
df = pd.read_sql(query, engine)
df['ds'] = pd.to_datetime(df['ds'])

# Обучаем модель
model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
model.fit(df)

# Прогноз на 30 дней вперёд
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

# Сохраняем
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv('data/forecast.csv', index=False)
print(f"Прогноз сохранён: {len(forecast)} дней")
print(f"Файл forecast.csv создан в папке data/")