# Streamlit app


## Description
This repo has 3 components: 
- An API using FastAPI to serve as a mimmic for the backend API. It is defined in the API_endpoints.py and helper_fonctions.py files. It use the data in the data folder. The returned models are defined in models.py.
- A python client in generated client that as its own readme. It was generated using "openapi-python-client generate --url <API_URL>/openapi.json --output-path ./generated_client"
- A streamlit app using the client defined in dashboard.py that render a interactiv dashboard of the data behind the API


## Installation
- install poetry:
```bash
pip install poetry
```

- use you favorite tool to create a virtual env (if you don't do anything, poetry will do it) and activate it.
For example:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

- install the dependancies (-no-root as it is not yet packageable)
```bash
poetry install --no-root
```

## Usage
- activate your virtual environment 
With poetry: 
```bash
poetry env activate
```
That will give you the command to activate the env. It is of the form "source somepath/bin/activate"

- API setup:
```bash
fastapi dev API_endpoints.py
```
create a new terminal as the 2 servers need to be running at the same time. Note that the streamlit server can be run before, the call to the API append only when a page is requested to the streamlit server.

- Streamlit app:

In the new terminal, activate the virtual environment again:
```bash
source .venv/bin/activate
```
    
Set the environment variables with API URL and authentication URL:
```bash
export API_URL=<API_URL>
export API_AUTH_URL=<API_AUTH_ENDPOINT_URL>
```
Then, run the Streamlit app:
```bash
streamlit run dashboard.py --server.port <dashboard_port> --server.address <dashboard_ip_address>
```

Example:
```bash
export API_URL="http://127.0.0.1:8000"
export API_AUTH_URL="http://127.0.0.1:8000/token"
streamlit run dashboard.py --server.port 8501 --server.address 127.0.0.1
```

Now the frontend is accessible from your web browser at the specified IP address and port and will use the API endpoints specified.

- Authentication for Dashboard:

After opening the frontend dashboard, you will need to enter a username and password. Two sets of pre-configured username and password are provided for access:
```
"username": "bob"
"password": "secret"
```
```
"username": "alice"
"password": "secret2"
```


## Integration to the EDGAR data warehouse

The API created here is meant to mimic the FastAPI API of the warehouse.
The main point is the streamlit app. It can have is own container, with the IP addresses and ports parameterizable with command lines.
It requests the user for its gitlab credentials to authenticate to the API.
It is meant to be accessible without any previous authentication, either by exposing the container port, or by adding and redirecting to it an unsecure endpoint of the API.