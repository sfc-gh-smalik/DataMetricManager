import streamlit as st
from snowflake.snowpark import Session


def set_session_params():

    if 'custom_associated' not in st.session_state:
        st.session_state['custom_associated'] = False

    if 'new_custom_schedule' not in st.session_state:
        st.session_state['new_custom_schedule'] = ''

    if 'test_placeholder' not in st.session_state:
        st.session_state['test_placeholder'] = ''

    if 'selected_table_reporting' not in st.session_state:
        st.session_state['selected_table_reporting'] = ''

    if 'f_q_custom_dmf' not in st.session_state:
        st.session_state['f_q_custom_dmf'] = ''

    if 'f_q_table_name' not in st.session_state:
        st.session_state['f_q_table_name'] = ''

    if 'assoc_custom_dmf' not in st.session_state:
        st.session_state['assoc_custom_dmf'] = False

    if 'cr_custom_dmf' not in st.session_state:
        st.session_state['cr_custom_dmf'] = False

    if 'custom_dmf_validated' not in st.session_state:
        st.session_state['custom_dmf_validated'] = False

    if 'custom_dmf_option' not in st.session_state:
        st.session_state['custom_dmf_option'] = ''

    if 'custom_dmf_create' in st.session_state:
        st.session_state['custom_dmf_create'] = False

    if 'validated' not in st.session_state:
        st.session_state['validated'] = False

    if 'scheduled' not in st.session_state:
        st.session_state['scheduled'] = False

    if 'applied' not in st.session_state:
        st.session_state['applied'] = False

    if 'create_alert' not in st.session_state:
        st.session_state['create_alert'] = False

    if 'system_selected_table' not in st.session_state:
        st.session_state['system_selected_table'] = ''

    if 'system_selected_columns' not in st.session_state:
        st.session_state['system_selected_columns'] = []

    if 'custom_selected_table' not in st.session_state:
        st.session_state['custom_selected_table'] = ''

    if 'custom_selected_columns' not in st.session_state:
        st.session_state['custom_selected_columns'] = []

    if 'columns_with_types' not in st.session_state:
        st.session_state['columns_with_types'] = {}

    if 'selected_system_dmf' not in st.session_state:
        st.session_state['selected_system_dmf'] = []

    if 'system_selected_schema' not in st.session_state:
        st.session_state['system_selected_schema'] = []

    if 'system_selected_db' not in st.session_state:
        st.session_state['system_selected_db'] = []

    if 'custom_selected_schema' not in st.session_state:
        st.session_state['custom_selected_schema'] = []

    if 'custom_selected_db' not in st.session_state:
        st.session_state['custom_selected_db'] = []

    if 'custom_dmf_name' not in st.session_state:
        st.session_state['custom_dmf_name'] = ''

    if 'custom_validated' not in st.session_state:
        st.session_state['custom_validated'] = False

    if 'custom_scheduled' not in st.session_state:
        st.session_state['custom_scheduled'] = False

    if 'existing_dmf' not in st.session_state:
        st.session_state['existing_dmf'] = False

    if 'dmf_schedule' not in st.session_state:
        st.session_state['dmf_schedule'] = ''


DATABASE = "DATA_METRICS_DB"
SCHEMA = "DQ"
STAGE = "DMF_FILES"

DMF_LOG_TABLE = "DATA_METRICS_DB.DQ.DMF_ASSOCIATIONS"

total_steps = 3
step_labels = ["Test DMF", "Schedule", "Associate DMF"]

adjust_streamlit_style = """
<style>
.st-emotion-cache-1p2amu 
{max-width: 60rem;}
</style>

"""

set_session_params()
