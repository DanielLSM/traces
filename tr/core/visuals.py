import numpy as np
np.random.seed(sum(map(ord, 'calmap')))
import pandas as pd
import calmap
import pickle

# all_days = pd.date_range('1/15/2014', periods=700, freq='D')
# days = np.random.choice(all_days, 500)
# events = pd.Series(np.random.randn(len(days)), index=days)

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
for _ in schedule.keys():
    all_days_schedule.extend(schedule[_]['assigned_dates'])