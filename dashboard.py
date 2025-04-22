import streamlit as st
import pandas as pd
import plotly.express as px
import httpx
import os
from typing import Union

from generated_client.fast_api_client import AuthenticatedClient
from generated_client.fast_api_client.types import Response
from generated_client.fast_api_client.api.default import list_ride_dashboard_rides_get, get_gps_data_dashboard_gps_get, get_ride_data_dashboard_ride_name_get


# Get the API URL and authentication URL from environment variables
api_url = os.getenv("API_URL", "http://127.0.0.1:8000/")
api_auth_url = os.getenv("API_AUTH_URL", "http://127.0.0.1:8000/token")

st.session_state.api_url = api_url
st.session_state.api_auth_url = api_auth_url 

# authentification
# function to get the token from the API
def get_token(username: str, password: str, token_url: str) -> str:
    response = httpx.post(
        token_url,
        data={
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    return response.json()["access_token"]

def check_response(response: Response) -> Union[dict, list]:
    if response.status_code != 200:
        st.session_state.authenticated = False
        st.error(f"Error: {response.status_code} - {response.content.decode()}")
        st.stop()
    return response.parsed
    

if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.write("Please log in using gitlab credentials")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        if submit_button:
            try:
                token = get_token(username, password, st.session_state.api_auth_url)
                st.session_state.authenticated = True
                st.session_state.token = token
                st.success("Login successful")
                st.rerun()
            except httpx.HTTPStatusError:
                st.error("Invalid username or password")
                st.stop()
        else:
            st.stop()
    

client = AuthenticatedClient(
    base_url=st.session_state.api_url,
    verify_ssl=True,
    token=st.session_state.token,
)

# Get the data from the API for the overview
with client as client:
    # List rides
    rides = check_response(list_ride_dashboard_rides_get.sync_detailed(client=client))
    
    # Get GPS data
    gps_data = check_response(get_gps_data_dashboard_gps_get.sync_detailed(client=client))
    
    # Sample data for demonstration
    num_rides = len(rides)
    num_scenes = sum(ride['num_scenes'] for ride in rides)
    num_samples = sum(ride['num_samples'] for ride in rides)
    total_duration = sum(ride['duration'] for ride in rides) / 60  # assuming duration is in seconds
    total_distance = sum(ride['distance'] for ride in rides)

    # Calculate average metrics
    avg_scenes_per_ride = num_scenes / num_rides if num_rides else 0
    avg_samples_per_ride = num_samples / num_rides if num_rides else 0
    avg_distance_per_ride = total_distance / num_rides if num_rides else 0
    avg_duration_per_ride = total_duration / num_rides if num_rides else 0

    # Define a function to render the navigation bar
    def navigation_bar():
        st.sidebar.title("Navigation")
        if st.sidebar.button("Overview"):
            st.session_state.page = "overview"
        if st.sidebar.button("Rides"):
            st.session_state.page = "rides"


    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "overview"

    # Render the navigation bar
    navigation_bar()


    if st.session_state.page == "overview":
        # 1. Streamlit Dashboard Title
        st.title("Streamlit Dashboard")

        # Create two columns: One for the "Summary of Important Metrics" and one for "Average Metrics"
        col1, col2 = st.columns(2)

        with col1:
            # 2. Summary of the Most Important Metrics
            st.header("Summary of Important Metrics")

            # Use st.columns within col1 to align metrics in rows
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric(label="Number of rides", value=num_rides)
                st.metric(label="Number of scenes", value=num_scenes)
                st.metric(label="Number of samples", value=num_samples)
            with metric_col2:
                st.metric(label="Total driven duration", value= total_duration)
                st.metric(label="Total distance in km", value=total_distance)

        with col2:
            # 3. Average Metrics Section
            st.header("Average Metrics")

            # Use st.columns within col2 to align metrics in rows
            avg_metric_col1, avg_metric_col2 = st.columns(2)
            with avg_metric_col1:
                st.metric(label="Average scenes per ride", value=round(avg_scenes_per_ride, 2))
                st.metric(label="Average samples per ride", value=round(avg_samples_per_ride, 2))
            with avg_metric_col2:
                st.metric(label="Average distance of a ride (km)", value=round(avg_distance_per_ride, 2))
                st.metric(label="Average duration of a ride (min)", value=round(avg_duration_per_ride, 2))

        # Show the number of rides over time.
        # Convert the list of rides to a DataFrame
        rides_df = pd.DataFrame(rides)
        # Group by 'date' and count the number of rides for each date
        rides_count_df = rides_df.groupby('date').size().reset_index(name='Rides')
        # Rename the columns for clarity
        rides_count_df.columns = ['Time', 'Rides']
        # create Line graph.
        fig = px.bar(rides_count_df, x='Time', y='Rides', title='Rides over Time')
        st.plotly_chart(fig, use_container_width=True)

        # 4. GPS Overview Section
        st.header("GPS Overview")

        # Scatter plot example
        scatter_fig = px.scatter_map(
            pd.DataFrame(gps_data), lat="Latitude", lon="Longitude",
            zoom=12,
            map_style="open-street-map"
        )
        st.plotly_chart(scatter_fig, use_container_width=True)

        # 5. Heatmap Section
        st.header("Heatmap")

        # Heatmap example
        heatmap_fig = px.density_map(
            pd.DataFrame(gps_data), lat="Latitude", lon="Longitude",
            radius=10, center=dict(lat=48.137154, lon=11.576124),
            map_style="open-street-map"
        )
        st.plotly_chart(heatmap_fig, use_container_width=True)

    elif st.session_state.page == "rides":
        st.title("Rides")

        # Function to sort data
        def sort_rides(data, sort_by, order):
            return sorted(data, key=lambda x: x[sort_by], reverse=(order == "descending"))

        # Search bar
        search_query = st.text_input("Search for rides...", key="ride_search")

        # Filters
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            sort_by = st.selectbox("Sort by", ["scenes", "samples", "duration", "distance"], key="sort_by")
        with col2:
            sort_order = st.selectbox("Select order", ["ascending", "descending"], key="sort_order")
        with col3:
            sort_button = st.button("Sort")
        with col4:
            reset_button = st.button("Reset all filters")

        # Reset functionality
        if reset_button:
            del(st.session_state["ride_search"])
            st.session_state["ride_search"] = ""
            del(st.session_state["sort_by"])
            st.session_state["sort_by"] = "scenes"
            del(st.session_state["sort_order"])
            st.session_state["sort_order"] = "ascending"

        # Filtering and sorting
        translation_dict = {"scenes": "num_scenes", "samples": "num_samples", "duration": "duration", "distance": "distance"} # Mapping for sorting
        filtered_rides = rides
        if search_query:
            filtered_rides = [ride for ride in rides if search_query.lower() in ride["name"].lower()]
        if sort_button:
            filtered_rides = sort_rides(filtered_rides, translation_dict[st.session_state["sort_by"]], st.session_state["sort_order"])

        # 'details_visible' should be initialized for each ride
        if 'details_visible' not in st.session_state:
            st.session_state.details_visible = {ride['name']: False for ride in rides} # dict with ride name as key and False as the details of none have been loaded
            
        # Initialize the ride_details state
        if 'ride_details' not in st.session_state:
            st.session_state.ride_details = {} # dict to store the details of the rides

        # Display rides with buttons
        st.write("### Available Rides")
        for ride in filtered_rides:
            with st.container():
                details_visible = st.session_state.details_visible[ride['name']]

                # Create a button for each ride
                if st.button(f"{ride['name']}: {ride['num_scenes']} Scenes - {ride['num_samples']} Examples - "
                            f"Duration: {ride['duration']} - Distance: {ride['distance']} m",
                            key=f"btn_{ride['name']}"):
                    st.session_state.details_visible[ride['name']] = not details_visible

                # If details are visible, show them
                if st.session_state.details_visible[ride['name']]:
                    # Check if ride details are already fetched
                    if ride['name'] not in st.session_state.ride_details:
                        # Request the ride data from the API
                        ride_details = check_response(get_ride_data_dashboard_ride_name_get.sync_detailed(client=client, ride_name=ride['name']))
                        # Store the fetched data in the session state
                        st.session_state.ride_details[ride['name']] = ride_details
                    else:
                        # Use the stored data
                        ride_details = st.session_state.ride_details[ride['name']]
                        
                        
                    # Display main ride details
                    st.write(f"**Name of the Ride:** {ride_details['name']}")
                    st.write("---")
                    st.write("### Ride Details")
                    with st.container():
                        st.write(f"- **Date**: {ride_details['date']}")
                        st.write(f"- **Time**: {ride_details['time']}")
                        st.write(f"- **Number of Scenes**: {ride_details['num_scenes']}")
                        st.write(f"- **Number of Samples**: {ride_details['num_samples']}")
                        st.write(f"- **Duration**: {ride_details['duration']}")
                        st.write(f"- **Distance**: {ride_details['distance']} m")

                    # Scene filter
                    st.write("### Filter: Select Scenes")
                    available_scenes = [f"Scene {i + 1}" for i in range(ride_details["num_scenes"])]
                    selected_scene = st.selectbox("Scenes", ["All Scenes"] + available_scenes, key=f"filter_{ride_details['name']}")

                    # Display GPS information
                    st.write("### GPS Information")
                    gps_coordinates = ride_details["gps_coordinates"]  # Default to full ride data
                    if selected_scene != "All Scenes":
                        # Filter GPS data based on the selected scene
                        st.write(f"Displaying GPS data for {selected_scene}.")

                    # GPS Map (scatter plot equivalent)
                    scatter_fig = px.scatter_map(
                        lat=[coord[0] for coord in gps_coordinates],  # Latitude
                        lon=[coord[1] for coord in gps_coordinates],  # Longitude
                        zoom=12, map_style="open-street-map",
                        title=f"GPS Information for {ride_details['name']}"
                    )
                    st.plotly_chart(scatter_fig, use_container_width=True)

                    # GPS Heatmap
                    st.write("### GPS Heatmap")
                    heatmap_fig = px.density_map(
                        lat=[coord[0] for coord in ride_details["gps_heatmap_data"]],  # Extract latitudes from the gps_heatmap_data
                        lon=[coord[1] for coord in ride_details["gps_heatmap_data"]],  # Extract longitudes from the gps_heatmap_data
                        radius=10,  # Adjust the radius of the heatmap points
                        center=dict(lat=ride_details["gps_heatmap_data"][0][0], lon=ride_details["gps_heatmap_data"][0][1]),
                        # Center the map based on the first data point
                        map_style="open-street-map",  # Use a basic map style
                        title=f"GPS Heatmap for {ride_details['name']}"
                    )
                    st.plotly_chart(heatmap_fig, use_container_width=True)

