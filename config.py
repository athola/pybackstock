import os
import secrets

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	DEBUG = False
	TESTING = False
	CSRF_ENABLED = True
	# Use environment variable for SECRET_KEY, fall back to generated secret for development
	SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
	# Handle both old and new PostgreSQL URI formats
	database_url = os.environ.get('DATABASE_URL', '')
	if database_url.startswith('postgres://'):
		database_url = database_url.replace('postgres://', 'postgresql://', 1)
	SQLALCHEMY_DATABASE_URI = database_url
	
class ProductionConfig(Config):
	DEBUG = False
	
class StagingConfig(Config):
	DEVELOPMENT = True
	DEBUG = True
	
class DevelopmentConfig(Config):
	DEVELOPMENT = True
	DEBUG = True
	
class TestingConfig(Config):
	TESTING = True