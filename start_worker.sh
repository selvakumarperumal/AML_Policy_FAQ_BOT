#!/bin/bash
celery -A app.celery_backend.app.celery_app:celery_app worker --beat --loglevel=info --pool=solo