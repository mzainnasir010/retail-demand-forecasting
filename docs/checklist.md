# Ground-Truth Requirements Checklist

Mark an item complete only when the repository or demo contains evidence.

## A. Foundation and data

- [ ] State a realistic business scenario and connect industry → problem → dataset → approach → forecast → decision.
- [ ] Select a publicly available, legally usable dataset and confirm terms/license before use or redistribution.
- [ ] Document source, license/terms, retrieval date, row/feature count, time span, granularity, target/units and limitations.
- [ ] Provide a data dictionary for every field used.
- [ ] Inspect dimensions, types, missing values, exact duplicates and repeated date/entity keys.
- [ ] Inspect product/store counts, date range, granularity, calendar gaps and per-series history length.
- [ ] Summarize target distribution, zeros, statistics, invalid values and unusual spikes.
- [ ] Document deliberate handling of missing values, duplicates, invalid values, outliers and aggregation.
- [ ] Distinguish missing observations from genuine zero demand; do not silently remove legitimate spikes.

## B. Analysis and time series

- [ ] Include interpreted time-series line chart and rolling-average overlay.
- [ ] Analyze trend, level changes and weekday/month/year seasonality as history permits.
- [ ] Include seasonal/subseries views, demand distribution, outlier/spike analysis and product/store comparisons where supported.
- [ ] Include product/category/store comparisons and a calendar heatmap where supported.
- [ ] Add a short interpretation and modeling/business implication to every key chart.
- [ ] Perform and explain decomposition; justify additive vs multiplicative choice.
- [ ] Inspect residual structure and document stationarity/differencing when using ARIMA-family models.

## C. Features and validation

- [ ] Build features on chronologically sorted data and state the hypothesis behind each feature group.
- [ ] Include appropriate lags (e.g. 1, 7, 14, 28) and shifted rolling mean/std (e.g. 7, 14, 28).
- [ ] Include calendar features (weekday, day, month, quarter/year, weekend, holiday as available).
- [ ] Use price, promotion, store or category only when present and known at prediction time.
- [ ] Verify features do not use current/future target; handle undefined lags explicitly.
- [ ] Use chronological train/validation/test boundaries; no random split.
- [ ] Fit preprocessing only on training data and keep test untouched during tuning.
- [ ] Record exact split boundaries and validation strategy; add walk-forward evaluation if appropriate.

## D. Models and forecast quality

- [ ] Establish naive and/or seasonal-naive baseline before advanced models.
- [ ] Compare multiple suitable approaches from at least two model families.
- [ ] Explain selected models and why major alternatives were omitted.
- [ ] Record versions, random seeds, hardware, training time, hyperparameters and direct/recursive prediction strategy.
- [ ] Report MAE and RMSE plus MAPE or preferably sMAPE when zero-demand periods exist; explain metric choice.
- [ ] Compare candidates to baseline and select using practical considerations as well as accuracy.
- [ ] Report final performance once on held-out test data.
- [ ] Generate a defined future forecast (typically 7–30 days for retail) with origin and horizon marked.
- [ ] Show prediction intervals where supported; otherwise provide labeled historical-error tolerance.
- [ ] Plot actual vs predicted, residual distribution and error over time; identify failures, likely causes and helpful additional data.

## E. Insights and product application

- [ ] Identify growth, decline, seasonal peaks, volatility and low-demand items where supported.
- [ ] Include inventory/reorder suggestions only if inventory and lead-time inputs exist; state assumptions.
- [ ] Tie each business recommendation to a chart, metric or forecast.
- [ ] Provide dashboard overview with historical/forecast demand and growth/decline indicator.
- [ ] Provide demand-trends panel with actuals, forecasts and seasonal context.
- [ ] Provide product selector and ranked product view where supported.
- [ ] Provide model comparison including baseline and MAE/RMSE/MAPE or sMAPE.
- [ ] Provide business insights/risk panel.
- [ ] Use consistent chart colors, readable defaults, labeled dates/units, business-friendly names and graceful loading/caching.
- [ ] Provide functioning FastAPI routes and SQLite persistence for forecast outputs and run metadata.

## F. Repository and communication deliverables

- [ ] Keep backend code in backend/, React code in frontend/, training material in model_training/, and Markdown project docs in docs/.
- [ ] Include reproducible data pipeline and documented cleaning workflow.
- [ ] Include notebooks, reusable source, model/config artifacts as license and repository size permit.
- [ ] Include professional root README covering overview, business problem, dataset, data dictionary, EDA, time-series analysis, features, models, evaluation, forecast results, dashboard, insights, installation, usage, limitations and future improvements.
- [ ] Include .gitignore for secrets, local DB, raw/proprietary data, notebook secrets and large generated artifacts.
- [ ] Include screenshots of dashboard and key charts.
- [ ] Provide LinkedIn demonstration video/post covering dataset, EDA, model choice, evaluation vs baseline, forecast, dashboard, insights and lessons.
- [ ] Provide repository/dashboard links and required submission/contact details through the official process.
- [ ] Review code quality, reproducibility, leakage safeguards and all assignment quality standards.

## G. Kaggle training handoff

- [ ] Attach the appropriate dataset and verify terms and notebook column mapping.
- [ ] Select GPU and two T4 accelerators in Kaggle when available; confirm detected device count.
- [ ] Run preprocessing, baselines, candidate models, evaluation and future forecast cells successfully.
- [ ] Review metrics and artifacts; do not select a model solely because it is neural.
- [ ] Create and download the generated ZIP from Kaggle's clickable output link.
- [ ] Return selected model and output bundle for API/dashboard integration.

## External owner actions

- [ ] Confirm/attach the Kaggle dataset and accept required competition terms.
- [ ] Click the Kaggle notebook download link to save the ZIP locally.
- [ ] Record/publish the LinkedIn video/post and complete official submission/contact details.
