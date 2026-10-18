# Experience journal

## 18 October 2026 — starting the public project

The project grows from an existing private Home Assistant prototype introduced on 11 October 2026. The practical goal is to compare supply scenarios using the same measured intervals and make missing data and assumptions visible.

Lessons informing the public design:

- A cost number needs an explanation of covered measurements, prices and contract assumptions.
- A counter returning after an outage must not assign all missing consumption to its return time.
- EV pauses and unknown connection states need careful session handling.
- Dashboard refresh needs visible progress, timeout recovery and a last-success time.
- Simulated tests and a working dashboard do not prove agreement with a real supplier invoice.

These are design lessons from the prototype. This entry claims neither verified savings nor a validated complete bill. The public implementation and independent installation tests are pending.

## Template for future measured entries

For each entry include:

1. Observation dates and software versions.
2. Question and comparison method.
3. Configured capabilities and anonymized or synthetic examples.
4. Coverage, missing intervals and known assumptions.
5. Results separated into measurements, estimates and hypotheses.
6. Validation against an independent source where available.
7. Limitations and next step.

Do not publish raw household histories, invoices or private logs. A seasonal observation is not an annual savings forecast. Label illustrative graphs and numbers as synthetic.
