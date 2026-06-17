PORT=5000
export PYTHONWARNINGS=ignore::SyntaxWarning

install:
	./install.sh

kill-server:
	@PID=$$(lsof -t -i:$(PORT)); \
	if [ -n "$$PID" ]; then \
		echo "Killing process on port $(PORT): $$PID"; \
		kill -9 $$PID; \
	else \
		echo "Port $(PORT) is free."; \
	fi

kill-redis:
	@PID=$$(lsof -t -i:6379); \
	if [ -n "$$PID" ]; then \
		echo "Killing process on port 6379: $$PID"; \
		kill -9 $$PID; \
	else \
		sudo systemctl stop redis; \
		echo "Port 6379 is free."; \
	fi

api:
	kill-server
	. .venv/bin/activate && python3 run.py &

worker:
	. .venv/bin/activate && PYTHONPATH=. python3 -m src.workers.summarize_worker &

docker-up:
	docker compose up -d

docker-down:
	docker compose down

run: install kill-server kill-redis docker-up
	. .venv/bin/activate && python3 run.py &
	sleep 10
	. .venv/bin/activate && PYTHONPATH=. python3 -m src.workers.summarize_worker &