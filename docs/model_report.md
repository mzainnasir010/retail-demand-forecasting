# Model Report

## Objective and setup

Forecast daily sales for each of 54 stores × 33 product families for up to 30 days. The training notebook uses one pooled regressor over 1,782 series. It compares persistence-naive and weekly seasonal-naive baselines with LightGBM and XGBoost. The boosted models use `log1p(sales)`, static store/family context, known calendar fields, lags (1, 7, 14, 28) and past-only rolling mean/std (7, 14, 28). Recursive prediction feeds earlier predictions into later steps. Future promotions are excluded because they are not supplied.

LightGBM was selected by the mean rank of MAE, RMSE and sMAPE across four validation windows. Two later 30-day windows were kept for held-out reporting. A pooled tree model was favored for the many related series and static/calendar features. A separate ARIMA fit per series was omitted to avoid maintaining thousands of models and their feature pipelines; deep learning was not added because the supplied tree/baseline comparison already provides a simpler benchmark and no validated benefit was established.

## Held-out metrics

| Model | MAE ↓ | RMSE ↓ | sMAPE ↓ | RMSLE ↓ |
|---|---:|---:|---:|---:|
| LightGBM (selected on validation) | 62.82 | 240.82 | 55.84% | 0.438 |
| XGBoost | 65.81 | 256.32 | 52.40% | 0.442 |
| Seasonal naive (7-day) | 78.89 | 309.59 | 41.57% | 0.553 |
| Naive (last observed value) | 168.68 | 579.13 | 50.69% | 0.642 |

LightGBM improves held-out MAE and RMSE over seasonal naive, but seasonal naive has lower sMAPE. The model is therefore not best on every measure. sMAPE gives equal percentage weight to low-volume and zero-heavy series, while MAE/RMSE emphasize absolute unit errors. These metrics should be considered together when applying the forecast.

## Error analysis and uncertainty

The notebook exports daily test actual-versus-forecast totals, residuals over time, validation residual distribution and largest-miss tables. The overall errors show remaining volatility and peaks that calendar/lag features do not fully explain. Possible drivers include events, promotions, price changes and unusual local demand; the source inputs do not provide future promotion plans or a complete operational context. Large errors are retained and reported, not removed from training.

The p10/p90 bands use pooled validation residual quantiles by horizon step, calibrated in log/model space and transformed back to sales units. They summarize historical model error; they are not guaranteed coverage intervals for future periods.

## Business signals

The supplied run forecasts a total-demand peak on 2017-09-03. It reports growth in School and Office Supplies and declines in several families. BOOKS has the largest percentage growth from a very small prior base, so absolute units and percentage changes should be read together. Volatility rankings use recent observed means and standard deviations. These findings guide attention; without stock and lead-time inputs they do not constitute reorder or stockout recommendations.

## Serving and limitations

The FastAPI service loads the native saved model artifact, verifies its feature count and sidecar metadata, runs recursive 7/14/30-day inference, and persists each result as a new SQLite run. Complete new dates can be uploaded using the CSV template. The supplied bundle predates the new serving sidecars and must be regenerated with the updated notebook before model status becomes ready.

The training history ends on 2017-08-15, so forecasts from the existing bundle are historical demonstrations rather than current retail guidance. Tree models do not extrapolate long-term year trends, recursive errors can accumulate, and online retraining, inventory feeds and production deployment remain future work.
