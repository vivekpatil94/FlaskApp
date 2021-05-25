#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import os
import unittest
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from app import app
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class AgencyTestCase(unittest.TestCase):

    """This class represents the agency's test case"""

    def setUp(self):
        """Define test variables and initialize app."""

        self.app = app
        self.client = self.app.test_client
        self.database_name = 'mylabs_test'
        self.database_path = 'postgresql://{}:{}@{}/{}'.format(
                             'postgres', 'admin',
                             'localhost:5432', self.database_name)
    
        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            self.db.drop_all()

            # create all tables
            self.db.create_all()


if __name__ == '__main__':
    unittest.main()