CREATE TABLE IF NOT EXISTS component_stats (
    component VARCHAR(50) PRIMARY KEY,
    requests INT DEFAULT 0,
    errors INT DEFAULT 0,
    avg_response DOUBLE DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS metrics (
    id INT PRIMARY KEY AUTO_INCREMENT, -- أو بدونه إذا كان جدول من سطر واحد فقط
    total_requests INT DEFAULT 0,
    error INT DEFAULT 0,
    avg_response DOUBLE DEFAULT 0.0
);

-- كودك بالـ update_metric بيعمل SELECT أولاً، فلو الجدول فاضي تماماً رح يرجع None وتعمل مشاكل.
-- يفضل تحط سطر مبدئي بقيم أصفار:
INSERT INTO metrics (total_requests, error, avg_response) 
SELECT 0, 0, 0.0 
WHERE NOT EXISTS (SELECT 1 FROM metrics);

-- تجهيز المكونات الأربعة اللي كود الـ MetricsCalculator بيعرفها
INSERT INTO component_stats (component, requests, errors, avg_response) VALUES
('auth', 0, 0, 0.0),
('payment', 0, 0, 0.0),
('database', 0, 0, 0.0),
('rate-limiter', 0, 0, 0.0)
ON DUPLICATE KEY UPDATE component=component;