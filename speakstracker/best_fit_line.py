from datetime import date, datetime, time
import numpy as np

def linefit(dates, speaks):

    low_date = min(dates)
    heigh_date = max(dates)
    low_timestamp  = datetime(low_date.year, low_date.month, low_date.day).timestamp()
    heigh_timestamp  = datetime(heigh_date.year, heigh_date.month, heigh_date.day).timestamp()

    timestamps = [datetime.combine(date, time.min).timestamp()
                    - low_timestamp for date in dates]

    slope, intercept = np.polyfit(timestamps, speaks, 1)
    
    low_y = intercept
    heigh_y = slope*(heigh_timestamp - low_timestamp) + intercept    

    return {"low": {"x": low_date, "y": low_y},
            "heigh": {"x": heigh_date, "y": heigh_y}}
