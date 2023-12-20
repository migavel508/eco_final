from flask import Flask, jsonify, request
import gspread
import datetime
import json

app = Flask(__name__)

gc = gspread.service_account(filename='./service_account.json')

def get_current_date_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate_total_consumption(data):
    total_consumption = {}
    total_usage_hours = {}

    for row in data:
        type_value = row.get("Type")
        place_value = row.get("Place")
        consumption_str = row.get("Consumption", "0")

        try:
            consumption = float(consumption_str)
        except ValueError:
            # Skip rows with non-numeric Consumption values
            continue

        if type_value and place_value:
            key = f"{type_value}_{place_value}"

            if key not in total_consumption:
                total_consumption[key] = 0
                total_usage_hours[key] = 0

            total_consumption[key] += consumption
            total_usage_hours[key] += 1

    return total_consumption, total_usage_hours

@app.route('/append_row', methods=['POST'])
def append_row():
    try:
        request_data = request.get_json()
        timestamp = get_current_date_time()
        type_value = request_data.get("Type")
        place_value = request_data.get("Place")
        consumption_str = request_data.get("Consumption", "0")

        try:
            consumption = float(consumption_str)
        except ValueError:
            return jsonify({"error": "Invalid Consumption value. Must be a number."})

        user_data = [timestamp, type_value, place_value, consumption]
        sh = gc.open("sih_23")
        worksheet = sh.sheet1
        worksheet.append_row(user_data)

        return jsonify({"message": "Row appended successfully."})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/get_data', methods=['GET'])
def get_data():
    sh = gc.open("sih_23")
    worksheet = sh.sheet1
    data = worksheet.get_all_records()

    if data:
        # Calculate total consumption and usage hours
        total_consumption, total_usage_hours = calculate_total_consumption(data)

        # Update the result with "Total Consumption" and "Usage Hours" columns
        for row in data:
            type_value = row.get("Type")
            place_value = row.get("Place")
            key = f"{type_value}_{place_value}"

            row["Total Consumption"] = total_consumption.get(key, 0)
            row["Usage Hours"] = total_usage_hours.get(key, 0)

        return jsonify({"data": data})
    else:
        return jsonify({"data": []})

if __name__ == '__main__':
    app.run(debug=True)
