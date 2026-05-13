# Zabbix Dependencies

Python project for monitoring Zabbix network dependencies.

## Features

- Monitor network nodes from Zabbix API
- Automatic node status updates every 3 minutes
- Web dashboard with auto-refresh every 20 seconds
- Admin panel for managing services and configurations

## Models

- **NetworkService** - Network services with relations to Service, Location, Object, and NetworkNode
- **NetworkNode** - Network nodes synced from Zabbix
- **Service** - Service types
- **Location** - Physical locations
- **Object** - Network objects

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set environment variable for Flask:
```bash
export FLASK_ENV=development
```

## Usage

```bash
python app.py
```

Visit http://localhost:5000 to view the dashboard.

## Requirements

- Python 3.11+
- PostgreSQL
- Zabbix API access