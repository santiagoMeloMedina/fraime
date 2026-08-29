.PHONY: install-api run-api define-api publish-api install-sdk publish-sdk publish-sdk-pypi install-mcp run-mcp publish-mcp publish-mcp-pypi

install-api:
	$(MAKE) -C api install

run-api:
	$(MAKE) -C api run

define-api:
	$(MAKE) -C api define

publish-api:
	$(MAKE) -C api publish

install-sdk:
	$(MAKE) -C sdk install

publish-sdk:
	$(MAKE) -C sdk publish

publish-sdk-pypi:
	$(MAKE) -C sdk publish-pypi

install-mcp:
	$(MAKE) -C mcp install

run-mcp:
	$(MAKE) -C mcp run

publish-mcp:
	$(MAKE) -C mcp publish

publish-mcp-pypi:
	$(MAKE) -C mcp publish-pypi
