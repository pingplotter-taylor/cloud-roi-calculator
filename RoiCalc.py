import pandas as pd
import numpy as np
import plotly.express as px
import math


def price_per_trace(trace_count):
    if trace_count <= 25:
        return 10
    elif trace_count > 25 and trace_count <= 50:
        return 9
    elif trace_count > 50 and trace_count <= 100:
        return 8
    elif trace_count > 100 and trace_count <= 250:
        return 6
    else:
        return 5


def calc_pingplotter_cost(trace_count):
    per_trace = price_per_trace(trace_count)
    total = per_trace * trace_count
    return total


def calc_downtime_cost(user_cost, it_cost, issue_frequency, issue_duration_minutes):
    hourly_HR_cost = user_cost + it_cost
    avg_issue_cost = (issue_duration_minutes / 60) * hourly_HR_cost
    monthly_downtime_cost = issue_frequency * avg_issue_cost
    return monthly_downtime_cost


class PingPlotterRoi:
    def __init__(
        self,
        user_count,
        critical_services,
        monthly_downtime_cost,
        pingplotter_downtime_impact,
    ):
        self.scenarios = [i / 100 for i in range(0, 101)]
        self.figsize = (10, 5)
        self.inputs = dict(
            user_count=user_count,
            critical_services=critical_services,
            monthly_downtime_cost=monthly_downtime_cost,
            pingplotter_downtime_impact=pingplotter_downtime_impact,
        )
        max_traces = user_count * critical_services
        traces = pd.Series([math.ceil(max_traces * i) for i in self.scenarios]).rename(
            "traces"
        )
        coverage = pd.Series(self.scenarios).rename("coverage")
        df = pd.DataFrame([coverage, traces]).T
        df["pingplotter_cost"] = df["traces"].apply(lambda x: calc_pingplotter_cost(x))
        df["cost_per_trace"] = df["traces"].apply(lambda x: price_per_trace(x))
        df["downtime_cost"] = monthly_downtime_cost
        df["downtime_impact"] = (
            df["downtime_cost"] * pingplotter_downtime_impact * df["coverage"]
        )
        df["adjusted_downtime"] = df["downtime_cost"] - df["downtime_impact"]
        df["roi"] = (df["downtime_impact"] - df["pingplotter_cost"]) / df[
            "pingplotter_cost"
        ]
        self.df = df.groupby("traces").max().reset_index().dropna()

    def getRoiValues(self, agg="min"):
        if agg == "min":
            df = self.df.query("roi > 0")
            target_index = df.index.min()
        elif agg == "max":
            df = self.df
            target_index = df.index.max()
        else:
            raise ValueError("Error")
        if ~np.isnan(target_index):
            record = df.loc[target_index]
            if record["roi"] > 0:
                return record

    def plotRoi(self):
        info = self.getRoiValues(agg="max")
        if isinstance(info, pd.Series):
            title = (
                f"Max ROI saves ${round(info['downtime_impact'])} in monthly downtime"
            )
        else:
            title = "Negative ROI"
        plt = px.line(
            self.df, x="traces", y=["pingplotter_cost", "downtime_impact"], title=title
        )
        return plt

    def plotBreakeven(self):
        info = self.getRoiValues(agg="min")
        if isinstance(info, pd.Series):
            title = f"Positive ROI begins at {round(info['traces'])} traces for ${round(info['pingplotter_cost'])}/mo"
            plt = px.line(
                self.df,
                x="traces",
                y=["downtime_cost", "adjusted_downtime"],
                title=title,
            )
            plt.add_hline(
                y=info["adjusted_downtime"],
                line_dash="dash",
                line_color="gray",
                annotation_text="Breakeven downtime",
            )
            plt.add_vline(
                info["traces"],
                line_dash="dash",
                line_color="gray",
                annotation_text="Min ROI Traces",
            )
        else:
            title = "Negative Roi"
            plt = px.line(
                self.df,
                x="traces",
                y=["downtime_cost", "adjusted_downtime"],
                title=title,
            )
        return plt

    def report(self):
        data = {
            "plots": {
                "roi": self.plotRoi(),
                "breakeven": self.plotBreakeven(),
            },
            "min_roi": self.getRoiValues(agg="min"),
            "max_roi": self.getRoiValues(agg="max"),
            "df": self.df.to_html(),
        }
        return data


if __name__ == "__main__":
    attorney_count = 20
    attorney_cost = 200
    critical_services = 2
    it_cost = 3 * 37
    issue_frequency = 4
    issue_duration_minutes = 36
    pingplotter_downtime_impact = 0.5

    legal_downtime_cost = calc_downtime_cost(
        attorney_cost, it_cost, issue_frequency, issue_duration_minutes
    )

    legal = PingPlotterRoi(
        attorney_count,
        critical_services,
        legal_downtime_cost,
        pingplotter_downtime_impact,
    )

    legal.report("Legal IT")
