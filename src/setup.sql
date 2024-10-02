use ROLE <your_role>; -- role with privileges to create a Database
CREATE DATABASE DATA_METRICS_DB;
CREATE SCHEMA DATA_METRICS_DB.DQ;

USE SCHEMA DATA_METRICS_DB.DQ;

CREATE OR REPLACE TABLE DATA_METRICS_DB.DQ.DMF_ASSOCIATIONS (
                                                              METRIC_NAME VARCHAR,
                                                              REF_DATABASE_NAME VARCHAR,
                                                              REF_SCHEMA_NAME VARCHAR,
                                                              REF_ENTITY_NAME VARCHAR,
                                                              REF_ENTITY_DOMAIN VARCHAR,
                                                              DOMAIN VARCHAR,
                                                              APPLIED_TO VARCHAR,
                                                              SCHEDULE VARCHAR,
                                                              SCHEDULE_STATUS VARCHAR);

INSERT INTO DATA_METRICS_DB.DQ.DMF_ASSOCIATIONS
SELECT METRIC_NAME, REF_DATABASE_NAME, REF_SCHEMA_NAME,REF_ENTITY_NAME,REF_ENTITY_DOMAIN,
GET(parse_json(REF_ARGUMENTS[0]),'domain')::STRING as domain,
GET(parse_json(REF_ARGUMENTS[0]),'name')::STRING as applied_to,
SCHEDULE,SCHEDULE_STATUS FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_METRIC_FUNCTION_REFERENCES;


-- Stage to upload files and use in Streamlit Application
CREATE STAGE DATA_METRICS_DB.DQ.DMF_FILES 
	DIRECTORY = ( ENABLE = true );
  

-- Grants (Optional) if not already provisioned by your accountadmin
use role accountadmin; -- or custom role with privileges

1. GRANT APPLICATION ROLE SNOWFLAKE.DATA_QUALITY_MONITORING_VIEWER TO ROLE <your role>;
--OR
2. GRANT DATABASE ROLE SNOWFLAKE.USAGE_VIEWER TO ROLE <your role>;
--OR
3. GRANT DATABASE ROLE SNOWFLAKE.DATA_METRIC_USER TO ROLE <your role>;

-- GRANTS to execute Alerts in Account
use role accountadmin; -- or custom role with privileges
GRANT EXECUTE MANAGED ALERT ON ACCOUNT TO ROLE <your role>;

-- Grant to create DATA METRIC FUNCTIONS in ACCOUNT
GRANT CREATE DATA METRIC FUNCTION ON ACCOUNT TO ROLE <your role>;
GRANT EXECUTE DATA METRIC FUNCTION ON ACCOUNT TO ROLE <your role>;


-- Example grant for existing DATA METRIC FUNCTION 
-- Create the secure DMF to validate emails
CREATE OR REPLACE DATA METRIC FUNCTION validate_email(users TABLE (EMAIL VARCHAR))  
RETURNS NUMBER COMMENT='Returns count of invalid email addresses in given rows'
AS
$$
   SELECT COUNT(*) FROM users WHERE LENGTH(EMAIL) > 254 OR NOT REGEXP_LIKE(EMAIL, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
$$;

GRANT USAGE on FUNCTION TESTING.DMF_PII.VALIDATE_EMAIL(varchar) to role <your role>;

-- ******Important*****
-- replace the table name in __init__ as fully qualified name
-- DMF_LOG_TABLE = "DATA_METRICS_DB.DQ.DMF_ASSOCIATIONS"
