#!/bin/bash
pip install pyinstaller==6.4.0
pyinstaller --onefile --windowed calipers.py
