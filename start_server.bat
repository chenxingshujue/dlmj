lsof -i:8765 -t|xargs kill -9
lsof -i:80 -t|xargs kill -9
nohup python3 server.py > server.log &
nohup python3 -m http.server 80 > web.log &