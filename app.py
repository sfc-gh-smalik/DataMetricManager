from snowflake.snowpark.context import get_active_session
import Stepper as stp
from utils import prefixed_key, set_png_as_page_bg, dmf_types, get_db_schema_details, system_dmfs, render_object_selection, display_notification,is_dmf_compatile, clear_container, reset_app
from SystemDMFs import apply_dmf, log_dmf, get_table_dmfs, schedule_dmf, test_dmf
from alerts import create_alert, render_alert_objects
from __init__ import total_steps, step_labels, adjust_streamlit_style
from CustomDMFs import create_custom_dmf, test_custom_dmf, get_custom_dmf, schedule_custom_dmf, associate_custom_dmf
from dmfReport import dmfReport
from styling import stylable_container, card, button_right
import streamlit as st
import time

# Import following custom libraries Packages -> Stage Packages where DATA_METRICS_DB.DQ.DMF_FILES is your Stage location
# DATA_METRICS_DB.DQ.DMF_FILES/styling.py
# DATA_METRICS_DB.DQ.DMF_FILES/dmfReport.py
# DATA_METRICS_DB.DQ.DMF_FILES/CustomDMFs.py
# DATA_METRICS_DB.DQ.DMF_FILES/SystemDMFs.py
# DATA_METRICS_DB.DQ.DMF_FILES/utils.py
# DATA_METRICS_DB.DQ.DMF_FILES/alerts.py
# DATA_METRICS_DB.DQ.DMF_FILES/Stepper.py
# DATA_METRICS_DB.DQ.DMF_FILES/__init__.py


# Get the current Snowflake session
session = get_active_session()
debug = False
prefix = ''
# put the session in State object
st.session_state['session'] = session

schedule_btn = "Set Schedule"
new_schedule = ''
st.set_page_config(layout="centered", page_title="Data Quality Manager")
st.markdown(adjust_streamlit_style, unsafe_allow_html=True)

try:
    set_png_as_page_bg(st.session_state['session'], 'DATA_METRICS_DB.DQ.DMF_FILES', 'iceberg.png')
except Exception as e:
    st.write()

with stylable_container(key="MainBlock", css_styles=card):
    st.title("Data Metric Functions Manager")

page = st.sidebar.selectbox("Choose a page",
                            ["Home", "Create DMF", "Create Alerts", "View DMF Results"])
st.session_state['stepper'] = stp.Stepper(total_steps, step_labels, height=-10)

if debug:
    with st.sidebar.expander(label="Session State"):
        st.write(st.session_state)

if page == 'Home':
    with stylable_container(key="MainBlock", css_styles=card):
        st.header("Snowflake Data Quality Manager")
        st.subheader("Choose options from the left hand side navigation menu.")
        st.markdown(
            """
            Welcome to the Snowflake Data Quality Manager App ! Within this application you can do the following tasks:
    
            * Create Data Meteric Functions (**Create DMFs**)
                * System DMFs
                    * Test, Schedule and Associate Data Metric Functions available in the System
                * Custom DMFs
                    * Create Custom Data Metric Functions and define the business logic you would like to validate
            * Check for **Existing Data Metric Functions** you can access via your role and apply them to Snowflake Tables or Columns 
            * **Create Alerts** to detect anomolies or metric violations on existing Data Metric functions associated in the system
            * Configure alerts to be send via email or webhook Integration (Optional)
            * **Reporting** - View Data Metric function results and track 
    
            """
        )

