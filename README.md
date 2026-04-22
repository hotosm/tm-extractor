# TM Extractor

The **TM Extractor** script is designed to trigger extraction requests for Tasking Manager projects. It utilizes the HOTOSM Tasking Manager API and the Raw Data API for data extraction. For more complex queries navigate to [osm-rawdata module](https://github.com/hotosm/osm-rawdata/)


## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Command Line](#command-line)
  - [AWS Lambda](#aws-lambda)
  - [Streamlit APP](#streamlit)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Config JSON](#config-json)
- [Releasing](#releasing)
- [Script Overview](#script-overview)
- [Result Path](#result-path)

## Getting Started

### Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Access token for Raw Data API

### Installation

The package is published on PyPI. The fastest path requires no cloning and no manual install, `uvx` fetches the package into an ephemeral environment and runs it:

```bash
uvx tm-extractor --fetch-active-projects 24
```

For local development, clone and sync:

```bash
git clone https://github.com/kshitijrajsharma/TM-Extractor
cd TM-Extractor
uv sync
```

## Usage

### Command Line

Head over to [Env](#environment-variables) to verify you have setup correct env variables & run the command with the following options:

- For Specific TM Projects :

```bash
uvx tm-extractor --projects 123 456 789
```

- For fetching active projects within last 24hr

```bash
uvx tm-extractor --fetch-active-projects 24
```

- For tracking request and Dumping result

```bash
uvx tm-extractor --projects 123 --track
```

During local development, swap `uvx tm-extractor` for `uv run tm-extractor` to use the checked-out source.

You can set it up as systemd service or cronjob in your PC if required or run manually.

### AWS Lambda

1. **Create an AWS Lambda Function:**

   - In the AWS Management Console, navigate to the Lambda service, Choose role and create one with necessary permissions

2. **Set Environment Variables:**

   - Add the following environment variables to your Lambda function configuration:

     - `CONFIG_JSON`: [Optional] Path to a custom config JSON file. If unset, the packaged default bundled inside `tm-extractor` is used.
     - Refer to [Configurations](#configuration) for more env variables as required

3. **Deploy the Script as a Lambda Function:**

   - Build a deployment bundle with `uv pip install --target ./package 'tm-extractor'` (add `[sentry]` for Sentry support).
   - Zip the contents of `./package` together with any custom `config.json` override and upload to your Lambda function.
   - Set the handler to `tm_extractor.lambda_handler`.

4. **Configure Lambda Trigger:**

   - Configure an appropriate event source for your Lambda function. This could be an API Gateway, CloudWatch Event, or another trigger depending on your requirements.

5. **Invoke the Lambda Function:**

   - Trigger the Lambda function manually or wait for the configured event source to invoke it. Event shape: `{"fetch_active_projects": 24}` or `{"projects": [123, 456]}`.

   Your Lambda function should be able to execute the script with the provided configurations.

### Using Terraform

1. **Download & install Terraform:**

   - Install terraform from the [HashiCorp install guide](https://developer.hashicorp.com/terraform/install).

2. **Create AWS Credentials**

   - Create an IAM programmatic user :

     - Configure .aws/credentials or use AWS Environment varibles for terraform authentication. [Check Here](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

3. **Environment Variables**
You can set terraform input variables using `TF_VAR_<varible-name-from-vars.tf>` if you don't want to provide them each time.

4. **Run Terraform Plan/Apply**
   - Run `terraform init` to download required providers
   - Run `terraform plan` plan to check for infrastructure changes.
   - Run `terraform apply` to apply terraform configurations.

> **_NOTE:_**  Check `main.tf` for resources terraform creates.

### Streamlit

The Streamlit frontend lives in this repo but is not shipped in the PyPI package.

1. Run locally :

   ```bash
   uv run --with streamlit streamlit run streamlit_app.py
   ```

1. To use hosted service : Go to [tm-extractor.streamlit.app](https://tm-extractor.streamlit.app/)

## Configuration

### Environment Variables

Set the following environment variables for proper configuration. `.env` files in the working directory are loaded automatically.

Example :

```bash
export RAWDATA_API_AUTH_TOKEN='my_token'
```

- **`RAWDATA_API_AUTH_TOKEN`**: API token for Raw Data API authentication, Request admins for yours to [RAW DATA API](https://github.com/hotosm/raw-data-api/)

- **`RAW_DATA_API_BASE_URL`**: Base URL for the Raw Data API. Default is `https://api-prod.raw-data.hotosm.org/v1`.

- **`TM_API_BASE_URL`**: Base URL for the Tasking Manager API. Default is `https://tasking-manager-production-api.hotosm.org/api/v2`.

- **`CONFIG_JSON`**: Path to a custom config JSON file. If unset, the default `config.json` bundled inside the package is used.

- **`TASKING_MANAGER_API_KEY`**: [Optional] Tasking manager API key . Example : `Token your_token_key_from_tasking_manager`. Only required to fetch projects that requires authentication.

- **`SENTRY_DSN`**: [Optional] Enables Sentry error reporting. Install with the `[sentry]` extra: `uvx --from 'tm-extractor[sentry]' tm-extractor ...`.

### Config JSON

The `config.json` file contains configuration settings for the extraction process. It includes details about the dataset, categories, and geometry of the extraction area. A default `config.json` ships inside the package ([`src/tm_extractor/config.json`](src/tm_extractor/config.json)) and is used automatically when no override is provided; pass `--config path/to/config.json` or set `CONFIG_JSON=...` to override.

```json
{
    "geometry": {...},
    "dataset": {...},
    "categories": [...]
}
```

### Explanation

#### `geometry`

Defines the geographical area for extraction. Typically auto-populated with Tasking Manager (TM) geometry.

#### `queue`

Specifies the Raw Data API queue, often set as "raw_default" for default processing, This can be changed if there is disaster activation and special services are deployed so that those requests can be prioritized.

#### `dataset`

Contains information about the dataset:

- `dataset_prefix`: Prefix for the dataset extraction eg : hotosm_project_123.
- `dataset_folder`: Default Mother folder to place during extraction eg : TM , Mindful to change this.
- `dataset_title`: Title of the Tasking Manager project eg : Tasking Manger Project 123.

#### `categories`

Array of extraction categories, each represented by a dictionary with:

- `Category Name`: Name of the extraction category (e.g., "Buildings", "Roads").
  - `types`: Types of geometries to extract (e.g., "polygons", "lines", "points").
  - `select`: Attributes to select during extraction (e.g., "name", "highway", "surface").
  - `where`: Conditions for filtering the data during extraction (e.g., filtering by tags).
  - `formats`: File formats for export (e.g., "geojson", "shp", "kml").

Adjust these settings based on your project requirements and the types of features you want to extract.

Refer to the sample [config.json](src/tm_extractor/config.json) for default config.

## Releasing

Versioning is managed by [commitizen](https://commitizen-tools.github.io/commitizen/) using [conventional commits](https://www.conventionalcommits.org/).

```bash
uv run cz bump          # bumps version in pyproject.toml, updates CHANGELOG.md, creates v$version tag
git push --follow-tags  # push the tag, then create a GitHub Release to trigger PyPI publish
```

The `publish.yml` workflow builds with `uv build` and publishes to PyPI on release.

## Script Overview

### Purpose

The script is designed to trigger extraction requests for Tasking Manager projects using the Raw Data API. It automates the extraction process based on predefined configurations.

### Features

- Supports both command line and AWS Lambda execution.
- Dynamically fetches project details, including mapping types and geometry, from the Tasking Manager API.
- Configurable extraction settings using a `config.json` file.
- Helps debugging the service and track the api requests

## Result Path

- Your export download link will be generated based on the config , with raw-data-api logic it will be ```Base_download_url```/```dataset_folder```/```dataset_prefix```/```Category_name```/```feature_type```/```dataset_prefix_category_name_export_format.zip```
- Example for Waterways configuration :
Here Category Name is ```Waterways```, dataset_prefix is ```hotosm_project_9```, dataset_folder is ```TM``` , feature_type is ```lines``` and export format is ```geojson```

```json
"Waterways": {
    "resources": [
    {
        "name": "hotosm_project_9_waterways_lines_geojson.zip",
        "format": "geojson",
        "description": "GeoJSON",
        "url": "https://s3.sample.your_domain.org/TM/hotosm_project_9/waterways/lines/hotosm_project_9_waterways_lines_geojson.zip",
        "last_modifed": "2023-12-28T17:48:21.378667"
    },
    ]
}
```

See [sample result](./sample_result.json) to go through how result will look like
