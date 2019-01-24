build:
	pip3 install --require-hashes -r requirements.txt

test:
	pip3 install -r test_requirements.txt
	flake8 --exclude lib
	pytest -v --cov-report term-missing --cov server --cov app
	coverage html

