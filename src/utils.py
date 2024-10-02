import time
import streamlit as st
from streamlit.components.v1 import html
import base64
from styling import *
from __init__ import set_session_params

dmf_types = [
    "System DMFs",
    "Custom DMFs"]

system_dmfs = [
    "FRESHNESS",
    "DATA_METRIC_SCHEDULED_TIME",
    "NULL_COUNT",
    "DUPLICATE_COUNT",
    "UNIQUE_COUNT",
    "ROW_COUNT",
    "BLANK_COUNT",
    "BLANK_PERCENT",
    "AVG",
    "MIN",
    "MAX",
    "NULL_PERCENT",
    "STDDEV"
]

compatibility = {
    "FRESHNESS": ["TIMESTAMP_LTZ", "DATE", "TIMESTAMP_TZ"],
    "DATA_METRIC_SCHEDULED_TIME": ["TIMESTAMP", "DATE"],
    "NULL_COUNT": ["DATE", "FLOAT", "NUMBER", "TIMESTAMP_LTZ", "TIMESTAMP_NTZ", "TIMESTAMP_TZ", "VARCHAR"],
    "DUPLICATE_COUNT": ["DATE", "FLOAT", "NUMBER", "TIMESTAMP_LTZ", "TIMESTAMP_NTZ", "TIMESTAMP_TZ", "VARCHAR"],
    "UNIQUE_COUNT": ["DATE", "FLOAT", "NUMBER", "TIMESTAMP_LTZ", "TIMESTAMP_NTZ", "TIMESTAMP_TZ", "VARCHAR"],
    "ROW_COUNT": ["ALL"],
    "AVG": ["FLOAT", "NUMBER"],
    "BLANK_PERCENT": ["NUMBER"],
    "MAX": ["FLOAT", "NUMBER"],
    "MIN": ["FLOAT", "NUMBER"],
    "NULL_PERCENT": ["DATE", "FLOAT", "NUMBER", "TIMESTAMP_LTZ", "TIMESTAMP_NTZ", "TIMESTAMP_TZ", "VARCHAR"],
    "STDDEV": ["FLOAT", "NUMBER"],
    "BLANK_COUNT": ["NUMBER"]
}


def prefixed_key(prefix, key):
    return '_'.join([prefix, key])


def has_value(val):
    if val is None:
        return False
    elif isinstance(val, str):
        return True if len(val) > 0 else False
    elif isinstance(val, int):
        return True if val != None else False
    elif isinstance(val, list):
        return True if len(val) > 0 else False


