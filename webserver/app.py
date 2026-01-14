#!/usr/bin/env python3
from flask import Flask, render_template, jsonify
import psycopg2
import os

app = Flask(__name__)

SERVER_ID = os.getenv('SERVER_ID', 'WebServer-Unknown')
DB_PRIMARY_HOST = os.getenv('DB_PRIMARY_HOST', 'db-primary')
DB_STANDBY_HOST = os.getenv('DB_STANDBY_HOST', 'db-standby')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin123')
DB_NAME = os.getenv('DB_NAME', 'monitoring')

def get_db_connection():
    """Tenta conectar ao banco primário, se falhar, conecta ao standby"""
    try:
        conn = psycopg2.connect(
            host=DB_PRIMARY_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=3
        )
        return conn, 'Primary'
    except Exception:
        try:
            conn = psycopg2.connect(
                host=DB_STANDBY_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=3
            )
            return conn, 'Standby'
        except Exception:
            return None, 'None'

def get_latest_metrics():
    """Busca as métricas mais recentes do banco de dados"""
    conn, db_status = get_db_connection()
    
    if not conn:
        return {
            'cpu_usage': 0,
            'memory_usage': 0,
            'memory_total': 0,
            'memory_used': 0,
            'host_ip': 'N/A',
            'ping_latency': 0,
            'timestamp': 'N/A',
            'db_status': db_status
        }
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cpu_usage, memory_usage, memory_total, memory_used, 
                   host_ip, ping_latency, timestamp
            FROM host_metrics
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                'cpu_usage': float(result[0]),
                'memory_usage': float(result[1]),
                'memory_total': int(result[2]),
                'memory_used': int(result[3]),
                'host_ip': result[4],
                'ping_latency': float(result[5]),
                'timestamp': result[6].strftime('%Y-%m-%d %H:%M:%S'),
                'db_status': db_status
            }
        
        return {
            'cpu_usage': 0,
            'memory_usage': 0,
            'memory_total': 0,
            'memory_used': 0,
            'host_ip': 'N/A',
            'ping_latency': 0,
            'timestamp': 'N/A',
            'db_status': db_status
        }
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return {
            'cpu_usage': 0,
            'memory_usage': 0,
            'memory_total': 0,
            'memory_used': 0,
            'host_ip': 'N/A',
            'ping_latency': 0,
            'timestamp': 'N/A',
            'db_status': 'Error'
        }

@app.route('/')
def index():
    """Renderiza a página principal"""
    metrics = get_latest_metrics()
    return render_template('index.html', server_id=SERVER_ID, **metrics)

@app.route('/api/metrics')
def api_metrics():
    """Endpoint API para obter métricas atualizadas"""
    metrics = get_latest_metrics()
    metrics['server_id'] = SERVER_ID
    return jsonify(metrics)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)