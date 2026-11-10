# Ground-Truth Requirements Checklist

Mark an item complete only when the repository or demo contains evidence.

## A. Foundation and data

- [x] State a realistic business scenario and connect industry → problem → dataset → approach → forecast → decision.
- [x] Select the Kaggle competition dataset and record its source terms; do not redistribute raw data or imply a standalone open license.
- [x] Document source, rules reference, retrieval date, row/feature count, time span, granularity, target/units and limitations.
- [x] Provide a data dictionary for source fields, generated model features and exported outputs.
- [x] Inspect dimensions, types, missing values, exact duplicates and repeated date/entity keys.
- [x] Inspect product/store counts, date range, granularity, calendar gaps and per-series history length.
- [x] Summarize target distribution, zeros, statistics, invalid values and unusual spikes; export daily outlier flags.
- [x] Document deliberate handling of missing values, duplicates, invalid values, outliers and aggregation.
- [x] Distinguish calendar closures/missing cells from observed zero demand; do not silently remove legitimate spikes.

## B. Analysis and time series

- [x] Include interpreted time-series line chart and rolling-average overlay.
- [x] Analyze trend and weekday/month seasonality; include date trend context in the dashboard.
- [x] Include seasonal patterns, demand distribution, outlier flags and product/store comparisons.
- [x] Include product/category/store comparisons and a calendar heatmap.
- [x] Add chart titles/units and a short modeling/business interpretation in the notebook.
- [x] Perform and explain additive weekly decomposition; zero-sales closure dates make multiplicative decomposition unsuitable.
- [x] Stationarity/differencing checks are not applicable because no ARIMA-family model is used.

## C. Features and validation

- [x] Build features on chronologically sorted data and state the rationale for lag, calendar and series-context groups.
- [x] Include lags 1, 7, 14, 28 and shifted rolling mean/std for 7, 14, 28 days.
- [x] Include weekday, day, month, quarter/year, weekend, payday and available national-holiday calendar features.
- [x] Exclude promotions because future promotion values are not known in this forecast contract; include store/family context.
- [x] Ensure lag/rolling features use only dates before each target; warm-up rows are excluded.
- [x] Use chronological rolling validation and held-out test windows; no random split.
- [x] Keep held-out windows outside candidate selection; category codes encode known entities and are not target-fitted transforms.
- [x] Record each origin, target interval and walk-forward window in run metadata.

## D. Models and forecast quality

- [x] Establish naive and/or seasonal-naive baseline before advanced models.
- [x] Compare multiple suitable approaches from at least two model families.
- [x] Explain the selected LightGBM and the tree/baseline alternatives; document why ARIMA/deep-learning approaches were not selected for this pooled multi-series implementation.
- [x] Record versions, random seed, detected hardware, fit times, parameters and recursive prediction strategy.
- [x] Report MAE and RMSE plus MAPE or preferably sMAPE when zero-demand periods exist; explain metric choice.
- [x] Compare candidates to baseline and select using validation performance; baseline comparison and test metrics are exported.
- [x] Report final performance once on held-out test data.
- [x] Generate a defined 30-day future forecast with origin and horizon marked.
- [x] Show forecast intervals, with p10/p90 bounds in the exported predictions.
- [x] Plot actual vs predicted, residual distribution and error over time; exported figures are available in the dashboard.

## E. Insights and product application

- [x] Identify growth, decline, forecast peaks, volatile series and lowest-volume families where supported.
- [x] Withhold inventory/reorder suggestions because stock and lead-time inputs are absent; state this limitation.
- [x] Tie business signals to the forecast, evaluation metrics, or observed-series volatility values.
- [x] Provide dashboard overview with historical/forecast demand and growth/decline indicator.
- [x] Provide demand-trends panel with actuals, forecasts, uncertainty and a 7-day rolling mean.
- [x] Provide product selector and ranked product view where supported.
- [x] Provide model comparison including baseline and MAE/RMSE/sMAPE.
- [x] Provide business insights panel; inventory risk is explicitly withheld without stock and lead-time inputs.
- [x] Use consistent chart colors, labeled dates/units, responsive layouts, loading/error states and cached model loading.
- [x] Provide functioning FastAPI routes and SQLite persistence for forecast outputs and run metadata.

## F. Repository and communication deliverables

- [x] Keep backend code in backend/, React code in frontend/, training material in model_training/, and Markdown project docs in docs/.
- [x] Include Kaggle training notebook and documented cleaning output; confirm dataset terms remain an owner task.
- [x] Include the training notebook and reusable inference source; large generated models remain excluded from Git and are loaded from the artifact folder.
- [x] Include root README covering project, data, EDA, model features/evaluation, inference flow, setup, usage, limitations and next steps.
- [x] Include .gitignore for secrets, local DB, raw/proprietary data, notebook secrets and large generated artifacts.
- [ ] Include screenshots of dashboard and key charts.
- [ ] Provide LinkedIn demonstration video/post covering dataset, EDA, model choice, evaluation vs baseline, forecast, dashboard, insights and lessons.
- [ ] Provide repository/dashboard links and required submission/contact details through the official process.
- [x] Review code structure, notebook feature chronology, model/artifact compatibility checks, bounded CSV validation and documented limitations.

## G. Kaggle training handoff

- [x] Attach the Store Sales competition dataset and align notebook paths/columns; terms acceptance remains an owner task.
- [ ] Select GPU and two T4 accelerators in Kaggle when available; run updated automatic dual-GPU workflow and confirm device use.
- [ ] Run the updated notebook after adding EDA and serving sidecars; the previously supplied run predates these new exports.
- [x] Review metrics and artifacts; selected model is LightGBM using validation windows and baseline/model comparisons.
- [ ] Create and download the updated ZIP from Kaggle's clickable output link.
- [x] Integrate the previously supplied selected model and output files into the API/dashboard; refresh the bundle for inference sidecars before running fresh predictions.

## External owner actions

- [ ] Confirm that the Kaggle competition terms permit any intended public redistribution of derived artifacts; raw source data is not included.
- [ ] Click the Kaggle notebook download link to save the ZIP locally.
- [ ] Run the updated Kaggle notebook and provide its refreshed ZIP/model metadata bundle so the model-serving endpoint becomes ready.

## H. Saved-model prediction flow

- [x] Load LightGBM/XGBoost native model artifacts from a configured local artifact directory.
- [x] Validate model features, model metadata and complete series mappings before inference.
- [x] Generate recursive 7/14/30-day forecasts with the training feature order and saved validation interval calibration.
- [x] Accept optional complete, consecutive daily sales input and optional known future national holiday dates.
- [x] Persist each prediction as a new SQLite run while retaining the linked history.
- [x] Expose model readiness, prediction submission and downloadable input-template API routes.
- [x] Expose a downloadable CSV for the active prediction run's series forecasts and intervals.
- [x] Add the dashboard prediction form with model status, horizon selection, optional CSV, holiday dates, and result/error states.
- [ ] Re-run/export the updated notebook sidecars and execute a real prediction from the refreshed model bundle.
- [ ] Record/publish the LinkedIn video/post and complete official submission/contact details.
