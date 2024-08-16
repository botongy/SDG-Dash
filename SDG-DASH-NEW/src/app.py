import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from pymongo import MongoClient
import pandas as pd

# MongoDB connection
client = MongoClient('mongodb+srv://botongyuan00:Wojiaoybt1220@cluster0.okmf3dv.mongodb.net/')
db = client['SDG']
collection = db['Apple']

# Fetch data from MongoDB
data = list(collection.find())
df = pd.DataFrame(data)

# Convert the 'Timestamp' to datetime for filtering
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Determine the default date range for the time-series analysis
latest_date = df['Timestamp'].max()
default_end_date = latest_date.date()
default_start_date = (latest_date - pd.DateOffset(years=1)).date()

# Initialize the Dash app
external_stylesheets = ['assets/style.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "Company Visualization Dashboard"
server = app.server

# Define the layout for the main dashboard page
def main_layout():
    return html.Div(children=[
        html.H1("Company SDG Statistics", style={'textAlign': 'center', 'color': 'white'}),
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='company-dropdown',
                    options=[{'label': company, 'value': company} for company in df['Company_Name'].unique()],
                    value=df['Company_Name'].unique()[0],
                    className='custom-dropdown'
                )
            ], style={'flex': '1', 'padding': '20px'}),

            html.Div([
                html.Label('Select Date:', style={'color': 'white', 'fontSize': '18px'}),
                dcc.DatePickerSingle(
                    id='date-picker',
                    min_date_allowed=df['Timestamp'].min().date(),
                    max_date_allowed=df['Timestamp'].max().date(),
                    date=df['Timestamp'].max().date(),
                    display_format='YYYY-MM-DD',
                    style={'display': 'inline-block', 'marginLeft': '10px'}
                )
            ], style={'flex': '1', 'padding': '20px', 'textAlign': 'center'})
        ], style={'display': 'flex', 'justify-content': 'space-between'}),

        html.Div(id='company-info'),
        html.Div(id='mean-scores', style={'padding': '20px', 'display': 'flex', 'justify-content': 'space-around'}),
        html.Div([
            html.Div([dcc.Graph(id='gauge-graph-1')], className='graph-container', style={'flex': '1'}),
            html.Div([dcc.Graph(id='gauge-graph-2')], className='graph-container', style={'flex': '1'}),
            html.Div([dcc.Graph(id='sdg-graph')], className='graph-container', style={'flex': '1'})
        ], style={'display': 'flex', 'justify-content': 'space-around', 'padding': '20px'})
    ])

# Define the layout for the time-series analysis page
def time_series_layout():
    return html.Div(children=[
        html.H1("Time-Series Analysis", style={'textAlign': 'center', 'color': 'white'}),
        html.Div([
            html.Label('Select Date Range:', style={'color': 'white', 'fontSize': '18px'}),
            dcc.DatePickerRange(
                id='date-range-picker',
                min_date_allowed=df['Timestamp'].min().date(),
                max_date_allowed=df['Timestamp'].max().date(),
                start_date=default_start_date,
                end_date=default_end_date,
                display_format='YYYY-MM-DD',
                style={'display': 'inline-block', 'marginLeft': '10px'}
            )
        ], style={'display': 'flex', 'alignItems': 'center', 'padding': '20px'}),
        html.Div([
            html.H3("Short-term Score (STS) Over Time", style={'color': 'white', 'textAlign': 'center'}),
            dcc.Graph(id='sts-mean-timeseries-graph')
        ], style={'padding': '20px'}),
        html.Div([
            html.H3("Overall SDG Sentiment Over Time", style={'color': 'white', 'textAlign': 'center'}),
            dcc.Graph(id='sdg-mean-timeseries-graph')
        ], style={'padding': '20px'})
    ])

