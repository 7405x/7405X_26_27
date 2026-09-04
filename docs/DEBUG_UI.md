# Debug dashboard

`coprocessor/main.py` serves a debugging page from the Jetson on port 8080 (set `webui_port`,
or `"webui": false` to disable). Open `http://<jetson-ip>:8080/` from any laptop or phone on the
robot's network. No build step; it is one HTML file and a stdlib HTTP server.

## Panels

- **Camera**: the Limelight MJPEG stream relayed through the Jetson, with our detection boxes,
  labels, confidence and estimated range drawn over it. "Snapshot to Limelight" saves the current
  frame on the Limelight for training data.
- **Field**: top-down map with the robot (heading arrow, camera FOV), the last 300 poses as a
  trail, every projected object, and the strategy's current target.
- **Detections**: table of projected objects with field coordinates.
- **Robot**: pose, GPS status flags (shows "odom" when running on Brain odometry), strategy
  command, loop timing.
- **Limelight / ML**: live `/status` from the Limelight (pipeline index, fps, temperature, cpu)
  plus a per-class histogram of what the model currently sees. The dropdown switches pipelines.
- **Jetson**: thermal zones, load, memory.
- **Logs / replay**: every world log in `logs/`. Play one back in the browser with the scrubber,
  then "live" to return to the live feed.

## Header dots

server, limelight, V5 brain, GPS. Grey = unknown, green = ok, red = down.

## Without hardware

Serve a recorded log on a laptop:

    python coprocessor/tools/webui_demo.py logs/worldlog_20260904_1.jsonl

## Endpoints

See the docstring at the top of `coprocessor/vaic/webui/__init__.py`.
