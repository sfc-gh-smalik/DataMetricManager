import streamlit as st
from utils import *
from SystemDMFs import schedule_dmf
import pandas as pd


def get_custom_dmf(session):
    try:
        if st.session_state['custom_dmf_db']:
            existing_dmfs = session.sql(f"""SHOW DATA METRIC FUNCTIONS IN SCHEMA 
            {st.session_state['custom_dmf_db']}.{st.session_state['custom_dmf_schema']}""").collect()

            existing_dmfs = pd.DataFrame(existing_dmfs)
            if len(existing_dmfs) > 0:
                return existing_dmfs[['schema_name', 'name']].drop_duplicates()
            else:
                display_notification(f"No Custom DMFs found in Schema "
                                     f"{st.session_state['custom_dmf_db']}.{st.session_state['custom_dmf_schema']}",
                                     'info')
                return pd.DataFrame()
    except Exception as e:
        st.error(f"Error getting existing custom DMFs in Database {st.session_state['custom_dmf_db']} : {str(e)}")


def create_custom_dmf(session, stepper):
    st.subheader("Create Custom DMF")

    with stylable_container(
            key="customDMF",
            css_styles=card
    ):
        if st.session_state['custom_dmf_db'] and st.session_state['custom_dmf_schema']:
            col1, col2 = st.columns(2)
            with col1:
                custom_dmf_name = st.text_input("Custom DMF Name", key='custom_dmf_name')
            with col2:
                dmf_description = st.text_area("DMF Description", key='dmf_description')

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Input Parameters")
                num_params = st.number_input("Number of Input parameters", min_value=1, value=1, key='num_params')
                st.session_state['params'] = []

            for i in range(st.session_state['num_params']):
                col1, col2 = st.columns(2)

                with col1:
                    param_name = st.text_input(f"Parameter {i + 1} Name")

                with col2:
                    param_type = st.selectbox(f"Parameter {i + 1} Type", ["NUMBER", "VARCHAR", "DATE", "BOOLEAN"])
                st.session_state['params'].append({"name": param_name, "type": param_type})

            col1, col2 = st.columns(2)

            with col1:
                table_arg = st.text_input(f"Table Parameter", value="ARG_T", disabled=True, key='table_param')

            with col2:
                return_type = st.selectbox("Return Type", ["NUMBER", "VARCHAR", "DATE", "BOOLEAN"], key='return_type')

            col1, col2 = st.columns([99.9, 0.01])
            with col1:
                dmf_sql = st.text_area("SQL Definition", height=200, key='dmf_sql')

            if all([st.session_state['dmf_sql'],
                    st.session_state['custom_dmf_name'],
                    st.session_state['params']
                    ]):
                param_str = ", ".join([f"{p['name']} {p['type']}" for p in st.session_state['params']])
                dmf_query = f"""
                CREATE OR REPLACE DATA METRIC FUNCTION {st.session_state['custom_dmf_db']}.{st.session_state['custom_dmf_schema']}.{st.session_state['custom_dmf_name']} 
                ( {st.session_state['table_param']} TABLE ({param_str} ))
                RETURNS {st.session_state['return_type']}
                AS
                    '{st.session_state['dmf_sql']}'
                """
                with st.expander("Preview Custom DMF"):
                    st.code(dmf_query)

                if st.button("Create Custom DMF"):
                    try:
                        session.sql(dmf_query).collect()
                        st.session_state['custom_dmf_create'] = True
                        display_notification(f"Custom DMF {st.session_state['custom_dmf_name']} created successfully!",
                                             'success')
                    except Exception as e:
                        st.error(f"Error creating Custom DMF: {str(e)}")


def test_custom_dmf(session, stepper):
    st.session_state['test_placeholder'] = st.empty()
    with st.session_state['test_placeholder'].container():
        with stylable_container(
                key="TestCustomDMF",
                css_styles=button_right
        ):
            if st.button("Test Custom DMF"):
                try:
                    st.session_state['f_q_custom_dmf'] = f"{st.session_state['custom_dmf_db']}.{st.session_state['custom_dmf_schema']}.{st.session_state['custom_dmf_name']}"
                    st.session_state['f_q_table_name'] = f"{st.session_state['custom_selected_db']}.{st.session_state['custom_selected_schema']}.{st.session_state['custom_selected_table']}"
                    if st.session_state['custom_dmf_name'] and st.session_state['custom_selected_table']:
                        dmf_columns = ','.join(st.session_state['custom_selected_columns'])

                        for column in st.session_state['custom_selected_columns']:
                            result = session.sql(f"""
                            SELECT {st.session_state['f_q_custom_dmf']}(
                            SELECT {column}
                            FROM {st.session_state['f_q_table_name']}
                            )
                            """).collect()

                        display_notification(
                            f"{st.session_state['f_q_custom_dmf']} for {st.session_state['custom_selected_columns']} in "
                            f"{st.session_state['f_q_table_name']}: {result[0][0]}", 'success')
                        st.session_state['custom_dmf_validated'] = True
                        stepper.set_current_step(stepper.get_current_step() + 1)
                except Exception as e:
                    display_notification(f"Error testing Custom DMF: {str(e)}", 'error')


def schedule_custom_dmf(session, stepper) -> None:
    if st.session_state['custom_dmf_validated'] and not st.session_state['custom_scheduled']:
        with stylable_container(key="ScheduleCustomDMF", css_styles=button_right):
            with st.popover("Set Schedule"):
                # get_table_dmfs(custom_selected_db, custom_selected_schema, custom_selected_table)
                new_custom_schedule = st.text_input(
                    "Enter New Schedule (e.g., '60 minute' or 'USING CRON 0 9 * * * America/New_York or 'TRIGGER_ON_CHANGES'",
                    key='new_custom_schedule')

                if st.button("Save Schedule", key='set_custom_schedule'):
                    # get_existing_dmfs(custom_selected_table, custom_selected_columns)
                    if st.session_state['new_custom_schedule']:

                        schedule_dmf(st.session_state['session'],
                                     st.session_state['f_q_table_name'],
                                     st.session_state['new_custom_schedule']
                                     )
                        stepper.set_current_step(stepper.get_current_step() + 1)


def associate_custom_dmf(session) -> None:
    # if table is scheduled for custom DMF, Associate DMF on table columns
    if st.session_state['custom_scheduled']:
        dmf_columns = ','.join(st.session_state['custom_selected_columns'])
        apply_dmf_sql = f"""
                            ALTER table {st.session_state['f_q_table_name']}
                            ADD DATA METRIC FUNCTION {st.session_state['f_q_custom_dmf']}
                            ON ({dmf_columns})
                                """

        with stylable_container(
                key="CustomDMFAssocCode",
                css_styles=card
        ):
            with st.expander("Custom DMF Definition"):
                st.code(apply_dmf_sql, language="sql")

        with stylable_container(
                key="AssociateCustomDMF",
                css_styles=button_right
        ):
            if st.button("Associate Custom DMF"):
                session.sql(apply_dmf_sql).collect()
                display_notification(
                    f"Custom DMF {st.session_state['custom_dmf_name']} applied successfully "
                    f"on table {st.session_state['custom_selected_table']}!",
                    'success')
                st.session_state['custom_associated'] = True
