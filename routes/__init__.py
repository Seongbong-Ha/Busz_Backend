from .station_routes import station_bp

def register_routes(app):
    """버스 도착 정보 리스트 REST API 라우트 등록"""
    app.register_blueprint(station_bp, url_prefix='/api')
    print("REST API 등록 완료")