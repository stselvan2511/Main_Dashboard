import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import graphviz

# Load the dataset
@st.cache_data
def load_data():
    data = pd.read_excel(r'Data/_Water_Consumption_Dataset_.xlsx')
    data['Time'] = pd.to_datetime(data['Time'])
    # Drop unnamed columns and the 'Anomalous' column if present
    data = data.loc[:, ~data.columns.str.contains('^Unnamed')]
    if 'Anomalous' in data.columns:
        data = data.drop(columns=['Anomalous'])
    return data

data = load_data()

# Extract year, month, and day from 'Time' and add them as separate columns
data['Year'] = data['Time'].dt.year
data['Month'] = data['Time'].dt.month
data['Day'] = data['Time'].dt.day

# Sidebar filters
st.sidebar.header("Filter Data")

def multi_select_with_all(label, options, default=None):
    st.sidebar.write(label)
    all_selected = st.sidebar.checkbox(f"Select All {label}", value=False)
    if all_selected:
        selected = options
    else:
        selected = st.sidebar.multiselect(f"Select {label}", options, default=default)
    return selected

# Get unique values for filters
unique_ids = data['User_ID'].unique()
unique_area_codes = data['Area_Code'].unique()
unique_device_ids = data['Device_ID'].unique()
unique_water_usage = data['Water_Usage'].unique()
unique_years = data['Year'].unique()
unique_months = data['Month'].unique()
unique_days = data['Day'].unique()

# Filter options with select all functionality
selected_id = multi_select_with_all("User ID", unique_ids)
selected_area_code = multi_select_with_all("Area Code", unique_area_codes)
selected_device_id = multi_select_with_all("Device ID", unique_device_ids)
selected_water_usage = multi_select_with_all("Water Usage", unique_water_usage)
selected_year = multi_select_with_all("Year", unique_years)
selected_month = multi_select_with_all("Month", unique_months)
selected_day = multi_select_with_all("Day", unique_days)

# Filter data based on selections
filtered_data = data.copy()

if selected_id:
    filtered_data = filtered_data[filtered_data['User_ID'].isin(selected_id)]
if selected_area_code:
    filtered_data = filtered_data[filtered_data['Area_Code'].isin(selected_area_code)]
if selected_device_id:
    filtered_data = filtered_data[filtered_data['Device_ID'].isin(selected_device_id)]
if selected_water_usage:
    filtered_data = filtered_data[filtered_data['Water_Usage'].isin(selected_water_usage)]
if selected_year:
    filtered_data = filtered_data[filtered_data['Year'].isin(selected_year)]
if selected_month:
    filtered_data = filtered_data[filtered_data['Month'].isin(selected_month)]
if selected_day:
    filtered_data = filtered_data[filtered_data['Day'].isin(selected_day)]

# Compute Leakage Values
filtered_data['Leakage'] = filtered_data['Monthly_Water_Consumption'] * 0.05

# Display filtered data
st.title("Water Consumption Analysis Dashboard")
st.write(f"Showing {filtered_data.shape[0]} rows of filtered data.")
st.dataframe(filtered_data)

# Water Distribution Flowchart Visualization using Graphviz
st.header("Water Distribution Flowchart")

dot = graphviz.Digraph(comment='Water Distribution Network', engine='dot')

# Set graph size and font sizes
dot.attr(size='12,8', ratio='fill', fontsize='0.5')  # Adjusted for potential speed improvement

# Define the Water Tank and Main Device
dot.node('Water_Tank', 'Water Tank', shape='box', style='filled', color='lightblue', fontsize='0.5')
dot.node('Main_Device', 'Main Device', shape='box', style='filled', color='purple', fontsize='0.5')

# Define the Pipelines and Areas
for i in range(1, 5):
    dot.node(f'Pipeline_{i}', f'Pipeline {i}', shape='box', style='filled', color='lightyellow', fontsize='0.5')
    dot.node(f'Area_{i}', f'Area {i}', shape='box', style='filled', color='lightpink', fontsize='0.5')

# Define the Users and Devices
for i in range(1, 13):
    dot.node(f'User_{i}', f'User {i}', shape='ellipse', style='filled', color='lightgray', fontsize='0.5')
    dot.node(f'Device_{i}', f'Device {i}', shape='ellipse', style='filled', color='orange', fontsize='0.5')

# Connect Water Tank to Main Device
dot.edge('Water_Tank', 'Main_Device')

# Connect Main Device to Pipelines
for i in range(1, 5):
    dot.edge('Main_Device', f'Pipeline_{i}')

# Connect Pipelines to Areas
for i in range(1, 5):
    dot.edge(f'Pipeline_{i}', f'Area_{i}')

# Connect Areas to Users and Users to Devices
user_idx = 1
for i in range(1, 5):
    for j in range(3):
        dot.edge(f'Area_{i}', f'User_{user_idx}')
        dot.edge(f'User_{user_idx}', f'Device_{user_idx}')
        user_idx += 1

