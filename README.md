# Quickstart

## Environment variables

A 'dotenv' file is used to store environment variables that configure the app. An example file is provided that must be copied to '.env' as it will be used to keep local configuration changes that should not be committed to the repository.

Copy the dotenv example file.
```
cp env.example .env
```

## Development

For development the app should be run with Flask because it provides a debug mode and automatic reloading when source files change.

Install Python 3.11+.

Create a virtual environment.

```
python -m venv .venv

# Activate venv in Linux and MacOS
source .venv/bin/activate
# Windows - cmd.exe
venv\Scripts\activate.bat
# Windows - PowerShell
venv\Scripts\Activate.ps1

pip install --upgrade pip
```

Install the app dependencies.

```
pip install -e '.[dev]'
```

Start the app server.
```
flask -A pbdm_app.app -e .env --debug run
```

The app should be available at [http://localhost:5000/](http://localhost:5000/).


## Testing

To run the app as it would be when deployed in a production setting, use Docker Compose.

[Install Docker Compose].

Start the app.
```
docker compose up -d
```

The app should be available at [http://localhost:8000/](http://localhost:8000/).

Tail the logs.
```
docker compose logs -f
```

Shut down the app.
```
docker compose down
```


[Install Docker Compose]: https://docs.docker.com/compose/install/
