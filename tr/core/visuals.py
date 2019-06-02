import numpy as np
np.random.seed(sum(map(ord, 'calmap')))
import pandas as pd
import calmap
import pickle
import matplotlib.pyplot as plt

all_days = pd.date_range('1/15/2014', periods=700, freq='D')
days = np.random.choice(all_days, 500)
events = pd.Series(np.random.randn(len(days)), index=days)

# calmap.yearplot(events, year=2015)

# import ipdb
# ipdb.set_trace()

# calmap.calendarplot(events,
#                     monthticks=3,
#                     daylabels='MTWTFSS',
#                     dayticks=[0, 2, 4, 6],
#                     cmap='YlGn',
#                     fillcolor='grey',
#                     linewidth=0,
#                     fig_kws=dict(figsize=(8, 4)))

pickle_in = open("output.pkl", "rb")
schedule = pickle.load(pickle_in)

all_days_schedule = []
all_days_per_aircraft = {}

for _ in schedule.keys():
    all_days_schedule.extend(schedule[_]['assigned_dates'])
    all_days_per_aircraft[_] = schedule[_]['assigned_dates']

series_all = {_: 0 for _ in all_days_schedule}

for _ in all_days_schedule:
    series_all[_] += 1

flotas = []
indexes = []
for key, value in series_all.items():
    indexes.append(key)
    flotas.append(value)

events = pd.Series(flotas, index=indexes)

# calmap.yearplot(events, year=2019)
# events = pd.Series(np.random.randn(len(all_days_schedule)),
#                    index=all_days_schedule)
# your code

# calmap.calendarplot(events,
#                     monthticks=3,
#                     daylabels='MTWTFSS',
#                     dayticks=[0, 2, 4, 6],
#                     cmap='YlGn',
#                     fillcolor='grey',
#                     linewidth=0,
#                     fig_kws=dict(figsize=(8, 4)))

flotas_aircraft = []
index_aircraft = []
for _ in all_days_per_aircraft['A-15']:
    flotas_aircraft.append(1)
    index_aircraft.append(_)

events_aircraft = pd.Series(flotas_aircraft, index=index_aircraft)

calmap.calendarplot(events_aircraft,
                    monthticks=3,
                    daylabels='MTWTFSS',
                    dayticks=[0, 2, 4, 6],
                    cmap='YlGn',
                    fillcolor='grey',
                    linewidth=0,
                    fig_kws=dict(figsize=(8, 4)))

plt.show()