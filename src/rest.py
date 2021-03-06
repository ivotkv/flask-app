from flask import request
from flask_restful import Api, Resource

from . import models
from .crud import CRUDable
from .app import app
from .db import db

api = Api(app)


class DatabaseResource(Resource):
    @property
    def model(self):
        return getattr(models, self.__class__.__name__)

    def get(self, id=None):
        if id is None:
            query = self.model.query
            field_names = self.model.get_field_names()
            for key, value in request.args.items():
                if key in field_names:
                    col_type = type(getattr(self.model, key).property.columns[0].type)
                    if col_type is db.Integer and value.isdigit():
                        query = query.filter(getattr(self.model, key) == int(value))
            return [i.read() for i in query.all()], 200
        else:
            try:
                return self.model.query.filter_by(id=id).one().read(), 200
            except db.NoResultFound:
                return {}, 404

    def post(self):
        entity = self.model.create(request.json)
        db.session.commit()
        return entity.read(), 201

    def delete(self, id):
        try:
            self.model.query.filter_by(id=id).one().delete()
            db.session.commit()
            return {}, 204
        except db.NoResultFound:
            return {}, 404

    def put(self, id):
        try:
            entity = self.model.query.filter_by(id=id).one()
            entity.update(request.json)
            db.session.commit()
            return entity.read(), 200
        except db.NoResultFound:
            return {}, 404


for model_name in (
    name
    for name in dir(models)
    if (
        isinstance(getattr(models, name), type)
        and issubclass(getattr(models, name), db.Model)
        and issubclass(getattr(models, name), CRUDable)
    )
):
    api.add_resource(
        type(model_name, (DatabaseResource,), {}),
        '/{0}'.format(model_name.lower()),
        '/{0}/<int:id>'.format(model_name.lower()),
    )
