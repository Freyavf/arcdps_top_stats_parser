from click import style
from dash import html, dcc, Output, Input, State, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc


from app import app

img_size = {}
img_size[1] = 400
img_size[2] = 400
img_size[3] = "95%"
img_size[4] = "60%"
img_size[5] = "60%"
img_size[6] = 400
img_size[7] = "70%"
img_size[8] = "100%"
img_size[9] = "100%"
img_size[10] = "80%"
img_size[11] = "100%"
img_size[12] = "80%"
img_size[13] = "80%"
img_size[14] = "80%"

img_top_offset = {}
img_top_offset[1] = "2.5%"
img_top_offset[2] = "45%"
img_top_offset[3] = "45%"
img_top_offset[4] = "5%"
img_top_offset[5] = "5%"
img_top_offset[6] = "45%"
img_top_offset[7] = "2.5%"
img_top_offset[8] = "15%"
img_top_offset[9] = "25%"
img_top_offset[10] = "30%"
img_top_offset[11] = "20%"
img_top_offset[12] = "10%"
img_top_offset[13] = "25%"
img_top_offset[14] = "20%"

layout = [
    html.H2('How to read the Records of Valhalla', style={'text-align': 'center'}),
    html.Div(
        dbc.Card([
            dbc.CardBody([
                "Welcome to the tutorial on how to read the Records of Valhalla!",
                html.Br(),
                "Since you will be seeing a lot of data, we tried to make a comprehensive guide on the features and usage of our stats page. The goal is to allow everyone to check their own performance over a whole raid at a glance, to see their development over past raids, and to identify top performing players so everyone knows who to ask for advice with a specific class. If you'd prefer to get the tutorial by video, you can find it ",
                html.A("here.", href="https://youtu.be/OLhaHNC1e0M"),
                html.Br(),
                html.Br(),
                dbc.Row([
                    dbc.Col([
                        html.H3("API Key"),
                        "First of all, the website will ask you to add an API key with character permissions, so go to your ",
                        html.A("arenanet account", href="https://account.arena.net/applications/create"),
                        " and create a new API key with account and character permissions. We need those to check your character names and show you your own data. Copy the API key and ",
                        html.A("add it", href="https://records-of-valhalla-staging.herokuapp.com/api"),
                        " to the Records of Valhalla. You will then see your account name and a list of your characters. Next to each character, their class and the number of raids they attended is shown. The characters that attended at least one raid are clickable. We will come to that later. You will only need to add your API key once, unless you start playing with a new character. ",
                    ]),
                    dbc.Col(
                        html.Div(html.Img(id={'type': 'image', 'index': 1},src="assets/API_permissions.png", style={'width': img_size[1]}, className='bordered-img'),
                                 id={'type': 'image-div', 'index': 1}, style={}),
                        className="centered-col"),
                ],
                align="center",
                ),

            dbc.Row([
                dbc.Col(html.H3("Home page")),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 2}, src="assets/home.png", style={'width': img_size[2]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 2}, style={}),
                    className="centered-col"),
            ],
            align="center",),
                
            dbc.Row([
                dbc.Col("This shows what you have previously known as the Carrot Awards. At the top, there is a dropdown menu where you can choose which raid you want to see the stats of. By default, the last raid will be chosen. Below that, there is a table with a short summary of the raid, like the date, how many kills and deaths we had, the average number of squad members and enemies, the total squad damage, and so on."),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 3}, src="assets/summary_table.png", style={'width': img_size[3]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 3}, style={}),
                    className="centered-col"),
            ],
                    align="center"),

            dbc.Row([
                dbc.Col("In the bar charts, the top performing players for the most relevant stats are shown. These stats are damage, tag distance, stability, condition cleanse, healing, and boon rips. Top performing players for damage and tag distance are the top 5, for all other stats on this page it’s the top 3. All except tag distance are sorted by the total values achieved in the chosen raid. Each line shows the name and profession of the character. The classes are also color coded as shown in the legend on the bottom right of each graph. The two numbers at the beginning of each bar indicate how often this character was one of the top performing players and in how many fights they were present. The value at the end of each bar shows the total value achieved over the whole raid, which also corresponds to the length of the bars in the graphs. The value behind the bar is the average stat value per second over all fights a character was involved in. "),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 4}, src="assets/award_bar_chart.png", style={'width': img_size[4]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 4}, style={}),
                    className="centered-col")
            ],
            align="center"),

            dbc.Row([
                dbc.Col("For tag distance, the graph looks slightly different. Here, the characters are sorted by the percentage of times they reached top 5 closest to tag. Again, the character name, profession, times top and number of fights in which a character was involved are given. The percentage at the end of the bar indicates how often a character achieved top 5 distance to tag in the fights they were involved in, so times top 5 divided by number of fights present."),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 5}, src="assets/distance_bar_chart.png", style={'width': img_size[5]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 5}, style={}),
                    className="centered-col")
            ],
                    align="center"),

            dbc.Row([
                dbc.Col(html.H3("Details")),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 6}, src="assets/details.png", style={'width': img_size[6]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 6}, style={}),
                    className="centered-col")
            ],
                    align="center"),

            dbc.Row(
                dbc.Col([
                    "Again, you can choose from which raid you would like to see stats using the drop down menu at the top, which by default is the last raid. You will see a short summary of the overall squad stats for the chosen raid in a table. Below that, you see tabs for different stats, namely Damage, Rips, Might, Fury, Healing, Barrier, Cleanses, Stability, Protection, Aegis, and Distance. The numbers shown in these bar charts are the same as those shown on the Home page, i.e. times top, attendance, total value and average value per second (or percentage times top for distance). Note that for your healing or barrier to register, you will need to have the ",
                    html.A("arcdps healing addon", href="https://github.com/Krappa322/arcdps_healing_stats/releases"),
                    " running and stats sharing enabled. The top performing players will be shown by name. For might and fury, these are only the top 2 players, for all other stats you haven’t seen on the Home page yet it’s the top 3 players. All other players are shown by their profession only. ",
                    html.Br(),
                    "Additionally, you will be able to see your own character name if you were there for the chosen raid. This way, you can compare yourself to the top performing players, but can also see how you are doing compared to others in your class, using the color coding or profession names. If you want to see only players of specific classes, you can enable or disable them by clicking on the corresponding legend items. You can also view only players of a single class by double clicking the corresponding legend item.",
                ])
            ),

            dbc.Row([
                dbc.Col("On the top left, there is a drop down menu to sort the graphs differently. The choices are: 'total', which is the default and means the total stat value achieved over the whole raid; 'average', which is the average stat value per second over all fights a character was involved in; 'times top', which indicates how often someone achieved top stats; and 'attendance', which is how many fights someone was there for. Using this, you can for example check how you were doing compared to others on average, if you weren’t able to attend the whole raid."),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 7}, src="assets/sorting_order.png", style={'width': img_size[7]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 7}, style={}),
                    className="centered-col")
            ],
                    align="center"),
            dbc.Row(dbc.Col(html.H3("Personal Profile"))),
            dbc.Row(
                dbc.Col("Now we get to your personal profile. You can get to it either by:")
                ),
            dbc.Row([
                dbc.Col("clicking on one of your character names on the API page ", className="centered-col", width={'size': 4}),
                dbc.Col("or clicking one of your character names in any of the graphs ", className="centered-col", width={'size': 4}),
                dbc.Col("or by clicking on your account name and then Profile. ", className="centered-col", width={'size': 4})
            ]),
            dbc.Row([
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 8}, src="assets/profile_from_api.png", style={'width': img_size[8]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 8}, style={}),
                    className="centered-col", width={'size': 4}),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 9}, src="assets/profile_from_graph.png", style={'width': img_size[9]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 9}, style={}),
                    className="centered-col", width={'size': 4}),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 10}, src="assets/profile_from_prof.png", style={'width': img_size[10]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 10}, style={}),
                    className="centered-col", width={'size': 4}),
            ]),

            dbc.Row([
                dbc.Col("At the top, you see a summary table of how many raids and how many fights this character attended, how many fights you missed if you weren’t there for a whole raid, and how often you achieved top stats in a chosen stat. Below that is a drop down menu showing all of your characters that were present for at least one raid. "),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 11}, src="assets/profile_overview.png", style={'width': img_size[11]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 11}, style={}),
                    className="centered-col"),
            ],
                    align="center"),

            dbc.Row([
                dbc.Col([
                    "The line chart gives you your stat history over the past raids. You can choose which stat you want to see using the radio buttons in the table at the bottom. Here, we show your average stats, since these are more comparable between raids than total stats. Keep in mind that these values still depend on what kind of fights we had, for example how many enemies there were and if it was an organized group. The colored line shows your own average stats. The white line shows the top average stats for each raid, which might come from a different person every time. The colored markers indicate which class generated the top average stats.",
                    html.Br(),
                    "The shaded gray region shows the highest and lowest average stats in your profession. Note again that for healing and barrier, only players running the healing addon will register, so the lowest will often be zero for these two stats and thus the shaded region will go down to zero.",
                    html.Br(),
                    "If you want to look at something more closely, you can draw a rectangle in the chart to zoom in on that part, which might be interesting for stats to which your class is not a main contributor, for example boon rips on scrapper or stability on scourge. To reset the graph, double click anywhere in the graph area."
                ]),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 12}, src="assets/line_chart_annotated.png", style={'width': img_size[12]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 12}, style={}),
                    className="centered-col"),
            ],
                    align="center"),

            dbc.Row([
                dbc.Col("If you hover over any of the data points, you will see the top 10 average stats as a bar chart on the right, where the top performing players and your own characters are shown by name. "),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 13}, src="assets/hover_bar_chart.png", style={'width': img_size[13]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 13}, style={}),
                    className="centered-col"),
            ],
                    align="center"),

            dbc.Row([
                dbc.Col("The table at the bottom shows your average stats for each raid in numbers, if you want to look at several stats at once. You can also enable and disable showing some raids in the line chart by ticking the checkboxes at the left of the table."),
                dbc.Col(
                    html.Div(html.Img(id={'type': 'image', 'index': 14}, src="assets/profile_table.png", style={'width': img_size[14]}, className="bordered-img"),
                             id={'type': 'image-div', 'index': 14}, style={}),
                    className="centered-col"),
            ],
                    align="center"),

            dbc.Row(dbc.Col("We hope this covers the basics and this tool will be helpful for everyone. Let us know if there are any questions! Thank you :)", className="centered-col"))
                
        ])
        ])
    )

]

@app.callback(
    [Output({'type': 'image', 'index': MATCH}, 'style'),
     Output({'type': 'image-div', 'index': MATCH}, 'style'),],
    Input({'type': 'image-div', 'index': MATCH}, 'n_clicks'),
    State({'type': 'image', 'index': MATCH}, 'style'),
    State({'type': 'image', 'index': MATCH}, 'id'),
    prevent_initial_call=True
)
def enlarge_image_on_click(n, style, img_id):
    new_img_style = {
        'z-index': 1,
        'position': 'fixed',
        'left': '2.5%',
        'top': img_top_offset[img_id['index']],
        'width': '95%',
        'max-height': '95%'
    }
    old_img_style = {
        'width': img_size[img_id['index']],
    }
    new_div_style = {
        'z-index': 1,
        'position': 'fixed',
        'left': '0%',
        'top': '0%',
        'width': '100%',
        'height': '100%'
    }
    old_div_style = {
        #'width': img_size[img_id['index']],
    }
    print(style)
    if n:
        if style == old_img_style:
            return [new_img_style, new_div_style]
        else:
            return [old_img_style, old_div_style]

