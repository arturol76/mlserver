#!/bin/sh
uvicorn --reload --host 0.0.0.0 --port 5001 --ssl-keyfile=${SSL_KEYFILE} --ssl-certfile=${SSL_CERTFILE} api:app