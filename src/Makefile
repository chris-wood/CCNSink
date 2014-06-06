all:
	rm *.pyc *.log

rungw:
	kill -9 `lsof -t -i:7000`
	kill -9 `lsof -t -i:8000`
	kill -9 `lsof -t -i:9000`
	python NDNGateway config/simple.yaml

rundir:
	kill -9 `lsof -t -i:7000`
	kill -9 `lsof -t -i:8000`
	kill -9 `lsof -t -i:9000`
	python GatewayDirectory.py
	