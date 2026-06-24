.PHONY: run
.DEFAULT_GOAL: run

run:
	source .venv/bin/activate && python3 -Xgil=0 ./src/main.py

time:
	source .venv/bin/activate && time python3 -Xgil=0 ./src/main.py
