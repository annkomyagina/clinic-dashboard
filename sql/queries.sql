-- 1. Загрузка врачей по часам и дням недели
SELECT
    d.last_name || ' ' || d.first_name AS doctor_name,
    EXTRACT(DOW FROM a.appointment_datetime) AS day_of_week,
    EXTRACT(HOUR FROM a.appointment_datetime) AS hour,
    COUNT(*) AS appointment_count
FROM appointments a
JOIN doctors d ON a.doctor_id = d.doctor_id
WHERE a.status = 'состоялся'
GROUP BY doctor_name, day_of_week, hour
ORDER BY doctor_name, day_of_week, hour;

-- 2. Выручка по месяцам
SELECT
    DATE_TRUNC('month', a.appointment_datetime) AS month,
    SUM(a.price) AS revenue,
    COUNT(*) AS visit_count,
    ROUND(AVG(a.price), 2) AS avg_check
FROM appointments a
WHERE a.status = 'состоялся'
GROUP BY month
ORDER BY month;

-- 3. Топ-5 диагнозов по возрастным группам
WITH age_groups AS (
    SELECT
        a.diagnosis_name,
        CASE
            WHEN EXTRACT(YEAR FROM AGE(a.appointment_datetime, p.birth_date)) < 18 THEN '0-17'
            WHEN EXTRACT(YEAR FROM AGE(a.appointment_datetime, p.birth_date)) < 60 THEN '18-59'
            ELSE '60+'
        END AS age_group,
        COUNT(*) as cnt
    FROM appointments a
    JOIN patients p ON a.patient_id = p.patient_id
    WHERE a.status = 'состоялся' AND a.diagnosis_name IS NOT NULL
    GROUP BY a.diagnosis_name, age_group
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY age_group ORDER BY cnt DESC) AS rn
    FROM age_groups
)
SELECT age_group, diagnosis_name, cnt
FROM ranked
WHERE rn <= 5
ORDER BY age_group, cnt DESC;

-- 4. Когортный анализ удержания пациентов
WITH first_visits AS (
    SELECT
        patient_id,
        DATE_TRUNC('month', MIN(appointment_datetime)) AS cohort_month
    FROM appointments
    WHERE status = 'состоялся'
    GROUP BY patient_id
),
visits AS (
    SELECT
        a.patient_id,
        DATE_TRUNC('month', a.appointment_datetime) AS visit_month
    FROM appointments a
    WHERE a.status = 'состоялся'
    GROUP BY a.patient_id, visit_month
)
SELECT
    fv.cohort_month,
    EXTRACT(MONTH FROM AGE(v.visit_month, fv.cohort_month)) AS month_number,
    COUNT(DISTINCT fv.patient_id) AS total_cohort,
    COUNT(DISTINCT v.patient_id) AS active_patients,
    ROUND(COUNT(DISTINCT v.patient_id) * 100.0 / COUNT(DISTINCT fv.patient_id), 1) AS retention_pct
FROM first_visits fv
LEFT JOIN visits v ON fv.patient_id = v.patient_id AND v.visit_month >= fv.cohort_month
GROUP BY fv.cohort_month, month_number
ORDER BY fv.cohort_month, month_number;

-- 5. Доля неявок по дням недели
SELECT
    EXTRACT(DOW FROM a.appointment_datetime) AS day_of_week,
    COUNT(*) AS total_appointments,
    SUM(CASE WHEN a.status = 'неявка' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(SUM(CASE WHEN a.status = 'неявка' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS no_show_pct
FROM appointments a
GROUP BY day_of_week
ORDER BY day_of_week;