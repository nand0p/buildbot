# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

from random import choice
from string import ascii_lowercase
import sqlalchemy as sa
from twisted.trial import unittest
from buildbot.test.util import migration
from buildbot.util import sautils


class Migration(migration.MigrateTestMixin, unittest.TestCase):

    def setUp(self):
        return self.setUpMigrateTest()

    def tearDown(self):
        return self.tearDownMigrateTest()

    def create_table_thd(self, conn):
        metadata = sa.MetaData()
        metadata.bind = conn

        change_properties = sautils.Table(
            'change_properties', metadata,
            sa.Column('changeid', sa.Integer, nullable=False),
            sa.Column('property_name', sa.String(256), nullable=False),
            sa.Column('property_value', sa.String(1024), nullable=False),
        )

        change_properties.create()

    def test_update(self):
        def setup_thd(conn):
            self.create_table_thd(conn)

        def verify_thd(conn):
            metadata = sa.MetaData()
            metadata.bind = conn
            random_length = 4096
            random_string = ''.join(choice(ascii_lowercase) for byte in range(random_length))

            # Test column type is text
            change_properties = sautils.Table('change_properties', metadata, autoload=True)
            self.assertIsInstance(change_properties.c.property_value.type, sa.Text)

            # Test insert random string
            conn.execute(change_properties.insert(), [
                dict(changeid=1,
                     property_name="test_change_properties_property_value_length",
                     property_value=random_string),
            ])

            # Test db string length
            # Using raw sql due to error via sa
            # q = conn.execute(sa.select([sa.func.length(change_properties.c.property_value)]).where(changeid==1))
            q = conn.execute("select length(property_value) from change_properties where changeid == 1")
            [self.assertEqual(q_length[0], random_length) for q_length in q]

        return self.do_test_migration(47, 48, setup_thd, verify_thd)
