build:
	pip3 install -r requirements.txt

start:
	./startup.sh

test:
	pip3 install -r test_requirements.txt
	flake8 --exclude ./lib/*
	python3 -m unittest tests/*.py
