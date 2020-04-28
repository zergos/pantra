#!/usr/bin/env python
import db.models
import core.defaults as settings

db.models.db.migrate(migration_dir=settings.MIGRATION_PATH, **settings.DB_PARAMS)
