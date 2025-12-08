import sys
import os

sys.path.append(os.getcwd())
from discount_analyst.shared.data_types import StockData

schema = StockData.model_json_schema()
properties = schema.get("properties", {}).keys()
print("Properties in schema:", list(properties))
