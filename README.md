# 20252R0136COSE40700
20252R0136COSE40700 Final assignment


project/
  app/
    main.py
    database.py
    models.py
    routers/
      __init__.py
      exchange.py
      news.py
      backup.py
      ui.py
  static/
    index.html
  data/                # (호스트/볼륨에 마운트 권장)
  requirements.txt
  Dockerfile
  docker-compose.yml
  k8s/
    deployment.yaml
    service.yaml
    pvc.yaml
    cronjob.yaml