# App layout with header and page content
app.layout = html.Div([
    html.Div([
        dcc.Link('SDG Stats Dashboard', href='/', style={'padding': '40px', 'text-decoration': 'none', 'color': 'white'}),
        dcc.Link('Time-Series Dashboard', href='/timeseries', style={'padding': '40px', 'text-decoration': 'none', 'color': 'white'})
    ], style={'display': 'flex', 'justify-content': 'center', 'backgroundColor': 'black', 'padding': '10px'}),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Callback to control navigation between pages
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/timeseries':
        return time_series_layout()
    else:
        return main_layout()

# Callback for the main dashboard
@app.callback(
    [Output('company-info', 'children'),
     Output('mean-scores', 'children'),
     Output('gauge-graph-1', 'figure'),
     Output('gauge-graph-2', 'figure'),
     Output('sdg-graph', 'figure')],
    [Input('company-dropdown', 'value'),
     Input('date-picker', 'date')]
)
def update_dashboard(selected_company, selected_date):
    selected_date = pd.to_datetime(selected_date).date()
    filtered_df = df[(df['Company_Name'] == selected_company) & (df['Timestamp'].dt.date == selected_date)]

    if not filtered_df.empty:
        company_info = [
            html.H2(selected_company),
            html.P(f"Sector: {filtered_df['GICS Sector'].iloc[0]}"),
            html.P(f"Ticker: {filtered_df['Ticker'].iloc[0]}"),
            html.P(f"Date: {filtered_df['Timestamp'].iloc[0].strftime('%Y-%m-%d')}")
        ]

        sts_mean = filtered_df['STS_Mean'].iloc[0]
        lts_mean = filtered_df['LTS_Mean'].iloc[0]
        sts_overall_mean = df['STS_Mean'].mean()
        lts_overall_mean = df['LTS_Mean'].mean()
        #sdg_mean = filtered_df['SDG_Mean'].iloc[0]

        mean_scores = [
            html.Div([
                html.H3("Short-term Score (STS)"),
                html.P(f"{sts_mean:.4f}", className='score-value')
            ], style={'textAlign': 'center'}),
            html.Div([
                html.H3("Long-term Score (LTS)"),
                html.P(f"{lts_mean:.4f}", className='score-value')
            ], style={'textAlign': 'center'})
        ]

        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sts_overall_mean,
            gauge={
                'axis': {'range': [-3, 3]},
                'bar': {'color': 'rgba(0,0,0,0)', 'thickness': 0.2},
                'threshold': {
                    'line': {'color': 'red' if sts_overall_mean < 0 else 'green', 'width': 6},
                    'thickness': 1,
                    'value': sts_overall_mean
                },
                'steps': [
                    {'range': [-3, 0], 'color': 'rgba(255, 0, 0, 0.3)'},
                    {'range': [0, 3], 'color': 'rgba(0, 255, 0, 0.3)'}
                ],
            },
            name='Overall STS Score'
        ))
        fig2.update_layout(
            title='Overall STS Score',
            paper_bgcolor='black',
            plot_bgcolor='black',
            font=dict(color='white')
        )

        sdg_columns = [f'SDG_{i}' for i in range(1, 18)]
        sdg_values = filtered_df[sdg_columns].iloc[0]
        colors = ['green' if val > 0 else 'red' for val in sdg_values]

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=sdg_columns,
            y=sdg_values,
            name='Specific SDG Values',
            marker_color=colors
        ))
        fig3.update_layout(
            title="Specific SDG Values",
            xaxis_title="SDG",
            yaxis_title="Value",
            paper_bgcolor='black',
            plot_bgcolor='black',
            font=dict(color='white')
        )

        fig4 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=lts_overall_mean,
            gauge={
                'axis': {'range': [-3, 3]},
                'bar': {'color': 'rgba(0,0,0,0)', 'thickness': 0.2},
                'threshold': {
                    'line': {'color': 'red' if lts_overall_mean < 0 else 'green', 'width': 6},
                    'thickness': 1,
                    'value': lts_overall_mean
                },
                'steps': [
                    {'range': [-3, 0], 'color': 'rgba(255, 0, 0, 0.3)'},
                    {'range': [0, 3], 'color': 'rgba(0, 255, 0, 0.3)'}
                ],
            },
            name='Overall LTS Score'
        ))
        fig4.update_layout(
            title='Overall LTS Score',
            paper_bgcolor='black',
            plot_bgcolor='black',
            font=dict(color='white')
        )
    else:
        company_info = [html.H2("No data available for the selected date")]
        mean_scores = [html.Div(html.H3("No data available"))]
        fig2 = go.Figure()
        fig3 = go.Figure()

    return company_info, mean_scores, fig2, fig3, fig4

# Callback for the time-series analysis page
@app.callback(
    Output('sts-mean-timeseries-graph', 'figure'),
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_sts_mean_timeseries(start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    filtered_df = df[(df['Timestamp'] >= start_date) & (df['Timestamp'] <= end_date)]
    # Fill missing data with forward fill
    filtered_df = filtered_df.set_index('Timestamp').resample('D').ffill().reset_index()


    fig = go.Figure()
    if not filtered_df.empty:
        fig.add_trace(go.Scatter(
            x=filtered_df['Timestamp'],
            y=filtered_df['STS_Mean'],
            mode='lines',
            name='STS_Mean',
            line=dict(color='blue')
        ))

    fig.update_layout(
        #title='Time-Series of STS Mean',
        xaxis_title='Date',
        yaxis_title='STS Mean Value',
        paper_bgcolor='black',
        plot_bgcolor='black',
        font=dict(color='white')
    )

    return fig

# Callback for the SDG_Mean time-series graph
@app.callback(
    Output('sdg-mean-timeseries-graph', 'figure'),
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_sdg_mean_timeseries(start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    filtered_df = df[(df['Timestamp'] >= start_date) & (df['Timestamp'] <= end_date)]
    # Fill missing data with forward fill
    filtered_df = filtered_df.set_index('Timestamp').resample('D').ffill().reset_index()


    fig = go.Figure()
    if not filtered_df.empty:
        fig.add_trace(go.Scatter(
            x=filtered_df['Timestamp'],
            y=filtered_df['SDG_Mean'],
            mode='lines',
            name='SDG_Mean',
            line=dict(color='orange')
        ))

    fig.update_layout(
        #title='Time-Series of Overall SDG Sentiment',
        xaxis_title='Date',
        yaxis_title='SDG Mean Value',
        paper_bgcolor='black',
        plot_bgcolor='black',
        font=dict(color='white')
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
