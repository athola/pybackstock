import os
import sys
import io
import csv
import json
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, func

inventoryApp = Flask(__name__)
inventoryApp.config.from_object(os.environ.get('APP_SETTINGS', 'config.DevelopmentConfig'))
inventoryApp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(inventoryApp)

from models import Grocery

@inventoryApp.route('/', methods=['GET', 'POST'])
def index():
	errors = []
	items = []
	col = 'ID'
	load_search = False
	load_add_item = True
	load_add_csv = False
	item_searched = False
	item_added = False
	if request.method == 'POST':
		if 'search-item' in request.form:
			load_search = True
			load_add_item = False
			load_add_csv = False
			return render_template('index.html', errors = errors, items=items, column=col, loading_search=load_search, loading_add_item=load_add_item, loading_add_csv=load_add_csv, item_searched=item_searched, item_added=item_added)
		elif 'add-item' in request.form:
			load_search = False
			load_add_item = True
			load_add_csv = False
			return render_template('index.html', errors = errors, items=items, column=col, loading_search=load_search, loading_add_item=load_add_item, loading_add_csv=load_add_csv, item_searched=item_searched, item_added=item_added)
		elif 'add-csv' in request.form:
			load_search = False
			load_add_item = False
			load_add_csv = True
			return render_template('index.html', errors = errors, items=items, column=col, loading_search=load_search, loading_add_item=load_add_item, loading_add_csv=load_add_csv, item_searched=item_searched, item_added=item_added)
		elif 'send-search' in request.form:
			load_search = True
			load_add_item = False
			load_add_csv = False
			item_searched = True
			item_added = False
			try:
				col = request.form['column']
				item = request.form['item']
				matching_items = get_matching_items(col, item)
				for item in matching_items:
					items.append(item)
			except Exception as ex:
				error_type = 'Unable to search for item. Please double check your search parameters. '
				errors = report_exception(ex, error_type, errors)
		elif 'send-add' in request.form:
			load_search = False
			load_add_item = True
			load_add_csv = False
			item_searched = False
			try:
				item = set_item()
				errors, items = add_item(item, errors, items)
				item_added = True
			except Exception as ex:
				error_type = 'Unable to add item. Please double check your item parameters. '
				errors = report_exception(ex, error_type, errors)
		elif 'csv-submit' in request.form:
			load_search = False
			load_add_item = False
			load_add_csv = True
			item_searched = False
			try:
				file = request.files['csv-input']
				if not file:
					errors.append('No file')
				if '.' in file.filename:
					file_ext = file.filename.rsplit('.', 1)[1].lower()
				else:
					errors.append('Invalid file type. Needs to be .csv')
				if (file_ext == 'csv'):
					stream = io.StringIO(file.stream.read().decode('UTF8'), newline=None)
					csv_input = csv.reader(stream)
					iterate_through_csv(csv_input, errors, items)
				else:
					errors.append('Invalid file type. Needs to be .csv')
			except Exception as ex:
				error_type = 'Unable to add item. Please double check your item parameters. '
				errors = report_exception(ex, error_type, errors)
	item_length = len(items)
	return render_template('index.html', errors = errors, items=items, column=col, loading_search=load_search, loading_add_item=load_add_item, loading_add_csv=load_add_csv, item_searched=item_searched, item_added=item_added, )
	
def report_exception(ex, error_type, errors):
	error_str = error_type + str(ex) + ' - Error on line no: {}'.format(sys.exc_info()[-1].tb_lineno)
	errors.append(error_str)
	for error in errors:
		print (error)
	return errors

def get_matching_items(search_column, search_item):
	if ('DROP TABLE' in search_item):
		return {}
	if search_column == 'id':
		if search_item.isdigit():
			return Grocery.query.filter(Grocery.id == int(search_item))
		else:
			return {}
	elif search_column == 'x_for':
		if search_item.isdigit():
			return Grocery.query.filter(Grocery.x_for == int(search_item))
		else:
			return {}
	elif '*' in search_item or '_' in search_item: 
		search_term = search_item.replace('_', '__')\
							.replace('*', '%')\
							.replace('?', '_')
	elif search_item[-1] == 's':
		search_term = search_item[0:len(search_item) - 1]
		search_term = '%{0}%'.format(search_term)
	else:
		search_term = '%{0}%'.format(search_item)
	if search_column == 'last_sold':
		return Grocery.query.filter(func.to_char(Grocery.last_sold, '%YYYY-MM-DD%').ilike(search_term,)).order_by(Grocery.id)
	return Grocery.query.filter(getattr(Grocery, search_column).ilike(search_term,)).order_by(Grocery.id)

def set_item():
	id = int(request.form['id-add'])
	description = request.form['description-add']
	last_sold = request.form['last-sold-add']
	shelf_life = request.form['shelf-life-add']
	department = request.form['department-add']
	price = request.form['price-add']
	unit = request.form['unit-add']
	x_for = request.form['xfor-add']
	cost = request.form['cost-add']
	item_to_add = Grocery(id=id,
		description=description,
		last_sold=last_sold,
		shelf_life=shelf_life,
		department=department,
		price=price,
		unit=unit,
		x_for=x_for,
		cost=cost,
	)
	return item_to_add

def add_item(item, errors, items):
	try:
		# SQLAlchemy 2.0 compatible exists check
		item_exists = db.session.query(Grocery).filter(Grocery.id == item.id).first() is not None
		if not item_exists:
			db.session.add(item)
			db.session.commit()
			json_obj = json.dumps(dict(item))
			items.append(json_obj)
		else:
			errors.append('Unable to add item to database. This item has already been added with ID: ' + str(item.id))
	except Exception as ex:
		db.session.rollback()
		errors.append('Unable to add item to database. ' + str(ex))
	return errors, items
	
def iterate_through_csv(input, errors, items):
	count = 0
	for row in input:
		if count != 0:
			csv_item_to_add = Grocery(id=row[0],
				description=row[1],
				last_sold=row[2],
				shelf_life=row[3],
				department=row[4],
				price=row[5],
				unit=row[6],
				x_for=row[7],
				cost=row[8],
			)
			add_item(csv_item_to_add, errors, items)
		count+=1