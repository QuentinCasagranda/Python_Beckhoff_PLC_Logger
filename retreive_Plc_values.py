import pyads
from datetime import datetime
import time
import csv
import os
import threading
import uvicorn
from Api_csv import app, configure_api 
import argparse
import shutil

# --- Argument parser ---
parser = argparse.ArgumentParser(description="Reading PLC datas, save in CSV files and display graphs script")

parser.add_argument("--csvPath", type=str, help="Save path of the CSV files", default="csv")
parser.add_argument("--csvname", type=str, help="the name of the csv file", default="global")
parser.add_argument("--TMoy", type=int, help="Time before the average temperature calculation (in seconds)", default=10)
parser.add_argument("--NbMoy", type=int, help="Number of measure for the average temperature calculation", default=10)
parser.add_argument("--verbose", action="store_true", help="Enable debug messages", default=False)
parser.add_argument("--apiPort", type=int, help="Port of the API", default=80)
parser.add_argument("--keepLastValues", action="store_true", help="Keep the values that are already in the csv files", default=False)

args = parser.parse_args()

# --- Constants ---
PLC_IP = "ipag-plc03.u-ga.fr"
AMS_NET_ID = "5.107.103.42.1.1"
AMS_PORT = 851
T_MOY = args.TMoy
NB_MOY = args.NbMoy    
TE = T_MOY / NB_MOY   # Sampling time for all sensors
MODULE_NUMBER = 4    
SENSOR_NUMBER = MODULE_NUMBER * 2
MEASURE_PRECISION = 1  # Number of decimal for the measure rounding

configure_api(args.csvname, args.csvPath)

color = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[96m",
    "reset": "\033[00m"
}

# --- Arguments related messages ---

if "C:" in args.csvPath:
    print(f"Storage path of the csv files : {color['cyan']}{args.csvPath}{color['reset']}\n")
else:
    print(f"Storage path of the csv files : {color['cyan']}{os.path.join(os.getcwd(), args.csvPath)}{color['reset']}\n")

if args.apiPort in (80, 443):
    print(f"Access the API from {color['blue']}http://localhost/pt100-1.csv{color['reset']} (port {args.apiPort})")
else:
    print(f"Access the API from {color['blue']}http://localhost:{args.apiPort}/pt100-1.csv{color['reset']}")

# --- Csv creating function ---
def Create_csv_file(paths = []):

    for path in paths:
        if not os.path.exists(path) or not args.keepLastValues:
            with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f, delimiter=',')
                    csv_row = []

                    for sensor_name in sensors:
                        csv_row.append(sensor_name)

                    csv_row.append("Water_Temp(°C)")
                    csv_row.append("Water_Flow(l/min)")
                    csv_row.append("timestamp")
                    writer.writerow(csv_row)

# --- Csv writting function ---
def write_to_csv():

    time = datetime.now()

    # --- Écriture dans le CSV ---
    with open(tmpPath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=',')

        if time.tzinfo is None:
            time = time.astimezone()

        csv_row = []
        for sensor_name in sensors:
            sensors[sensor_name]['average'] = round(sum(sensors[sensor_name]['measure']) / len(sensors[sensor_name]['measure']), MEASURE_PRECISION)
            csv_row.append(sensors[sensor_name]['average'])

        sensors["SBG232"]["average_tempreature"] = round(sum(sensors["SBG232"]["tempreature"]) / len(sensors["SBG232"]["tempreature"]), MEASURE_PRECISION)
        sensors["SBG232"]["average_flow"] = round(sum(sensors["SBG232"]["flow"]) / len(sensors["SBG232"]["flow"]), MEASURE_PRECISION)
        
        csv_row.append(sensors["SBG232"]["average_tempreature"])
        csv_row.append(sensors["SBG232"]["average_tempreature"])
        csv_row.append(time.isoformat())
        writer.writerow(csv_row)

    shutil.copy(tmpPath, finalPath)

    if args.verbose:
        # TODO : modifier le message pour afficher les moyenne et pas la mesure
        print(f"{color['green']}New data received{color['reset']} - Sensor: {color['cyan']}{sensor_name}{color['reset']}, Measure: {color['yellow']}{csv_row}°C{color['reset']}, Timestamp: {color['blue']}{time}{color['reset']}\n")

