from app.models import Station, MusicGenre, Decade, Topic, Lang, Mood
from app.api import bp
from flask import request, jsonify
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy import func, case
from app import db
from app.models import station_musicgenres

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


@bp.route('/stations/<int:station_id>/similar', methods=['GET'])
def get_similar_stations(station_id):
    limit = request.args.get('limit', 10, type=int)
    source_station = Station.query.get_or_404(station_id)

    source_genre_ids = {tag.id for tag in source_station.music_genres}
    source_decade_ids = {tag.id for tag in source_station.decades}
    source_topic_ids = {tag.id for tag in source_station.topics}
    source_lang_ids = {tag.id for tag in source_station.langs}
    source_mood_ids = {tag.id for tag in source_station.moods}

    if not any([source_genre_ids, source_decade_ids, source_topic_ids, source_lang_ids, source_mood_ids]):
        return jsonify([])

    score_expression = (
            func.sum(case((MusicGenre.id.in_(source_genre_ids), 5), else_=0)) +
            func.sum(case((Lang.id.in_(source_lang_ids), 4), else_=0)) +
            func.sum(case((Decade.id.in_(source_decade_ids), 3), else_=0)) +
            func.sum(case((Topic.id.in_(source_topic_ids), 2), else_=0)) +
            func.sum(case((Mood.id.in_(source_mood_ids), 1), else_=0))
    ).label("similarity_score")


    query = db.session.query(Station, score_expression) \
        .outerjoin(Station.music_genres) \
        .outerjoin(Station.decades) \
        .outerjoin(Station.topics) \
        .outerjoin(Station.langs) \
        .outerjoin(Station.moods) \
        .filter(Station.id != station_id) \
        .group_by(Station.id) \
        .having(score_expression > 0) \
        .order_by(score_expression.desc()) \
        .limit(limit)

    similar_stations = [station for station, score in query.all()]

    return jsonify(stations_schema.dump(similar_stations))