elif page == "Create DMF":
    with stylable_container(key="DMFOptionBlock", css_styles=card):

        # Select DMF Type
        st.header("Select Data Metric Function Type")
        col1, col2 = st.columns(2)
        with col1:
            selected_dmf_type = st.selectbox("Choose DMF Type", dmf_types, index=None, key='selected_dmf_type')

        if selected_dmf_type == "System DMFs":
            with col2:
                selected_system_dmf = st.selectbox("Select System DMF", system_dmfs, index=None,
                                                   key='selected_system_dmf')

    if selected_dmf_type == "Custom DMFs":
        with stylable_container(key="CustomDMFBlock", css_styles=card):

            col1, col2 = st.columns(2)
            with col1:
                cr_custom_dmf = st.toggle('Create Custom DMF', key='cr_custom_dmf',
                                          disabled=st.session_state['assoc_custom_dmf'])
            with col2:
                assoc_custom_dmf = st.toggle('Associate Custom DMF', key='assoc_custom_dmf',
                                             disabled=st.session_state['cr_custom_dmf'])

            if st.session_state['cr_custom_dmf']:
                if get_db_schema_details(st.session_state['session']):
                    create_custom_dmf(st.session_state['session'], st.session_state['stepper'])

        if st.session_state['assoc_custom_dmf']:
            with stylable_container(key="GetCustomDMF", css_styles=card):
                st.subheader("Existing Custom DMF")
                if get_db_schema_details(st.session_state['session']):
                    # get the existing custom DMFs
                    response = get_custom_dmf(st.session_state['session'])

                    if len(response) > 0:
                        col1, _ = st.columns(2)
                        with col1:
                            st.selectbox("Select Custom DMF", response['name'], index=None, key='custom_dmf_name')

        if st.session_state['custom_dmf_name']:
            st.subheader(f"Using Custom DMF: {st.session_state['custom_dmf_name']}")

            # Render Stepper Bar for Reference
            st.session_state['stepper'].render()

            # Display selection to select DB, Schema, Table and Columns to check Custom DMF on..
            render_object_selection(st.session_state['session'], 'custom')

            if not st.session_state['custom_dmf_validated']:
                # Test out the custom DMF before association
                test_custom_dmf(st.session_state['session'], st.session_state['stepper'])

        if st.session_state['custom_dmf_validated'] and not st.session_state['custom_scheduled']:
            # get current associations for the custom DMF selected
            response = get_table_dmfs(st.session_state['session'], st.session_state['custom_selected_db'],
                                      st.session_state['custom_selected_schema'], st.session_state['custom_selected_table'],
                                      st.session_state['custom_selected_columns'], check=False)

            if response:
                with stylable_container(key="ExistingCustomDMF", css_styles=card):
                    st.subheader('Existing Custom DMFs Summary')
                    col1, _ = st.columns([99.9, 0.01])
                    with col1:
                        st.dataframe(response, hide_index=True)

            # Schedule Custom DMF
            schedule_custom_dmf(st.session_state['session'], st.session_state['stepper'])
            st.session_state['custom_scheduled'] = True

        if st.session_state['custom_scheduled'] and not st.session_state['custom_associated']:
            # Apply the custom DMF to the table
            associate_custom_dmf(st.session_state['session'])
            log_dmf(st.session_state['session'], st.session_state['custom_dmf_name'], 'custom')

        if st.session_state['custom_associated']:
            del st.session_state['custom_associated']

            # reset the app
            with st.spinner('Resetting Page !!!'):
                time.sleep(3)
                reset_app(True)

    notification = st.empty()
    if st.session_state['selected_dmf_type'] == "System DMFs" \
            and st.session_state['selected_system_dmf']:
        st.subheader(f"Using System DMF: {st.session_state['selected_system_dmf']}")
        # placeholder for all notification on the app
        placeholder = st.empty()

        st.session_state['stepper'].render()
        render_object_selection(st.session_state['session'])

        if not st.session_state['validated'] and not st.session_state['scheduled'] and (
                len(st.session_state['system_selected_columns']) > 0
                or st.session_state['selected_system_dmf'] == 'ROW_COUNT'):

            with stylable_container(key="TestSystemDMFBtn", css_styles=button_right):
                if st.button("Test System DMF", key='test_system_dmf'):
                    with placeholder.container():
                        try:
                            if (st.session_state['selected_system_dmf'] != 'ROW_COUNT'
                                    and st.session_state['system_selected_columns']):
                                for column in st.session_state['system_selected_columns']:
                                    if is_dmf_compatile(st.session_state['selected_system_dmf'],
                                                        st.session_state['columns_with_types'][column]):
                                        st.session_state[
                                            'f_q_table_name'] = f"{st.session_state['system_selected_db']}.{st.session_state['system_selected_schema']}.{st.session_state['system_selected_table']}"
                                        result = test_dmf(st.session_state['session'],
                                                          st.session_state['selected_system_dmf'],
                                                          st.session_state['f_q_table_name'], column)
                                        display_notification(
                                            f"Test result for {st.session_state['selected_system_dmf']} on column {column}: {result}",
                                            'success')
                                        st.session_state['validated'] = True
                                        st.session_state['stepper'].set_current_step(
                                            st.session_state['stepper'].get_current_step() + 1)
                                    else:
                                        display_notification(
                                            f"System DMF: {selected_dmf_type} is not compatible with column {column} {st.session_state['columns_with_types'][column]}).",
                                            'warning')
                                        st.session_state['validated'] = False
                                clear_container(placeholder)

                            elif st.session_state['selected_system_dmf'] == 'ROW_COUNT':
                                result = 'NA'
                                display_notification(
                                    f"Test result for {st.session_state['selected_system_dmf']} on column {''}: {result}",
                                    'success')
                                st.session_state['validated'] = True
                                st.session_state['stepper'].set_current_step(
                                    st.session_state['stepper'].get_current_step() + 1)
                            else:
                                display_notification(f"Ensure you have selected the columns for DMF", 'info')
                        except Exception as e:
                            display_notification(f"Error testing System DMF: {str(e)}", 'error')

        if st.session_state['validated'] and not st.session_state['scheduled']:
            response = get_table_dmfs(st.session_state['session'], st.session_state['system_selected_db'],
                                      st.session_state['system_selected_schema'],
                                      st.session_state['system_selected_table'], st.session_state['system_selected_columns'])
            if response:
                with stylable_container(key="ExistingSystemDMSummary", css_styles=card):
                    st.subheader('Existing DMFs Summary')
                    col1, _ = st.columns([99.9, 0.01])
                    with col1:
                        st.dataframe(response, hide_index=True)
                schedule_btn = "Change Schedule"

            with stylable_container(key="ScheduleSystemDMFBtn", css_styles=button_right):
                with st.popover(f"{schedule_btn}"):
                    new_schedule = st.text_input(
                        "Enter New Schedule (e.g., '60 minute' or 'USING CRON 0 9 * * * America/New_York or 'TRIGGER_ON_CHANGES'",
                        key='new_schedule')

                    if st.button(f"{schedule_btn}", key='set_schedule'):
                        if st.session_state['new_schedule']:
                            schedule_dmf(st.session_state['session'],
                                         st.session_state['f_q_table_name'],
                                         st.session_state['new_schedule'])
                            st.session_state['stepper'].set_current_step(
                                st.session_state['stepper'].get_current_step() + 1)

        if st.session_state['scheduled'] and not st.session_state['applied']:
            with stylable_container(key="AssociateSystemDMFBtn", css_styles=button_right):
                if st.button("Associate System DMF", key='apply_system_dmf'):
                    apply_dmf(st.session_state['session'],
                              st.session_state['selected_system_dmf'],
                              st.session_state['f_q_table_name'],
                              st.session_state['system_selected_columns'])

                    if st.session_state['applied']:
                        log_dmf(st.session_state['session'], st.session_state['selected_system_dmf'], 'system')

        if st.session_state['applied']:
            # del st.session_state['applied']

            with st.spinner('Resetting Page !!!'):
                time.sleep(3)
                reset_app(True)

