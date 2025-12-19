# 20252R0136COSE40700
20252R0136COSE40700 Final assignment


project/
  app/
    main.py : app entry point
    database.py 
    models.py : define ORM models 
    routers/
      __init__.py
      exchange.py
      news.py
      backup.py
      ui.py
  static/
    index.html
  data/                
  requirements.txt
  Dockerfile : container build script
  docker-compose.yaml : local/server's distribution compose  
  k8s/
    deployment.yaml : fastapi
    service.yaml : DNS
    pvc.yaml : DB backup
    cronjob.yaml : scheduler
