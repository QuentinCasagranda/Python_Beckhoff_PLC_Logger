# Python Beckhoff PLC Logger

Python logger used to record sensor values from a beckhoff PLC. It stores the data in a CSV file and can expose it via a simple FastAPI server to use it in web dashboard.

## Prerequisites

- Python 3.9+
- Network access to the Beckhoff PLC
- AMS / TwinCAT route configured for ADS communication
- Python libraries installed from `requirement.txt`

libraries installation:

```powershell
pip install -r requirement.txt
```

## How to use this project

run the script with default options:

```powershell
python .\retreive_Plc_values.py
```

Available options:

- `--csvPath <path>` : csv files output repertory (default: `csv`)
- `--csvname <name>` : Name of the csv file (default: `global`)
- `--TMoy <seconds>` : Time for the average calculation (default: `10`)
- `--NbMoy <count>` : Number of measure used for the average calculation (default: `10`)
- `--verbose` : Display the debug information in the console
- `--apiPort <port>` : API HTTP port (default: `80`)
- `--keepLastValues` : Keep the existing values of the csv file instead of overwriting it at each execution

## CSV behavior

The program stores the csv files in the `--csvPath` repertory:

- `<csvname>.tmp.csv` : Temporary file where the new values are written before being copied to the final csv file
- `<csvname>.csv` : Final csv file containing the historical values

Chaque ligne contient :

- Average value of the PT100 sensors
- water flow rate
- water temperature
- timestamp ISO

## HTTP API

The program run a server on the port `--apiPort`.

Endpoint exposé :

- `GET /getcsv`

Examples :

- `http://localhost/getcsv`
- `http://localhost:8080/getcsv` if `--apiPort 8080`

You can run the API separately using `uvicorn` :

```powershell
uvicorn Api_csv:app --host 0.0.0.0 --port 80
```

## Stopping the program

Press `Ctrl + C` in the terminal. the program handle `KeyboardInterrupt` and close the connexion.

## Troubleshooting

- ADS connection fails: check the PLC IP address, AMS Net ID, and the ADS route.
- Port 80 permission issue: use `--apiPort 8080` or another non-privileged port.
- No graph displayed: make sure `--showgraph` is enabled and the environment supports a graphical window.
- API not found: make sure `--csvPath` is `csv` when the script starts the embedded API.

## Notes

- The project reads 8 PT100 sensors (4 modules × 2 values) by default.
- The average is calculated every `TMoy` seconds, over `NbMoy` measurements.
- PLC symbols are read via `MAIN.fbAIModule[i].nTempValue` for the sensors and `MAIN.fbSBG232.in_data` for the water.
- To adapt the solution to another PLC configuration, modify the constants and reading logic in `retreive_Plc_values.py`.