# --- Clear the measure list for all sensors ---
def clear_measure() :
    for sensor in sensors:
        sensors[sensor]['measure'] = []

# --- Check if measure lenth is < NbMoy --- 
def check_measure_length():
    IsFull = False
    for sensor in sensors:
        if len(sensors[sensor]['measure']) >= NB_MOY:
            IsFull = True
        else:
            if args.verbose:
                print(f"{color['yellow']}Waiting for more data... Measure count: {color['yellow']}{len(sensors[sensor]['measure'])}/{NB_MOY}{color['reset']}\n")
            IsFull = False
            break

    return IsFull
            
# --- Read the data from PLC function ---
def read_plc_temp_data():
    for cnt in range(MODULE_NUMBER):
        try :
            PLC_table_name = f'MAIN.fbAIModule[{cnt}].nTempValue'

            sensor1_name = list(sensors.keys())[cnt * 2]
            sensor2_name = list(sensors.keys())[cnt * 2 + 1]
            if args.verbose:
               print(f"Reading data for sensor {color['cyan']}{sensor1_name}{color['reset']} from twincat table {color['blue']}{PLC_table_name}{color['reset']}...")
        
            measure_table = plc.read_by_name(PLC_table_name, pyads.PLCTYPE_INT * 2)

            sensors[sensor1_name]['measure'].append(round(measure_table[0] / 10.0, 1))
            sensors[sensor2_name]['measure'].append(round(measure_table[1] / 10.0, 1))

        except Exception as e:
            Time = datetime.now()
            print(f"{color['red']}Error reading PLC data: {e}{color['reset']} {color['yellow']}Time:{Time.time()}{color['reset']}\n")
            continue
        

def read_plc_water_data():
    try:
        water_measures = plc.read_by_name('MAIN.fbSBG232.in_data', pyads.PLCTYPE_BYTE * 4)
        water_temp = (water_measures[0] >> 2) + (water_measures[1] << 6)
        water_flow = water_measures[2] + water_measures[3] << 8
    
        sensors["SBG232"]["tempreature"].append(water_temp)
        sensors["SBG232"]["flow"].append(water_flow)

    except Exception as e:
        Time = datetime.now()
        print(f"{color['red']}Error reading PLC water data: {e}{color['reset']} {color['yellow']}Time:{Time.time()}{color['reset']}\n")
    


# --- PLC conexion ---
plc = pyads.Connection(AMS_NET_ID, AMS_PORT, PLC_IP)
plc.open()

# --- Creation of the dictionnaty that contains the measures ---
sensors = {}
for cnt in range(SENSOR_NUMBER):
    sensors[f"pt100-{cnt+1}"] = {
                                    "measure": [],
                                    "name": f"pt100-{cnt+1}",
                                    "timestamp": datetime.now(),
                                    "average": 0.0,
                                }

sensors["SBG232"] = {
                        "tempreature": [],
                        "flow": [],
                        "name": "SBG232",
                        "timestamp": datetime.now(),
                        "average_tempreature": 0.0,
                        "average_flow": 0.0,
                    }
    

# --- Create repertory for the csv files ---
os.makedirs(args.csvPath, exist_ok=True)

tmpPath = os.path.join(args.csvPath, args.csvname + ".tmp.csv")
finalPath = os.path.join(args.csvPath, args.csvname + ".csv")

Create_csv_file([tmpPath, finalPath])



# --- API handling ---
def start_api():
    uvicorn.run(app, host="0.0.0.0", port=args.apiPort)

api_thread = threading.Thread(target=start_api, daemon=True)
api_thread.start()


# --- Main loop ---
try:
    while True:
        try:
            read_plc_temp_data()
            read_plc_water_data()

        except Exception as e:
            Time = datetime.now()
            print(f"{color['red']}Error reading PLC data: {e}{color['reset']}{color['yellow']} Time:{Time.time()}{color['reset']}\n")

        if check_measure_length() :
            write_to_csv()
            clear_measure()

        time.sleep(TE) 
except KeyboardInterrupt:
    plc.close()
