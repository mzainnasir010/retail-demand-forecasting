# Data Dictionary

## Source dataset

The training notebook uses Kaggle's *Store Sales — Time Series Forecasting* competition dataset. The supplied run describes `train.csv` with 3,000,888 daily rows over 2013-01-01 through 2017-08-15, 54 stores and 33 product families (1,782 store/family series). Demand is measured in sales units. The dataset is subject to the [competition rules](https://www.kaggle.com/competitions/store-sales-time-series-forecasting/rules); raw source data is not redistributed here.

## Source fields used

| File / field | Meaning | Use / handling |
|---|---|---|
| `train.csv: id` | Source row identifier | Provenance only; not a model feature |
| `train.csv: date` | Daily observation date | Parsed as date; chronological index |
| `train.csv: store_nbr` | Store identifier | Series key and numeric model context |
| `train.csv: family` | Product family | Series key and categorical model context |
| `train.csv: sales` | Daily demand target in units | Nonnegative target; model uses `log1p` |
| `train.csv: onpromotion` | Number of items promoted | Inspected but omitted from future features because future values are not provided |
| `stores.csv: type` | Store class | Encoded as `store_type_code` |
| `stores.csv: cluster` | Store cluster | Static model feature |
| `stores.csv: city`, `state` | Store location | Available for context, not used by the selected model |
| `holidays_events.csv: date` | Calendar event date | Calendar join key |
| `holidays_events.csv: type`, `locale`, `transferred` | Event classification/scope/transfer flag | National non-transferred events supply the `national_holiday` flag |

No inventory balance or supplier lead-time field is present, so the application does not calculate reorder points or stockout risk.

## Model features

| Feature | Definition |
|---|---|
| `dow`, `dom`, `month`, `quarter`, `year` | Calendar weekday, day-of-month, month, quarter and year |
| `is_weekend` | Saturday/Sunday indicator |
| `is_payday` | Day 15 or final day of the month indicator |
| `national_holiday` | Known national non-transferred holiday indicator |
| `store_nbr`, `family_code`, `cluster`, `store_type_code` | Static series context and categorical codes exported in series order |
| `lag_1`, `lag_7`, `lag_14`, `lag_28` | Prior demand values in the target/model space |
| `roll_mean_7/14/28`, `roll_std_7/14/28` | Mean and population standard deviation over strictly prior observations |

Each target row uses only earlier dates. At forecast time, predicted demand is recursively fed into later lag and rolling features.

## Exported forecast and evaluation fields

| Artifact / field | Meaning |
|---|---|
| `forecast_30d.csv: date`, `horizon_day` | Future date and 1–30 horizon index |
| `store_nbr`, `family` | Forecast series identifiers |
| `forecast` | Nonnegative predicted sales units |
| `lower_p10`, `upper_p90` | Empirical validation-residual interval bounds |
| `window_predictions.csv: role`, `window` | Chronological validation/test split and window index |
| `actual`, `naive`, `seasonal_naive`, `lightgbm`, `xgboost` | Observed and candidate predictions for each historical window |
| `series_metadata.csv` | Stable series ordering and static categorical feature values for model serving |
| `inference_metadata.json` | Ordered feature definitions, calendar values, target transform and horizon-specific residual quantiles |
| `family_outlook.csv` | Previous 30 observed days and next 30 forecast units by family, with percent change |
| `volatile_series.csv` | 90-day mean, standard deviation and coefficient of variation by store/family |
| `largest_misses.csv` | Largest aggregate absolute errors by evaluation window and series |

The notebook also produces `cleaning_log.json`, `eda_summary.json`, validation/test metric CSVs and report figures.
