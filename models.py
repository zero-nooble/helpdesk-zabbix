from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __str__(self):
        return self.name

class Object(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)

    location = db.relationship('Location', backref='objects')

    def __str__(self):
        return self.name

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    def __str__(self):
        return self.name

class NetworkNode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    zabbix_host_id = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.String(20), default='unknown')
    unavailable_since = db.Column(db.DateTime, nullable=True)

    def __str__(self):
        return self.name

class NetworkService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    object_id = db.Column(db.Integer, db.ForeignKey('object.id'), nullable=False)
    node_id = db.Column(db.Integer, db.ForeignKey('network_node.id'), nullable=False)

    service = db.relationship('Service', backref='network_services')
    location = db.relationship('Location', backref='network_services')
    object = db.relationship('Object')
    node = db.relationship('NetworkNode', backref='network_services')

    def __str__(self):
        return f'{self.name} - {self.service.name}'