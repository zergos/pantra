# -*- coding: utf-8 -*-
# Generated by Pony ORM 0.8-dev on 2020-05-13 19:32
from __future__ import unicode_literals

import datetime
from pony import orm
from pony.migrate import diagram_ops as op

dependencies = ['0001_initial']

operations = [
    op.AddEntity('User', ['Entity'], [('created_at', orm.Required(datetime.datetime, sql_default='CURRENT_TIMESTAMP')), ('email', orm.Required(str, unique=True)), ('id', orm.PrimaryKey(int, auto=True)), ('is_admin', orm.Required(bool)), ('name', orm.Required(str)), ('password', orm.Optional(str)), ('salt', orm.Optional(str))]),
    op.AddEntity('App', ['Entity'], [('id', orm.PrimaryKey(int, auto=True)), ('name', orm.Required(str)), ('title', orm.Required(str))]),
    op.ModifyAttr('TestTable', 'Column1', orm.Optional(str, title='������� 1')),
    op.ModifyAttr('TestTable', 'Column2', orm.Optional(str, title='������')),
    op.ModifyAttr('TestTable', 'Column3', orm.Optional(int, title='�����')),
    op.ModifyAttr('TestTable', 'Column4', orm.Optional(float, title='���. �����')),
    op.ModifyAttr('TestTable', 'Column5', orm.Optional(datetime.datetime, title='����/�����')),
    op.AddRelation('User', 'apps', orm.Set('App'), 'users', orm.Set('User'))]