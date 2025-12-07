from datetime import date

import pandas as pd
from pydantic import BaseModel, ConfigDict


class Statement(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    date: date
    statement: pd.Series
