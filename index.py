import time
from dash import dcc, dash
from dash import html
from dash.dependencies import Input, Output
from flask import session
from flask_login import current_user, logout_user
import dash_bootstrap_components as dbc
from urllib.parse import unquote

from app import app
from apps import login, upload_page

server = app.server

app.layout = dbc.Container(id='container', children=[
    dcc.Location(id='url', refresh=False),
    dcc.Location(id='redirect', refresh=True),
    dcc.Store(id='login-status', storage_type='session'),
    dbc.Row(id='login-row', children=dbc.Col(html.Div(id='user-status-div'))),
    dbc.Row(id='header', children=[
        dbc.Col(html.Img(id='logo', src='../assets/logo.png'), sm=1),
        dbc.Col(children=[
            html.H1('Writing the Records of Valhalla', 'title'),
            ], sm=10)]),
    html.Hr(id='hr-header'),
    dcc.Store(id='db-update-date'),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              Output('redirect', 'pathname'),
              Input('url', 'pathname'))
def display_page(pathname):
    view = None
    url = dash.no_update
    if pathname == '/login':
        view = login.login
    elif pathname == '/success':
        if current_user.is_authenticated:
            view = login.success
            url = '/details'
        else:
            view = login.failed
    elif pathname == '/logout':
        if current_user.is_authenticated:
            logout_user()
            time.sleep(1)
            url = '/'
        else:
            view = login
            url = '/login'
    elif pathname == '/upload':
        #if current_user.is_authenticated:
        view = upload_page.layout
        #else:
        #    view = 'Redirecting to login...'
        #    url = '/login'
    elif pathname == '/':
        view = login.login
    else:
        view = login.login
    # You could also return a 404 "URL not found" page here
    return view, url


if __name__ == '__main__':
    app.run_server(debug=True)
