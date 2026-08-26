.PHONY: install-api run-api

install-api:
	$(MAKE) -C api install

run-api:
	$(MAKE) -C api run
