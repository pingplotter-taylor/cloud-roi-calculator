import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import RoiCalc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


def default_inputs(key=False):
    default_inputs = {
        "user_count": 250,
        "user_cost": 20,
        "it_cost": 500,
        "frequency": 25,
        "duration": 15,
        "critical_services": 1,
    }
    if key:
        return default_inputs[key]
    else:
        return default_inputs


inputs = default_inputs()
header = html.H1(children="PingPlotter ROI Calculator")
form = dbc.Form(
    dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Label(i.replace("_", " ").title(), html_for=i),
                    dcc.Input(id=i, value=default_inputs(key=i), type="text"),
                ]
            )
            for i in inputs.keys()
        ]
    )
)


plots = dbc.Row(
    [
        dbc.Col(dcc.Graph()),
        dbc.Col(dcc.Graph()),
    ],
    id="plots",
)


content = [
    header,
    form,
    plots,
]

app.layout = dbc.Container(content)


def makePlots(roi):
    report = roi.report()
    content = [
        dbc.Col(dcc.Graph(figure=report["plots"]["roi"])),
        dbc.Col(dcc.Graph(figure=report["plots"]["breakeven"])),
    ]
    return content


@app.callback(
    dash.Output("plots", "children"),
    [dash.Input(i, "value") for i in inputs.keys()],
)
def update_figure(*args):
    pingplotter_impact = 0.5
    arg_names = list(default_inputs().keys())
    try:
        inputs = {arg_names[i]: int(args[i]) for i in range(0, len(args))}

        downtime_cost = RoiCalc.calc_downtime_cost(
            inputs["user_cost"],
            inputs["it_cost"],
            inputs["frequency"],
            inputs["duration"],
        )

        roi = RoiCalc.PingPlotterRoi(
            inputs["user_count"],
            inputs["critical_services"],
            downtime_cost,
            pingplotter_impact,
        )
        plots = makePlots(roi)
        return plots
    except ValueError:
        pass


if __name__ == "__main__":
    app.run_server(debug=True)
