# TeSS-Metadata-Extractor-Agent

[![DOI](https://zenodo.org/badge/1235451518.svg)](https://doi.org/10.5281/zenodo.20159522)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
![python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue?style=flat)
[![CI](https://github.com/kennethrioja/TeSS-Metadata-Extractor-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/kennethrioja/TeSS-Metadata-Extractor-Agent/actions/workflows/ci.yml)


A metadata extractor agent to augment the metadata retrieval of any TeSS training resource

## Workflow

1. **User provides URL**: The user inputs the URL of the training resource they want to extract metadata from.
2. **Scraper retrieves content**: The scraper fetches the content of the provided URL and removes the links.
3. **Extractor processes content**: The extractor analyzes the content and returns relevant metadata.

For keywords, we use first a Regex based extractor that will keep relevant keywords from the defined list of keywords (i.e., `known_keywords.json`), then an LLM is used as a judge to review whether these keywords are relevant to the materials.
Removing links during the scraping process helps the Regex counter not to count relevant words in the links (e.g., we saw a lot of github hits).

## Run it locally

Prerequisites:
- Python >= 3.12, < 3.14
- [pdm](https://pdm-project.org/en/latest/)

Steps:

1. `cp config/config.yaml.example config/config.yaml`
2. `cp .env.example .env` and add your API keys
3. `pdm install`
4. `source .venv/bin/activate`
5. `python src/full_metadata_pipeline.py`

## Licence

CC-BY-4.0 – Attribution 4.0 International

## Authors

- Hugo Bacard ([LinkedIn](https://www.linkedin.com/in/hbacard/))
  - Roles: Software Engineering, AI Ops
  - Tasks: designed infrastructure, coded python module (scraper, regex, counters, LLM)

- Kenneth Rioja ([LinkedIn](https://www.linkedin.com/in/kennethrioja/))
  - Roles: Software Engineering, Dev Ops, Training infrastructure expert
  - Tasks: initiated project, designed infrastructure, interfaced this Metadata Extractor Agent with TeSS, made sure the output corresponds to what TeSS can ingest, created a Docker container containing this code to work with TeSS, wrote documentation, took care of the user experience

## Funding

This project has received funding from the European Union’s Horizon Europe Programme under GA 101129744 — EVERSE — HORIZON-INFRA-2023-EOSC-01-02