@st.cache_data
def create_card_container():
    css = """
        <style>
        .card {
            border: 1px solid #f0f0f0;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            background-color: #ffffff;
            box-shadow: 0 4x 8px rgba(0, 0, 0, 0.1);
            transition: box-shadow 03.s ease-in-out;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)
    # create a unique id for the card
    card_id = f"card_{id(create_card_container)}"
    # Open the container
    html(f"<div id='{card_id}', class='card'>", height=0)
    container = st.container()
    # returnn the container and a function to close the card
    return container, lambda: html("</div>", height=0)


# Function to check if a DMF is compatible with a column data type
def is_dmf_compatile(dmf_name, data_type):
    # Define compatibility rules
    if dmf_name in compatibility:
        return "ALL" in compatibility[dmf_name] or any(dtype in data_type.upper() for dtype in compatibility[dmf_name])

    return False  # For custom DMFs, assume compatibility


def filter_compatible_col(columns, data_types, dmf_name):
    compatible_columns = []
    compatible_types = compatibility[dmf_name]

    for column, data_type in zip(columns, data_types):
        data_type = data_type.upper()
        if 'ALL' in compatible_types or any(compatible_type in data_type for compatible_type in compatible_types):
            compatible_columns.append(column)

    return compatible_columns


def re_test():
    if 'scheduled' in st.session_state:
        st.session_state['scheduled'] = False
    if 'validated' in st.session_state:
        st.session_state['validated'] = False
    if 'custom_scheduled' in st.session_state:
        st.session_state['custom_scheduled'] = False
    if 'custom_dmf_validated' in st.session_state:
        st.session_state['custom_dmf_validated'] = False

    st.session_state['stepper'].set_current_step(st.session_state['stepper'].get_current_step() - 1)


def reset_app(rerun=False):
    for key in st.session_state.keys():
        # don't clear the session from the state when resetting the app
        if key != 'session':
            del st.session_state[key]
    set_session_params()

    if rerun:
        st.rerun()


def display_notification(msg, type):
    if type == 'success':
        alert = st.success(msg)
    elif type == 'error':
        alert = st.error(msg)
    elif type == 'warning':
        alert = st.warning(msg)
    else:
        alert = st.info(msg)

    time.sleep(2)  # Wait for X seconds
    alert.empty()  # Clear the alert


# clear alert message
def clear_container(placeholder, t_secs=3):
    time.sleep(t_secs)
    placeholder.empty()


# Function to get table columns
@st.cache_data
def get_table_columns(_session, f_q_table_name, selected_dmf):
    if selected_dmf != 'ROW_COUNT':
        columns = _session.sql(f"DESCRIBE TABLE {f_q_table_name}").collect()
        return {col['name']: col['type'].split('(')[0] for col in columns}
    else:
        return {}


def get_db_schema_details(session, object_list=None):
    """Return True when both Database and Schema are selected and object_list is Null"""
    if object_list is None:
        object_list = ['DB', 'SCHEMA']
    col1, col2 = st.columns(2)
    with col1:
        if 'DB' in object_list:
            dbs = session.sql("SHOW DATABASES").collect()
            db_names = [db_name['name'] for db_name in dbs]
            custom_dmf_db = st.selectbox("Select Database", db_names, on_change=re_test, index=None,
                                         key='custom_dmf_db')
    with col2:
        if 'SCHEMA' in object_list:
            if st.session_state['custom_dmf_db']:
                schemas = session.sql(f"""SHOW SCHEMAS IN DATABASE {custom_dmf_db}""").collect()
                selected_schema = [schema_name['name'] for schema_name in schemas]
                custom_dmf_schema = st.selectbox("Select Schema", selected_schema, on_change=re_test, index=None,
                                                 key='custom_dmf_schema')
    return True if st.session_state['custom_dmf_db'] and st.session_state['custom_dmf_schema'] else False


def render_object_selection(session, dmf_type='system'):
    with stylable_container(
            key="render_object_selection",
            css_styles=card
    ):
        col1, col2 = st.columns(2)
        with col1:
            db_key_value = '_'.join([dmf_type, 'selected_db'])
            databases = session.sql("SHOW DATABASES").collect()
            db_names = [db_name['name'] for db_name in databases]
            selected_db = st.selectbox("Select Database", db_names, on_change=re_test, index=None, key=db_key_value)

        with col2:
            if st.session_state[db_key_value]:
                sch_key_value = '_'.join([dmf_type, 'selected_schema'])
                schemas = session.sql(f"""SHOW SCHEMAS IN DATABASE {selected_db}""").collect()
                selected_schema = [schema_name['name'] for schema_name in schemas]
                selected_schema = st.selectbox("Select Schema", selected_schema, on_change=re_test, index=None,
                                               key=sch_key_value)

        try:
            if st.session_state[db_key_value] and st.session_state[sch_key_value]:
                col1, col2 = st.columns(2)
                with col1:
                    try:
                        tbl_key_value = '_'.join([dmf_type, 'selected_table'])
                        tables = session.sql(
                            f"""SHOW TABLES IN SCHEMA {st.session_state[db_key_value]}.{st.session_state[sch_key_value]}""").collect()
                        table_names = [table['name'] for table in tables]
                        selected_table = st.selectbox("Select Table", table_names, on_change=re_test, index=None,
                                                      key=tbl_key_value)

                        if st.session_state[tbl_key_value]:
                            val = True if dmf_type == 'custom' else False
                            st.checkbox('Show Compatible columns', key='Compatible_columns', disabled=val)
                    except Exception as e:
                        selected_table = ''
                        display_notification(
                            f"No tables found for {selected_db} {st.session_state[sch_key_value]} "
                            f"or you are not authorized. Try another combination. {str(e)}",
                            'info')
                with col2:
                    if selected_table:
                        col_key_value = '_'.join([dmf_type, 'selected_columns'])

                        # Get Columns for the selected table
                        f_q_table_name = f"""{st.session_state[db_key_value]}.{st.session_state[sch_key_value]}.{selected_table}"""
                        st.session_state['columns_with_types'] = get_table_columns(session, f_q_table_name,
                                                                                   st.session_state[
                                                                                       'selected_system_dmf'])

                        if st.session_state['Compatible_columns'] and not dmf_type == 'custom':
                            compatibile_cols = filter_compatible_col(st.session_state['columns_with_types'].keys(),
                                                                     st.session_state['columns_with_types'].values(),
                                                                     st.session_state['selected_system_dmf']
                                                                     )

                            selected_columns = st.multiselect("Select Columns",
                                                              compatibile_cols,
                                                              on_change=re_test, key=col_key_value)

                        else:
                            selected_columns = st.multiselect("Select Columns",
                                                              list(st.session_state['columns_with_types'].keys()),
                                                              on_change=re_test, key=col_key_value)

        except Exception as e:
            st.error(f"Error Unhandled: {str(e)}")


def set_png_as_page_bg(session, f_q_stage_path, image_name):
    """DATABASE = "DEMODB"
       SCHEMA = "DEV"
       STAGE = "BG_IMAGE"
      #image_name = 'app_background.png'
      image_name = 'snowflake.png'
      set_png_as_page_bg(session, image_name)"""
    
    # Get the Image Name and convert it to Streamlit app backgound
    # session.file.get(f"@{DATABASE}.{SCHEMA}.{STAGE}/{image_name}", f"/tmp")
    session.file.get(f"@{f_q_stage_path}/{image_name}", f"/tmp")
    mime_type = image_name.split('.')[-1:][0].lower()
    with open(f"/tmp/" + image_name, "rb") as f:
        content_bytes = f.read()
    content_b64encoded = base64.b64encode(content_bytes).decode()
    image_string = f'data:image/{mime_type};base64,{content_b64encoded}'

    page_bg_img = f'''
        <style>
        .stApp {{
            background-image: url("{image_string}");
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
        '''
    st.markdown(page_bg_img, unsafe_allow_html=True)
