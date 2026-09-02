# training/ — model data and export

The shipped `JetsonExample/models/pushback_lite.*` model knows two classes (BallBlue, BallRed)
from a previous season. It does not detect this season's objects, so a new model is required.

## Workflow
1. Capture images from robot height under match lighting. Include cluttered stacks and every
   alliance-colour variant. Aim for a few thousand labelled boxes per class before trusting it.
2. Label with your tool of choice, export YOLO format, and record the dataset version in
   `dataset.yaml` (never commit raw images; store them in a shared drive or bucket).
3. Train, then export ONNX and run `./export_engine.sh model.onnx` **on the Jetson** to
   produce the TensorRT engine (engines are device-specific and are gitignored).
4. Put the ONNX file in `training/models/` (Git LFS tracks it), update the model filename in a
   copy of `JetsonExample/model_backend.py` or point VEX's code at it, and update
   `JetsonExample/labels.txt` (or a team copy) so class indices match.

Class order in labels.txt is the wire `classID`, so never reorder classes between model versions
without bumping the log schema version in `coprocessor/vaic/world.py`.
