import streamlit as st
from utils import display_notification, prefixed_key
from __init__ import DMF_LOG_TABLE
from snowflake.snowpark.functions import col


# Function to test DMF
def test_dmf(session, dmf_name, f_q_table_name, column_name):
    try:
        if column_name:
            result = session.sql(f"""
                        SELECT SNOWFLAKE.CORE.{dmf_name}(
                            SELECT {column_name}
                            FROM {f_q_table_name}
                        )
                        """).collect()
            return result[0][0]
    except Exception as e:
        return f"Error Testing DMF: {str(e)}"


def apply_dmf(session, selected_system_dmf, selected_table, selected_columns):
    try:
        if selected_system_dmf != 'ROW_COUNT':
            for column in selected_columns:
                session.sql(f"""ALTER TABLE {selected_table}
                ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.{selected_system_dmf} ON ({column})
                """).collect()
        elif selected_system_dmf == 'ROW_COUNT':
            session.sql(f"""ALTER TABLE {selected_table}
                ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.{selected_system_dmf} ON ()
                """).collect()

        display_notification(
            f"System DMF '{selected_system_dmf}' applied to column(s) {selected_columns} in {selected_table} successfully!",
            'success')
        st.session_state['applied'] = True
    except Exception as e:
        display_notification(f"Error associating System DMF: {str(e)}", 'error')


def log_dmf(session, metric_name, dmf_type):
    # METRIC_NAME, REF_DATABASE_NAME, REF_SCHEMA_NAME,REF_ENTITY_NAME,REF_ENTITY_DOMAIN,DOMAIN,APPLIED_TO,SCHEDULE,SCHEDULE_STATUS
    prefix = 'custom' if dmf_type == 'custom' else 'system'

    if metric_name == 'ROW_COUNT':
        domain = ''
        applied_to = ''
    else:
        domain = 'COLUMN'
        applied_to = st.session_state[prefixed_key(prefix, 'selected_columns')]

    if len(applied_to) > 0:
        for column in applied_to:
            if not get_table_dmfs(st.session_state[prefixed_key(prefix, 'selected_db')],
                                  st.session_state[prefixed_key(prefix, 'selected_schema')],
                                  st.session_state[prefixed_key(prefix, 'selected_table')], column, check=True):
                try:
                    dmf_log_sql = f"""INSERT INTO {DMF_LOG_TABLE} VALUES ( '{metric_name}', 
                    '{st.session_state[prefixed_key(prefix, 'selected_db')]}', 
                    '{st.session_state[prefixed_key(prefix, 'selected_schema')]}',
                    '{st.session_state[prefixed_key(prefix, 'selected_table')]}','TABLE',
                    '{domain}','{column}','{st.session_state['dmf_schedule']}','STARTED')"""

                    session.sql(dmf_log_sql).collect()
                    # st.write(dmf_log_sql)
                except Exception as e:
                    display_notification(f"Error logging a DMF record: {str(e)}", 'error')


def schedule_dmf(session, selected_table, new_schedule):
    try:
        session.sql(f"""
        ALTER TABLE {selected_table}
        SET DATA_METRIC_SCHEDULE = '{new_schedule}'
        """).collect()
        display_notification(f"Table:'{selected_table}' scheduled with {new_schedule} successfully!", 'success')

        st.session_state['scheduled'] = True
        st.session_state['dmf_schedule'] = new_schedule
    except Exception as e:
        display_notification(f"Error scheduling DMF: {str(e)}", 'error')


