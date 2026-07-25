import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Дашборд клиники", layout="wide")
st.title("🏥 Аналитический дашборд частной клиники")

# Подключение к БД
import os
@st.cache_resource
def get_engine():
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    return create_engine(f'postgresql://clinic_user:clinic_pass@{DB_HOST}:5432/clinic_db')

engine = get_engine()

# Загружаем данные для фильтров
@st.cache_data
def load_doctors():
    return pd.read_sql("SELECT doctor_id, last_name || ' ' || first_name AS name, specialization FROM doctors", engine)

df_doctors = load_doctors()

# Боковая панель с фильтрами
st.sidebar.header("Фильтры")
date_range = st.sidebar.date_input("Период", [datetime(2025, 1, 1), datetime(2026, 12, 31)])
selected_doctor = st.sidebar.selectbox("Врач", ["Все"] + df_doctors['name'].tolist())

# Формируем WHERE-условия
where_clauses = ["status = 'состоялся'"]
if len(date_range) == 2:
    where_clauses.append(f"appointment_datetime >= '{date_range[0]}'")
    where_clauses.append(f"appointment_datetime <= '{date_range[1]}'")
if selected_doctor != "Все":
    doc_id = df_doctors[df_doctors['name'] == selected_doctor]['doctor_id'].values[0]
    where_clauses.append(f"doctor_id = {doc_id}")

where_str = " AND ".join(where_clauses)

# Ключевые метрики
query_metrics = f"""
SELECT
    COUNT(*) AS visit_count,
    ROUND(SUM(price)::numeric, 2) AS revenue,
    ROUND(AVG(price)::numeric, 2) AS avg_check
FROM appointments
WHERE {where_str}
"""
df_metrics = pd.read_sql(query_metrics, engine)

col1, col2, col3 = st.columns(3)
col1.metric("Приёмов", f"{df_metrics['visit_count'][0]:,}".replace(",", " "))
col2.metric("Выручка", f"{df_metrics['revenue'][0]:,.0f} ₽".replace(",", " "))
col3.metric("Средний чек", f"{df_metrics['avg_check'][0]:,.0f} ₽".replace(",", " "))

# График 1: Выручка по месяцам
st.subheader("Выручка по месяцам")
query_revenue = f"""
SELECT DATE_TRUNC('month', appointment_datetime) AS month, SUM(price) AS revenue
FROM appointments
WHERE {where_str}
GROUP BY month ORDER BY month
"""
df_revenue = pd.read_sql(query_revenue, engine)
fig1 = px.line(df_revenue, x='month', y='revenue', markers=True)
fig1.update_layout(yaxis_title="Выручка, ₽", xaxis_title="")
st.plotly_chart(fig1, use_container_width=True)

# График 2: Топ диагнозов
st.subheader("Топ-10 диагнозов")
query_diag = f"""
SELECT diagnosis_name, COUNT(*) AS cnt
FROM appointments
WHERE {where_str} AND diagnosis_name IS NOT NULL
GROUP BY diagnosis_name ORDER BY cnt DESC LIMIT 10
"""
df_diag = pd.read_sql(query_diag, engine)
fig2 = px.bar(df_diag, x='cnt', y='diagnosis_name', orientation='h')
fig2.update_layout(yaxis_title="", xaxis_title="Количество")
st.plotly_chart(fig2, use_container_width=True)

# График 3: Загрузка по часам и дням недели
st.subheader("Тепловая карта загрузки")
query_heatmap = f"""
SELECT
    EXTRACT(DOW FROM appointment_datetime)::int AS day_of_week,
    EXTRACT(HOUR FROM appointment_datetime)::int AS hour,
    COUNT(*) AS cnt
FROM appointments
WHERE {where_str}
GROUP BY day_of_week, hour ORDER BY day_of_week, hour
"""
df_heat = pd.read_sql(query_heatmap, engine)
days_map = {0: 'ПН', 1: 'ВТ', 2: 'СР', 3: 'ЧТ', 4: 'ПТ', 5: 'СБ', 6: 'ВС'}
pivot = df_heat.pivot(index='day_of_week', columns='hour', values='cnt').fillna(0)
pivot.index = [days_map.get(i, f'День {i}') for i in pivot.index]
fig3 = px.imshow(pivot, labels=dict(x="Час", y="День недели", color="Приёмов"),
                 x=[f"{h}:00" for h in pivot.columns],
                 color_continuous_scale="Blues")
st.plotly_chart(fig3, use_container_width=True)

# График 4: Доля неявок
st.subheader("Доля неявок по дням недели")
query_noshow = f"""
SELECT
    EXTRACT(DOW FROM appointment_datetime)::int AS day_of_week,
    ROUND(SUM(CASE WHEN status = 'неявка' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS no_show_pct
FROM appointments
WHERE status IN ('состоялся', 'неявка')
    AND appointment_datetime >= '{date_range[0]}'
    AND appointment_datetime <= '{date_range[1]}'
GROUP BY day_of_week ORDER BY day_of_week
"""
df_noshow = pd.read_sql(query_noshow, engine)
df_noshow['day_name'] = df_noshow['day_of_week'].apply(lambda x: days_map.get(x, f'День {x}'))
fig4 = px.bar(df_noshow, x='day_name', y='no_show_pct', text_auto='.1f')
fig4.update_layout(yaxis_title="% неявок", xaxis_title="", yaxis_range=[0, 20])
fig4.update_traces(texttemplate='%{text}%')
st.plotly_chart(fig4, use_container_width=True)

# График 5: Прогноз нагрузки
st.subheader("Прогноз нагрузки на 30 дней")
df_forecast = pd.read_csv('data/forecast.csv')
df_forecast['ds'] = pd.to_datetime(df_forecast['ds'])

# Разделяем на факт и прогноз
last_date = pd.to_datetime('2026-12-31')
df_fact = df_forecast[df_forecast['ds'] <= last_date]
df_pred = df_forecast[df_forecast['ds'] > last_date]

fig5 = go.Figure()
fig5.add_trace(go.Scatter(x=df_fact['ds'][-90:], y=df_fact['yhat'][-90:],
                          mode='lines', name='Факт', line=dict(color='blue')))
fig5.add_trace(go.Scatter(x=df_pred['ds'], y=df_pred['yhat'],
                          mode='lines', name='Прогноз', line=dict(color='red')))
fig5.add_trace(go.Scatter(x=df_pred['ds'], y=df_pred['yhat_upper'],
                          mode='lines', name='Верхняя граница',
                          line=dict(width=0), showlegend=False))
fig5.add_trace(go.Scatter(x=df_pred['ds'], y=df_pred['yhat_lower'],
                          mode='lines', name='Нижняя граница',
                          line=dict(width=0), showlegend=False,
                          fill='tonexty', fillcolor='rgba(255, 0, 0, 0.1)'))
fig5.update_layout(yaxis_title="Приёмов в день", xaxis_title="")
st.plotly_chart(fig5, use_container_width=True)

st.caption("Данные обновляются в реальном времени из PostgreSQL")