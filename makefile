PORT=5000
export PYTHONWARNINGS=ignore::SyntaxWarning

install:
	./install.sh

kill-port:
	@PID=$$(lsof -t -i:$(PORT)); \
	if [ -n "$$PID" ]; then \
		echo "Killing process on port $(PORT): $$PID"; \
		kill -9 $$PID; \
	else \
		echo "Port $(PORT) is free."; \
	fi

api:
	kill-port
	. .venv/bin/activate && python3 run.py &

worker:
	. .venv/bin/activate && PYTHONPATH=. python3 -m src.workers.summarize_worker &

docker-up:
	docker compose up -d

docker-down:
	docker compose down

run: install kill-port docker-up
	. .venv/bin/activate && python3 run.py &
	. .venv/bin/activate && PYTHONPATH=. python3 -m src.workers.summarize_worker &