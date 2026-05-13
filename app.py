from flask import Flask, render_template, redirect, url_for, flash, request
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from wtforms import StringField, TextAreaField
from pyzabbix import ZabbixAPI
from datetime import datetime
from collections import defaultdict
import os
import atexit
from models import db, NetworkNode, Service, NetworkService, Object, Location
from config import config
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

db.init_app(app)

# Zabbix config
ZABBIX_URL = 'http://172.16.0.242/zabbix/api_jsonrpc.php'
ZABBIX_TOKEN = 'b6a5c318ce17688577a076d7706986b3dae30e2e4bce2ea0bf121147dfaedefa'

def update_zabbix_nodes():
    """Update nodes from Zabbix API"""
    with app.app_context():
        try:
            zapi = ZabbixAPI(ZABBIX_URL)
            zapi.login(api_token=ZABBIX_TOKEN)

            hosts = zapi.host.get(output=['hostid', 'name'], selectInterfaces=['available'])

            updated_count = 0
            for host in hosts:
                host_id = host['hostid']
                name = host['name']
                status = 'available'
                for interface in host.get('interfaces', []):
                    if interface.get('available') == '2':
                        status = 'unavailable'
                        break

                node = NetworkNode.query.filter_by(zabbix_host_id=host_id).first()
                if node:
                    if node.status != status:
                        if status == 'unavailable':
                            node.unavailable_since = datetime.utcnow()
                        else:
                            node.unavailable_since = None
                        node.status = status
                        updated_count += 1
                else:
                    unavailable_time = datetime.utcnow() if status == 'unavailable' else None
                    node = NetworkNode(name=name, zabbix_host_id=host_id, status=status, unavailable_since=unavailable_time)
                    db.session.add(node)
                    updated_count += 1

            db.session.commit()
            print(f'[{datetime.utcnow()}] Updated {updated_count} nodes from Zabbix')
        except Exception as e:
            print(f'[{datetime.utcnow()}] Error updating from Zabbix: {str(e)}')

scheduler = BackgroundScheduler()
scheduler.add_job(func=update_zabbix_nodes, trigger='interval', minutes=3)
scheduler.start()

# Custom form for NetworkNode
class NetworkNodeForm(SecureForm):
    name = StringField('Name')
    zabbix_host_id = StringField('Zabbix Host ID')
    unavailable_since = StringField('Unavailable Since')

class NetworkNodeView(ModelView):
    form = NetworkNodeForm
    column_searchable_list = ['name', 'zabbix_host_id', 'status']
    column_list = ['id', 'name', 'zabbix_host_id', 'status', 'unavailable_since']

# Custom form for Location
class LocationForm(SecureForm):
    name = StringField('Name')

class LocationView(ModelView):
    form = LocationForm
    column_list = ['id', 'name']
    column_searchable_list = ['name']

# Object view with AJAX lookups for Location
class ObjectView(ModelView):
    column_list = ['id', 'name', 'location']
    column_searchable_list = ['name']
    form_ajax_refs = {
        'location': {
            'fields': ['name'],
            'page_size': 10
        }
    }

# Custom form for Service
class ServiceForm(SecureForm):
    name = StringField('Name')
    description = TextAreaField('Description')

class ServiceView(ModelView):
    form = ServiceForm
    column_list = ['id', 'name', 'description']
    column_searchable_list = ['name', 'description']

class NetworkServiceView(ModelView):
    column_list = ['name', 'service', 'location', 'object', 'node']
    column_searchable_list = ['name']
    form_columns = ['name', 'service', 'location', 'object', 'node']
    form_ajax_refs = {
        'service': {
            'fields': ['name'],
            'page_size': 10
        },
        'location': {
            'fields': ['name'],
            'page_size': 10
        },
        'object': {
            'fields': ['name'],
            'page_size': 10
        },
        'node': {
            'fields': ['name'],
            'page_size': 10
        }
    }

admin = Admin(app, name='Zabbix Monitor Admin', template_mode='bootstrap3')
admin.add_view(LocationView(Location, db.session))
admin.add_view(ObjectView(Object, db.session))
admin.add_view(NetworkNodeView(NetworkNode, db.session))
admin.add_view(ServiceView(Service, db.session))
admin.add_view(NetworkServiceView(NetworkService, db.session))

@app.route('/')
def index():
    # Get unavailable services grouped by Location
    unavailable_services = defaultdict(list)
    network_services = NetworkService.query.join(NetworkNode).filter(NetworkNode.status == 'unavailable').all()
    
    for ns in network_services:
        location_name = ns.location.name if ns.location else 'Unknown'
        unavailable_services[location_name].append({
            'service': ns.service,
            'object': ns.object,
            'network_service': ns,
            'node': ns.node,
            'unavailable_since': ns.node.unavailable_since
        })
    
    return render_template('index.html', services_by_location=unavailable_services)

@app.route('/update')
def update_nodes():
    update_zabbix_nodes()
    flash('Nodes updated from Zabbix', 'success')
    return redirect(url_for('index'))

atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5070, debug=True)