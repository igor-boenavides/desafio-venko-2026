-- Função: Cria a tabela no banco de dados quando ele é iniciado pela primeira vez.

-- Tabela para armazenar métricas de monitoramento
CREATE TABLE IF NOT EXISTS host_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    memory_total BIGINT,
    memory_used BIGINT,
    host_ip VARCHAR(50),
    ping_latency DECIMAL(10,2)
);

-- Índice para melhor performance nas consultas
CREATE INDEX IF NOT EXISTS idx_timestamp ON host_metrics(timestamp DESC);

-- Inserir dados iniciais
INSERT INTO host_metrics (cpu_usage, memory_usage, memory_total, memory_used, host_ip, ping_latency)
VALUES (0.0, 0.0, 0, 0, 'Inicializando...', 0.0);