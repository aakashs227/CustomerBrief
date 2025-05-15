import subprocess
import sys

# Full path to the streamlit executable
streamlit_path = r"C:\Users\aakashs\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\streamlit.exe"

# Path to your Streamlit app
app_path = r"C:\Users\aakashs\OneDrive - Allcargo Logistics Ltd\Desktop\MIRA\MIRA2.0\frontend.py"

# Run Streamlit with the specified app
subprocess.run([streamlit_path, 'run', app_path])
