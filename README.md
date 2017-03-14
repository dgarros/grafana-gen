
**grafana-gen** is a CLI tool to automate the creation of Grafana Dashboards.
It's eavily based on Jinja2 templates and Yaml file.

# Install
```
sudo python setup.py develop
```

# Generate Dashboard

```
grafana-gen --file aos_device.yaml --out-file
```

## Outputs

**grafana-gen** can either:
- `--out-file` Save the newly generated Dashboard in JSON on the local file system
- `--out-server` Upload the newly generated Dashboard to a grafana server. (if a dashboard with the same name already exist it will overwrite it)

## Usage

```
usage: grafana-gen [-h] [--file DASHBOARD] [--out-file] [--out-server]
                   [--server SERVER] [--login LOGIN] [--password PASSWORD]
                   [--log LEVEL]

Process user input

optional arguments:
  -h, --help           show this help message and exit
  --file DASHBOARD     Definition file for the dashboard to create
  --out-file           Save Dashboard to a JSON file on the local directory
  --out-server         Upload Dashboard to a Grafana server
  --server SERVER      Address of a grafana server to upload the dashboard
  --login LOGIN        Login to connect to a grafana server
  --password PASSWORD  Password to connect to a grafana server
  --log LEVEL          Specify the log level
```
