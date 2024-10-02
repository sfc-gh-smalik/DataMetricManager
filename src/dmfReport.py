import streamlit as st
import pandas as pd
import altair as alt
from utils import display_notification
from styling import *


def get_custom_dmf_sig():
    with stylable_container(
            key="MainBlock",
            css_styles=card
    ):
        # Display DMF details
        st.subheader("Custom DMF Details")

        dmfs = get_dmfs()
        if not dmfs.empty:
            with stylable_container(
                    key="CustomDMFSig",
                    css_styles=card
            ):
                df = dmfs[['created_on', 'catalog_name', 'schema_name', 'name']]
                st.dataframe(df, hide_index=True)
        else:
            display_notification("No Data Metric Functions found.", 'info')

        # Allow users to view DMF definition
        if not dmfs.empty:
            col1, _ = st.columns(2)
            with col1:
                selected_dmf = st.selectbox("Select DMF to view definition", dmfs['name'].unique())
            dmf_args = dmfs['arguments'].to_string(index=False).split('RETURN')[0]
            dmf_desc_query = f"DESC FUNCTION {st.session_state['selected_db_reporting']}.{st.session_state['selected_schema_reporting']}.{dmf_args} "

            dmf_desc = st.session_state['session'].sql(dmf_desc_query).collect()

            if dmf_desc:
                col1, _ = st.columns([99.9, 0.01])
                with col1:
                    st.code(dmf_desc[3]['value'], language='sql')
            else:
                display_notification("Unable to retrieve DMF definition.", 'info')


def get_dmf_details(dmf_name):
    query = f"""SELECT * FROM TABLE(INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES(METRIC_NAME => '{dmf_name}'))"""
    return pd.DataFrame(st.session_state['session'].sql(query).collect())


def get_dmf_associations(table_name, selected_table_dmf):
    query = f"""SELECT * FROM TABLE(INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES(
    REF_ENTITY_NAME => '{selected_table_dmf}',
    REF_ENTITY_DOMAIN => '{table_name}'
    ))"""
    return pd.DataFrame(st.session_state['session'].sql(query).collect())


def get_dmfs():
    query = f"SHOW DATA METRIC FUNCTIONS IN DATABASE {st.session_state['selected_db_reporting']}"
    return pd.DataFrame(st.session_state['session'].sql(query).collect())


def get_tables(database, schema):
    query = f"SHOW TABLES in SCHEMA {database}.{schema}"
    return [row['name'] for row in st.session_state['session'].sql(query).collect()]


def get_dmf_results(session, table_name=None):
    query = f"""SELECT scheduled_time, measurement_time, table_name, argument_names[0]::STRING as column_name, metric_name, value
                FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
                WHERE TABLE_DATABASE = '{st.session_state['selected_db_reporting']}'
            """

    if table_name:
        query = query + f""" AND TABLE_NAME = '{table_name}'"""
        query += f""" ORDER BY measurement_time DESC LIMIT 1000"""

        return pd.DataFrame(session.sql(query).collect())


def dmfReport():
    st.subheader("Data Metric Functions Reporting")

    st.sidebar.header("Filters")

    dbs = st.session_state['session'].sql(f"SHOW DATABASES").collect()
    db_names = [db_name['name'] for db_name in dbs]
    selected_db = st.sidebar.selectbox("Select Database", db_names, key='selected_db_reporting')

    schemas = st.session_state['session'].sql(f"SHOW SCHEMAS IN DATABASE {selected_db}").collect()
    selected_schemas = [schema_name['name'] for schema_name in schemas]
    selected_schema = st.sidebar.selectbox("Select Schema", selected_schemas, key='selected_schema_reporting')

    tables = get_tables(selected_db, selected_schema)
    if len(tables) > 0:
        selected_table = st.sidebar.selectbox("Select Table", ["All"] + tables, index=None,
                                              key='selected_table_reporting')
    elif len(tables) == 0:
        display_notification(f"No tables found for selected Database and Schema", 'info')

    # Get DMF results
    if st.session_state['selected_table_reporting'] == "All":
        df = get_dmf_results(st.session_state['session'])
    else:
        df = get_dmf_results(st.session_state['session'], st.session_state['selected_table_reporting'])

    if st.session_state['selected_table_reporting']:
        # Display results
        if len(df) == 0 or df.empty:
            display_notification("No DMF results found for the selected criteria.", 'info')
        else:
            with stylable_container(
                    key="DMFReporting",
                    css_styles=card
            ):
                st.subheader("Data Metric Function Results")
                metric_names = df['METRIC_NAME'].unique()
                selected_metric = st.sidebar.multiselect("Select Metrics", metric_names, default=metric_names)

                # filtered dataframe
                filtered_df = df[df['METRIC_NAME'].isin(selected_metric)]

                with stylable_container(
                        key="Visualizations",
                        css_styles=card
                ):
                    # Visualizations
                    st.subheader("Visualizations")
                dot_plot = st.toggle('Dot plot Graph')

                if dot_plot:
                    chart = alt.Chart(filtered_df).mark_circle(size=100).encode(
                        x=alt.X('MEASUREMENT_TIME:T', title='Measurement Time'),
                        y=alt.Y('VALUE:Q', title='Value'),
                        color=alt.Color('METRIC_NAME:N', legend=alt.Legend(title='Metric Name')),
                        tooltip=['MEASUREMENT_TIME', 'METRIC_NAME', 'VALUE']
                    ).configure_legend(orient='right').interactive(
                    ).configure_view(strokeWidth=0).configure_axis(grid=True)

                    with stylable_container(
                            key="ReportingLineGraph",
                            css_styles=card
                    ):
                        st.altair_chart(chart, use_container_width=True)

                col1, _ = st.columns([99.9, 0.01])
                with col1:
                    # Bar Chart of average metric value
                    try:
                        bar_chart = alt.Chart(filtered_df).mark_bar().encode(
                            x=alt.X('MEASUREMENT_TIME:T', title='Measurement Time'),
                            y=alt.Y('VALUE:Q', title='Metric Value'),
                            color=alt.Color('METRIC_NAME:N', scale=alt.Scale(scheme='category10'),
                                            legend=alt.Legend(title='Metric Name')),
                            tooltip=['MEASUREMENT_TIME', 'VALUE']
                        ).properties(title='Metric by Measurement Time').configure_legend(orient='right').configure_view(
                            strokeWidth=0).configure_axis(grid=True)

                        with stylable_container(
                                key="ReportingLineGraph",
                                css_styles=card
                        ):
                            st.altair_chart(bar_chart, use_container_width=True)

                        with st.expander("Show Measurement Details", expanded=False):
                            st.dataframe(filtered_df.reset_index(drop=True), hide_index=True)

                    except Exception as e:
                        display_notification(f"Bar Graph not available at the moment due to {str(e)}", 'info')

                # Show the DMF Signature if a Custom DMF
                get_custom_dmf_sig()
