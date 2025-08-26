# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Import Initial Data

python manage.py import_questions resources/json_input_files/ --workers=8 --batch-size=100 --pre-create-hierarchy


## 📊 Performance Optimization

### 1. Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_questions_facet ON questions(facet_id);
CREATE INDEX idx_user_responses_user_question ON user_responses(user_id, question_id);
CREATE INDEX idx_spaced_cards_due ON spaced_repetition_cards(user_id, due_date);
CREATE INDEX idx_sessions_user_status ON learning_sessions(user_id, status);

-- Partition large tables
ALTER TABLE learning_events PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027)
);
```

### 2. Caching Strategy

```python
# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            'MAX_CONNECTIONS': 1000,
            'PICKLE_VERSION': -1,
        },
    }
}

# Cache warming script
python manage.py warm_cache --models questions,facets --users active
```

### 3. API Rate Limiting

```nginx
# nginx.conf
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;
    
    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend:8000;
        }
        
        location /api/v1/auth/ {
            limit_req zone=auth burst=5 nodelay;
            proxy_pass http://backend:8000;
        }
    }
}
```


## 🛠️ Maintenance Commands

```bash
# Daily maintenance
python manage.py cleanup_sessions --days 30
python manage.py calculate_statistics
python manage.py send_reminders

# Weekly maintenance
python manage.py optimize_database
python manage.py backup_database
python manage.py analyze_performance

# Monthly maintenance
python manage.py archive_old_data
python manage.py generate_reports
```

## 📚 API Documentation

- **OpenAPI/Swagger**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Admin Panel**: http://localhost:8000/admin
- **Monitoring**: http://localhost:3000 (Grafana)


4. **Performance issues**
   ```bash
   # Profile slow queries
   python manage.py debugsqlshell
   # Check cache hit rate
   python manage.py cache_stats
   ```
