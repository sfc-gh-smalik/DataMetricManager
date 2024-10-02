# Data Metric Manager

**Setting Up the Environment**

First, ensure you have the necessary privileges and connections set up in Snowflake
For creating ALERTs in Snowflake you'll need:
1. **EXECUTE ALERT** privilege on the account
2. **USAGE** and **CREATE ALERT** privileges on the schema
3. **USAGE** privilege on the database, schema and warehouse

For **DATA METRIC FUNCTIONS** you'll need:

1. **CREATE DATA METRIC FUNCTION**: This privilege is required on the schema where you want to create the DMF
2. **EXECUTE DATA METRIC FUNCTION**: This is a global (account-level) privilege that enables using serverless compute resources when calling a DMF
3. **USAGE**: This privilege is needed on the data metric function itself to enable calling the DMF
4. For managing access to DMF results check the available access options [**here**](https://docs.snowflake.com/en/user-guide/data-quality-working#managing-access-to-the-dmf-results)

Log into your Snowflake account as run the setup script to create a dedicated Database, Schema and required objects [**setup.sql**](https://github.com/sfc-gh-smalik/DataMetricManager/blob/main/src/setup.sql)
  - Load all the files from the [**src**](https://github.com/sfc-gh-smalik/DataMetricManager/tree/main/src) folder into the Snowflake **STAGE** (**DMF_FILES**)
  - Navigate to Snowsight -> Projects -> Streamlit
  - Create a new Streamlit App (Choose Database, Schema and Warehouse to run the streamlit app)
  - Copy the [**app.py**](https://github.com/sfc-gh-smalik/DataMetricManager/blob/main/src/__init__.py) code and paste in the newly created Streamlit app


  
  _More detailed access setup control example can be found [here](https://docs.snowflake.com/en/user-guide/tutorials/data-quality-tutorial-start#access-control-setup)_



- Navigate to Packages -> Custom Packages in the Streamlit App and
- Import the python files uploaded to the Stage in your Streamlit App

  Example - @DATA_METRICS_DB.DQ.DMF_FILES/__init__.py

  <img width="280" alt="image" src="https://github.com/user-attachments/assets/91c3f19b-9cd0-4194-ba75-a4decd2d0501">

- Run the Streamlit app and you are all set..!!!

  <img width="1642" alt="image" src="https://github.com/user-attachments/assets/e1d9bfa2-4984-44bc-99b5-b87fa4d08293">

