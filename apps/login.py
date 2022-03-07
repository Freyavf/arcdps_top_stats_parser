from click import style
from dash import html, dcc, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import request, session
import requests
from requests.auth import HTTPBasicAuth

# Login screen
from flask_login import login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import app, db
from models import User


login = dbc.Row([
    dcc.Location(id='url_login', refresh=True),
    dbc.Col([
        html.H2('Login Form', style={'text-align': 'center'}),
        dbc.Card([
            dbc.CardImg(src="assets/logo.png", top=True, style={'width': 200, 'margin': 'auto'}),
            dbc.CardBody([
                html.Div(
                    className='mb-3',
                    children=[
                        dbc.Input(type='text', id='uname-box', placeholder='Enter your username')
                    ]
                ),
                html.Div(
                    className='mb-3',
                    children=[
                        dbc.Input(type='password', id='pwd-box', placeholder='Enter your password')
                    ]
                ),
                dbc.Button('Login', id='login-button', class_name='btn btn-color px-5 w-100', n_clicks=0)
            ])
        ]),
        html.Div(children='', id='output-state')
    ],
    width={'size': 4, 'offset': 4})
])


# Successful login
success = html.Div([html.Div([html.H2('Login successful.'),
                              html.Br(),
                              dcc.Link('Home', href='/')])
                    ])

# Failed Login
failed = html.Div([html.Div([html.H2('Log in Failed. Please try again.'),
                             html.Br(),
                             html.Div([login]),
                             dcc.Link('Home', href='/')
                             ])
                   ])


# Logout
logout = html.Div([html.Div(html.H2('You have been logged out - Please login')),
                   html.Br(),
                   dcc.Link('Home', href='/')
                   ])


logged_in_menu = dbc.Nav(className='menu', children=[
    dbc.DropdownMenu(
            [dbc.DropdownMenuItem("API Key", href='/api'), 
            dbc.DropdownMenuItem("Profile", href='/details/')],
            label="Account",
            caret=False,
            nav=True,
            id='account-dpn',
        ),
    dbc.NavItem(dbc.NavLink("Home", href='/')),
    dbc.NavItem(dbc.NavLink("Details", href='/details')),
    dbc.NavItem(dbc.NavLink("Upload", href='/upload')),
    dbc.NavItem(dbc.NavLink("Logout", href='/logout')),
],
)

loggin_menu = dbc.Nav(className='menu', children=[
    dbc.DropdownMenu(
            [dbc.DropdownMenuItem("API Key", href='/api'), 
            dbc.DropdownMenuItem("Profile", href='/details/')],
            label="Account",
            caret=False,
            nav=True,
            id='account-dpn',
        ),
    dbc.NavItem(dbc.NavLink("Home", href='/')),
    dbc.NavItem(dbc.NavLink("Details", href='/details')),
    dbc.NavItem(dbc.NavLink("Admin", href='/login')),
])


@app.callback(Output('url_login', 'pathname'),
              Output('output-state', 'children'),
              [Input('login-button', 'n_clicks')],
              [State('uname-box', 'value'), State('pwd-box', 'value')])
def login_button_click(n_clicks, username, password):
    if n_clicks > 0:
        user = db.session.query(User).filter_by(username = username).first()
        if user is not None:
            if check_password_hash(user.password, password):
                login_user(user)
                return '/success', ''
            else:
                return '/login', 'Incorrect username or password'
        else:
            return '/login', 'Incorrect username or password'
    return '/login', ''


@app.callback(
    Output('user-status-div', 'children'), 
    Output('login-status', 'data'), 
    [Input('url', 'pathname')]
    )
def login_status(url):
    ''' callback to display login/logout link in the header '''
    if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated \
            and url != '/logout':  # If the URL is /logout, then the user is about to be logged out anyways
        return logged_in_menu, current_user.get_id()
    else:
        return loggin_menu, 'loggedout'