# Render and display the Graphviz graph
st.graphviz_chart(dot)

# Animated Scatter Plot: Water Consumption Analysis
st.header("Animated Scatter Plot: Water Consumption Over Time")

# Ensure positive values for log scaling
filtered_data['Monthly_Water_Consumption'] = filtered_data['Monthly_Water_Consumption'].apply(lambda x: x if x > 0 else 1e-5)
filtered_data['Daily_Water_Consumption'] = filtered_data['Daily_Water_Consumption'].apply(lambda x: x if x > 0 else 1e-5)

fig_scatter_animation = px.scatter(
    filtered_data,
    x='Monthly_Water_Consumption',
    y='Daily_Water_Consumption',
    animation_frame='Time',
    animation_group='User_ID',
    size='Daily_Water_Consumption',
    color='User_ID',
    hover_name='User_ID',
    log_x=True,
    size_max=55,
    range_x=[filtered_data['Monthly_Water_Consumption'].min(), filtered_data['Monthly_Water_Consumption'].max()],
    range_y=[filtered_data['Daily_Water_Consumption'].min(), filtered_data['Daily_Water_Consumption'].max()],
    title='Animated Scatter Plot of Water Consumption Over Time'
)

fig_scatter_animation.update_layout(
    xaxis_title="Monthly Water Consumption (Liters)",
    yaxis_title="Daily Water Consumption (Liters)",
    transition={'duration': 3000}  # Set animation duration to 3 seconds
)
st.plotly_chart(fig_scatter_animation, use_container_width=True)

# Animated Bar Chart: Total Monthly Water Consumption by Area Code
st.header("Animated Bar Chart: Monthly Water Consumption by Area Code")

monthly_consumption = filtered_data.groupby(['Time', 'Area_Code'])['Monthly_Water_Consumption'].sum().reset_index()

fig_bar_animation = px.bar(
    monthly_consumption,
    x='Area_Code',
    y='Monthly_Water_Consumption',
    color='Area_Code',
    animation_frame='Time',
    range_y=[0, monthly_consumption['Monthly_Water_Consumption'].max() * 1.1],
    title='Animated Bar Chart of Monthly Water Consumption by Area Code'
)

fig_bar_animation.update_layout(
    xaxis_title="Area Code",
    yaxis_title="Monthly Water Consumption (Liters)",
    transition={'duration': 3000}  # Set animation duration to 3 seconds
)
st.plotly_chart(fig_bar_animation, use_container_width=True)

# Improved Distribution Chart: Violin Plot for Daily Water Consumption by Usage Type
st.header("Violin Plot for Daily Water Consumption by Usage Type")
fig_violin = px.violin(filtered_data, y='Daily_Water_Consumption', color='Water_Usage', box=True, points="all",
                       title='Distribution of Daily Water Consumption by Usage Type',
                       labels={'Daily_Water_Consumption': 'Daily Water Consumption (Liters)', 'Water_Usage': 'Usage Type'})
st.plotly_chart(fig_violin, use_container_width=True)

# Stacked Bar Chart for Monthly Consumption Breakdown
st.header("Stacked Bar Chart for Monthly Consumption Breakdown")
monthly_breakdown = filtered_data.groupby(['Month', 'Area_Code'])['Monthly_Water_Consumption'].sum().reset_index()
fig_stacked_bar = px.bar(monthly_breakdown, x='Month', y='Monthly_Water_Consumption', color='Area_Code', title='Monthly Water Consumption Breakdown by Area Code', text='Monthly_Water_Consumption', barmode='stack')
st.plotly_chart(fig_stacked_bar, use_container_width=True)

# Histogram of Hourly Water Consumption by User
st.header("Histogram of Hourly Water Consumption by User")
fig_histogram = px.histogram(filtered_data, x='Hourly_Water_Consumption', color='User_ID', title='Histogram of Hourly Water Consumption by User', nbins=50)
st.plotly_chart(fig_histogram, use_container_width=True)

# Leakage Chart: Monthly Leakage by Area Code
st.header("Monthly Leakage by Area Code")

# Aggregate leakage by area code and time
leakage_data = filtered_data.groupby(['Time', 'Area_Code'])['Leakage'].sum().reset_index()

fig_leakage = px.bar(
    leakage_data,
    x='Area_Code',
    y='Leakage',
    color='Area_Code',
    animation_frame='Time',
    range_y=[0, leakage_data['Leakage'].max() * 1.1],
    title='Monthly Leakage by Area Code'
)

fig_leakage.update_layout(
    xaxis_title="Area Code",
    yaxis_title="Leakage (Liters)",
    transition={'duration': 3000}  # Set animation duration to 3 seconds
)
st.plotly_chart(fig_leakage, use_container_width=True)
