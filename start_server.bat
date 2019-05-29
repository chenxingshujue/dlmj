lsof -i:8765 -t|xargs kill -9
nohup python3 server.py > server.log