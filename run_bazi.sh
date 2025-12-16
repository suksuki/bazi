# Kill previous instances
pkill -f streamlit || true
./venv/bin/pip install -r requirements.txt
./venv/bin/streamlit run main.py --server.port 8501 --server.address 0.0.0.0
