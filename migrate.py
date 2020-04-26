#!/usr/bin/env python
import db.models
import core.defaults as settings

db.models.db.migrate(migration_dir=settings.migration_dir, **settings.db_params)
