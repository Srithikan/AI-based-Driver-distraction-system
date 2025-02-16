from flask import Flask, render_template, Response, send_file, jsonify
import subprocess
import os
import csv

app = Flask(__name__)

demo_running = False
process = None
log_file_path = 'driver_monitoring_log.csv'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/first')
def first():
    return render_template('first.html')


@app.route('/start_demo')
def start_demo():
    global demo_running, process

    if not demo_running:
        demo_running = True
        command = ["python", "driver_monitoring.py"]
        print(f"Running command: {command}")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )


        stdout, stderr = process.communicate()
        if stdout:
            print(f"Subprocess stdout: {stdout}")
        if stderr:
            print(f"Subprocess stderr: {stderr}")

        return jsonify(message="Demo started!")
    else:
        return jsonify(message="Demo is already running!")


@app.route('/stop_demo')
def stop_demo():
    global demo_running, process

    if demo_running:
        demo_running = False
        if process:
            process.terminate()  
            process = None
        return jsonify(message="Demo stopped!")
    else:
        return jsonify(message="Demo is not running!")


@app.route('/download_log')
def download_log():
    if not os.path.exists(log_file_path):
       
        with open(log_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Activity', 'Details'])
    return send_file(log_file_path, as_attachment=True)


@app.route('/activity_feed')
def activity_feed():
    activities = []
    try:
        with open(log_file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  
            for row in reader:
                activities.append(f"{row[0]} - {row[1]}: {row[2]}")
    except (FileNotFoundError, StopIteration):
        activities.append("No activities logged yet.")
    
    return jsonify(activities)


if __name__ == '__main__':
    app.run(debug=True)
