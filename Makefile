.PHONY: test-dev-process

test-dev-process:
	python3 -m pytest skills/dev-process/tests -q
	python3 -m unittest discover -s skills/dev-process/scripts -p 'test_*.py' -q
