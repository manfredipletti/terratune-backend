from app.models import Station, MusicGenre, Decade, Topic, Lang, Mood
from app.api import bp
from flask import request, jsonify
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

ma = Marshmallow(bp)


class MusicGenreSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MusicGenre
        fields = ("name",)


class DecadeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Decade
        fields = ("name",)


class TopicSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Topic
        fields = ("name",)


class LangSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Lang
        fields = ("name",)


class MoodSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Mood
        fields = ("name",)


class StationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Station
        load_instance = True
        include_fk = True

    music_genres = ma.Nested(MusicGenreSchema, many=True)
    decades = ma.Nested(DecadeSchema, many=True)
    topics = ma.Nested(TopicSchema, many=True)
    langs = ma.Nested(LangSchema, many=True)
    moods = ma.Nested(MoodSchema, many=True)


station_schema = StationSchema()
stations_schema = StationSchema(many=True)



@bp.route('/stations', methods=['GET'])
def get_stations():
    """Endpoint per cercare e filtrare le stazioni."""

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Station.query

    search_term = request.args.get('search')
    if search_term:
        query = query.filter(Station.name.ilike(f'%{search_term}%'))

    filter_map = {
        'genre': (Station.music_genres, MusicGenre),
        'decade': (Station.decades, Decade),
        'topic': (Station.topics, Topic),
        'lang': (Station.langs, Lang),
        'mood': (Station.moods, Mood),
        'countrycode': (Station.countrycode, None)  # Filtro diretto
    }

    for arg, (relationship, model) in filter_map.items():
        if request.args.get(arg):
            values = request.args.get(arg).split(',')
            if model:
                query = query.join(relationship).filter(model.name.in_(values))
            else:
                query = query.filter(relationship.in_(values))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    stations = pagination.items

    result = stations_schema.dump(stations)

    return jsonify({
        'items': result,
        'total_items': pagination.total,
        'total_pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })