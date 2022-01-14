PI_IP_ADDRESS=10.0.2.224
PI_USERNAME=pi

.PHONY: transmit
transmit:
	@cd src && python3 transmitter.py

.PHONY: receive
receive:
	@cd src && python3 receiver.py

.PHONY: install
install:
	@cd scripts && bash install.sh

.PHONY: install-python
install-python:
	@python3 -m pip install --user -r src/requirements.txt

.PHONY: copy
copy:
	@echo "For development only"
	@rsync -a $(shell pwd) --exclude env --exclude training $(PI_USERNAME)@$(PI_IP_ADDRESS):/home/$(PI_USERNAME)

.PHONY: shell
shell:
	@echo "For development only"
	@ssh $(PI_USERNAME)@$(PI_IP_ADDRESS)

.PHONY: ping
ping:
	@echo "For development only"
	@ping $(PI_IP_ADDRESS)

.PHONY: web
web:
	@open http://$(PI_IP_ADDRESS):9090/
