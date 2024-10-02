import streamlit as st
from utils import has_value


def render_alert_objects():
    col1, col2 = st.columns(2)
    with col1:
        alert_name = st.text_input("Alert Name", key='alert_name')
    with col2:
        comparison_operator = st.selectbox("Comparison Operator", ['=', '<', '>', '<=', '>=', '!='], index=None,
                                           key='operator')

    col1, col2 = st.columns(2)
    with col1:
        threshold = st.number_input("Threshold", value=None, min_value=0, step=1, key='threshold')
    with col2:
        email_address = st.text_input("Email Address", key='email')

    schedule = st.text_input("Enter New Schedule (e.g., '1 Minute' or 'USING CRON 0 9 * * * America/New_York",
                             key='alert_schedule')

    return all([has_value(alert_name), has_value(comparison_operator), has_value(schedule), has_value(email_address), has_value(st.session_state['threshold'])])


def create_alert(session, alert_name, table_name, column_names, metric_name, threshold, comparison_operator, schedule,
                 email_address, execute=False):
    try:
        query_string = '('
        for column in column_names:
            query_string += f"ARRAY_CONTAINS('{column}'::VARIANT,ARGUMENT_NAMES) \n OR "

        query_string = query_string.rstrip(' OR')
        query_string += ')'

        alert_sql = f"""
        CREATE OR REPLACE ALERT {alert_name}\n
        SCHEDULE = '{schedule}'\n
        IF (EXISTS (\n
        SELECT 1
        FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS\n
        WHERE TABLE_NAME = '{table_name}'\n
        AND ARRAY_CONTAINS ('COLUMN'::VARIANT,ARGUMENT_TYPES)\n
        AND {query_string}
        AND METRIC_NAME = '{metric_name}'\n
        AND VALUE {comparison_operator} {threshold}\n
        AND MEASUREMENT_TIME >= DATEADD(hour, -1, current_timestamp())\n
        ))\n
        THEN CALL SYSTEM$SEND_EMAIL(\n
        "{email_address}",\n
        "Data Quality Alert",\n
        "Data Quality Issue detected for {table_name}.[{column_names}] using {metric_name}"
        )\n
        """
        if execute:
            session.sql(alert_sql).collect()
            return True, f"Alert '{alert_name}' created successfully!"
        return alert_sql
    except Exception as e:
        return False, f"Error Creating alert: {str(e)}"
