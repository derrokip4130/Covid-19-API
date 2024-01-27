# COVID CONVERSATIONAL AI BACKEND

API endpoints for covid conversational bot on SAP

## INITIAL SETUP

### Configuring Postgres

    CREATE USER covidbot with ENCRYPTED PASSWORD 'covidBotPass';

    CREATE DATABASE coviddb WITH OWNER covidbot;


### Import Data

    python manage.py db_dump << path/to/dataset/covid_dataset.csv >>


## API REFERENCE

### Example Calls

Get all data where cured cases are greater than or equal to 300,000

    curl 'http://127.0.0.1:8000/cases/?field_name=cured&query=gte&value=300000'

    'http://127.0.0.1:8000/?operation=sum&field_name=death&state=YourState&start_date=2023-01-01&end_date=2023-12-31'

Get all data where deaths are less than 10

    curl 'http://127.0.0.1:8000/cases/?field_name=death&query=lt&value=10'

`field_name` can be one of `date`, `state`, `tcin`, `tcfn`, `cured`, `death`


`query` must be [any valid Django field lookup](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#field-lookups) for the specified `field_name`


`value` can be:

    1. A number when `field_name` is one of the following: `tcin`, `tcfn`, `cured` and `death`
    2. A string when `field_name` is `state`
    3. A date string in the format `YYYY-MM-DD` when `field_name` is `date`

