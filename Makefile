SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help check

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  make %-12s %s\n", $$1, $$2}'

check: ## Verify relative links, heading anchors, and status markers across every Markdown file
	python3 scripts/check_docs.py