elif page == "View DMF Results":
    dmfReport()

elif page == "Create Alerts":

    with stylable_container(key="CreateAlertMain", css_styles=card):
        st.subheader('Create Alerts on Existing DMFs')

    with stylable_container(key="CreateAlert", css_styles=card):
        col1, col2 = st.columns(2)

        with col1:
            selected_dmf_type = st.selectbox("Choose DMF Type", dmf_types, index=None, key='selected_dmf_type')

        if selected_dmf_type == "System DMFs":
            prefix = 'system'
            with col2:
                selected_system_dmf = st.selectbox("Select System DMF", system_dmfs, index=None,
                                                   key='selected_system_dmf')

        elif selected_dmf_type == "Custom DMFs":
            st.subheader("Custom DMF")
            prefix = 'custom'

    placeholder = st.empty()
    notification = st.empty()

    if selected_dmf_type:
        render_object_selection(st.session_state['session'], prefix)

    if selected_dmf_type and all(
            [st.session_state[prefixed_key(prefix, 'selected_db')],
             st.session_state[prefixed_key(prefix, 'selected_schema')],
             st.session_state[prefixed_key(prefix, 'selected_table')],
             st.session_state[prefixed_key(prefix, 'selected_columns')]]
    ):
        response = get_table_dmfs(st.session_state['session'], st.session_state[prefixed_key(prefix, 'selected_db')],
                                  st.session_state[prefixed_key(prefix, 'selected_schema')],
                                  st.session_state[prefixed_key(prefix, 'selected_table')],
                                  st.session_state[prefixed_key(prefix, 'selected_columns')],
                                  source='Alerts')

        if response:
            with stylable_container(key="CreateAlertDMFSummary", css_styles=card):
                st.header("Table DMFs Summary")
                col1, _ = st.columns([99.9, 0.01])
                with col1:
                    st.dataframe(response)
        else:
            st.session_state['existing_dmf'] = False

    if st.checkbox("Create Alert", key='create_alert', disabled=(not st.session_state['existing_dmf'])):

        is_complete = render_alert_objects()

        if is_complete:
            with stylable_container(key="CreateAlertCode", css_styles=card):
                with st.expander('Alert Statement'):
                    st.code(create_alert(st.session_state['session'],
                                         st.session_state['alert_name'],
                                         st.session_state[prefixed_key(prefix, 'selected_table')],
                                         st.session_state[prefixed_key(prefix, 'selected_columns')],
                                         st.session_state['selected_system_dmf'],
                                         st.session_state['threshold'],
                                         st.session_state['operator'],
                                         st.session_state['alert_schedule'],
                                         st.session_state['email']))

    
        with stylable_container(key="CreateAlertBtn", css_styles=button_right):
            if st.button('Create', key='create_alert_btn', disabled =(not is_complete)):
                status = create_alert(st.session_state['session'],
                                      st.session_state['alert_name'],
                                      st.session_state[prefixed_key(prefix, 'selected_table')],
                                      st.session_state[prefixed_key(prefix, 'selected_columns')],
                                      st.session_state['selected_system_dmf'],
                                      st.session_state['threshold'],
                                      st.session_state['operator'],
                                      st.session_state['alert_schedule'],
                                      st.session_state['email'], True)

                if status[0]:
                    display_notification(status[1], 'success')
                else:
                    display_notification(status[1], 'error')
                del st.session_state['create_alert']
                with st.spinner('Resetting Page !!!'):
                    time.sleep(2)
                    reset_app(True)