@st.cache_data
def get_table_dmfs(_session, db_name, schema_name, table_name, column_names='', check=False, source=None):
    try:
        # enable support for DATA_METRIC_FUNCTION_REFERENCES in future once avaialable in SiS
        # table_dmfs = session.sql(f"""SELECT * FROM TABLE(
        #                             INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES(
        #                               REF_ENTITY_NAME => '{db_name}.{schema_name}.{table_name}',
        #                               REF_ENTITY_DOMAIN => 'table'
        #                             )
        #                           )""").collect()

        if isinstance(column_names, list):
            columns = "','".join(column_names)
        else:
            columns = column_names

        len_cols = len(column_names)

        table_dmfs = _session.sql(f"""SELECT DISTINCT * FROM {DMF_LOG_TABLE}
        WHERE REF_DATABASE_NAME = '{db_name}' AND REF_SCHEMA_NAME = '{schema_name}'
        AND  REF_ENTITY_NAME = '{table_name}'AND ( ((CASE WHEN DOMAIN = 'COLUMN' THEN TRUE END) 
        AND APPLIED_TO in ('{columns}')) OR ({len_cols} = 0)) """).collect()

        # enable support for DATA_METRIC_FUNCTION_REFERENCES in future once avaialable in SiS
        # table_dmfs = session.sql(f"""SELECT METRIC_NAME, REF_DATABASE_NAME, REF_SCHEMA_NAME,REF_ENTITY_NAME,REF_ENTITY_DOMAIN,
        #                              GET(parse_json(REF_ARGUMENTS[0]),'domain')::STRING as DOMAIN,
        #                              GET(parse_json(REF_ARGUMENTS[0]),'name')::STRING as APPLIED_TO,
        #                              SCHEDULE,SCHEDULE_STATUS
        #                              FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_METRIC_FUNCTION_REFERENCES
        #                              WHERE REF_DATABASE_NAME = '{db_name}'
        #                              AND REF_SCHEMA_NAME = '{schema_name}'
        #                              AND  REF_ENTITY_NAME = '{table_name}'
        #                              AND ( ((CASE WHEN DOMAIN = 'COLUMN' THEN TRUE END) AND APPLIED_TO in ('{columns}'))
        #                                OR ({len_cols} = 0)
        #                           )""").collect()

        if check:
            return True if table_dmfs else False

        if table_dmfs:
            if len(column_names) != len(table_dmfs):
                if source == 'Alerts':
                    display_notification(
                        f"DMF association doesn't exist for all selected columns, "
                        f"alert will be created for associated table/column(s) only",
                        'warning')
                else:
                    display_notification(
                        f"DMF association doesn't exist for all selected columns, "
                        f"existing associations will be skipped if you choose to continue",
                        'warning')
            else:
                if source is None:
                    display_notification(
                        f"DMF for this combination is already associated with the table. "
                        f"Please select another combination",
                        'info')

            st.session_state['existing_dmf'] = True
            return table_dmfs
        else:
            display_notification(
                f'No existing DMFs found for the combination.',
                'info')
            return None
    except Exception as e:
        display_notification(f"Error getting table DMFs: {str(e)}", 'error')


def get_existing_dmfs(session, selected_table, selected_columns):
    try:
        existing_dmfs = session.sql(f"""SELECT DATA_METRIC_FUNCTION_NAME 
            FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_METRIC_FUNCTIONS WHERE TABLE_NAME = '{selected_table}'
            AND COLUMN_NAME = '{selected_columns}' """).collect()

        if existing_dmfs:
            existing_dmf_names = [dmf['DATA_METRIC_FUNCTION_NAME'] for dmf in existing_dmfs]
            selected_existing_dmf = st.selectbox("Selecting Existing DMF", existing_dmf_names)
        else:
            st.write(f'No existing DMFs or authorized to access for the current role')
    except Exception as e:
        st.error(f"Error getting schedule for existing DMFs: {str(e)}")


def get_dmf_results(session, start_date, end_date):
    results = session.table("SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS")
    results = results.filter((col("MEASUREMENT_TIME") >= start_date) & (col("MEASUREMENT_TIME") <= end_date))
    return results.collect()


def remove_dmf_association(session, selected_dmf, selected_table, selected_columns):
    try:
        session.sql(f"ALTER TABLE {selected_table} DROP DATA METRIC FUNCTION {selected_dmf} ON ({selected_columns}); ")
        return True, f"Data Metric Function '{selected_dmf}' dropped successfully."
    except Exception as e:
        return False, (f"Error removing DMF Association from the Table {selected_table} "
                       f"on columns {selected_columns}: {str(e)}")
