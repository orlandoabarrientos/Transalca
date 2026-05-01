CREATE DATABASE IF NOT EXISTS db_transalca CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE db_transalca;


CREATE TABLE sucursales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    direccion VARCHAR(300),
    telefono VARCHAR(20),
    email VARCHAR(150),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categorias (
    nombre VARCHAR(150) PRIMARY KEY,
    descripcion VARCHAR(500),
    imagen VARCHAR(200) DEFAULT 'default_cat.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marcas (
    nombre VARCHAR(150) PRIMARY KEY,
    descripcion VARCHAR(500),
    logo VARCHAR(200) DEFAULT 'default_brand.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE proveedores (
    rif VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(150),
    direccion VARCHAR(300),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mecanicos (
    cedula VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    especialidad VARCHAR(200),
    foto_perfil VARCHAR(200) DEFAULT 'default.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clientes (
    cedula VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    email VARCHAR(150),
    direccion VARCHAR(300),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE configuracion (
    clave VARCHAR(100) PRIMARY KEY,
    valor VARCHAR(500)
);

CREATE TABLE productos (
    codigo VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    categoria VARCHAR(150),
    marca VARCHAR(150),
    sucursal_id INT,
    imagen VARCHAR(200) DEFAULT 'default_product.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria) REFERENCES categorias(nombre) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (marca) REFERENCES marcas(nombre) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL
);

CREATE TABLE servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    duracion_estimada VARCHAR(50),
    sucursal_id INT,
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL
);

CREATE TABLE inventario (
    producto_codigo VARCHAR(50) NOT NULL,
    sucursal_id INT NOT NULL,
    stock INT DEFAULT 0,
    stock_minimo INT DEFAULT 5,
    ubicacion VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (producto_codigo, sucursal_id),
    FOREIGN KEY (producto_codigo) REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE RESTRICT
);

CREATE TABLE promociones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(20) NOT NULL DEFAULT 'puntos',
    puntos_requeridos INT DEFAULT 3,
    recompensa VARCHAR(200),
    imagen_tarjeta VARCHAR(200) DEFAULT 'default_card.png',
    estado TINYINT(1) DEFAULT 1,
    fecha_inicio DATE,
    fecha_fin DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE ordenes_compra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proveedor_rif VARCHAR(20) NOT NULL,
    usuario_cedula VARCHAR(20) NOT NULL,
    sucursal_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0.00,
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
    observaciones VARCHAR(1000),
    FOREIGN KEY (proveedor_rif) REFERENCES proveedores(rif) ON UPDATE CASCADE,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL
);

CREATE TABLE ordenes_venta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_cedula VARCHAR(20) NOT NULL,
    sucursal_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0.00,
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
    metodo_pago VARCHAR(50),
    comprobante_url VARCHAR(255),
    observaciones VARCHAR(1000),
    FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL
);


CREATE TABLE detalle_orden_compra (
    orden_id INT NOT NULL,
    producto_codigo VARCHAR(50) NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (orden_id, producto_codigo),
    FOREIGN KEY (orden_id) REFERENCES ordenes_compra(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_codigo) REFERENCES productos(codigo) ON UPDATE CASCADE
);

CREATE TABLE detalle_orden_venta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_id INT NOT NULL,
    producto_codigo VARCHAR(50),
    servicio_id INT,
    tipo VARCHAR(20) NOT NULL DEFAULT 'producto',
    cantidad INT NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (orden_id) REFERENCES ordenes_venta(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_codigo) REFERENCES productos(codigo) ON UPDATE CASCADE,
    FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE SET NULL
);

CREATE TABLE servicio_mecanico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    servicio_id INT NOT NULL,
    mecanico_cedula VARCHAR(20),
    orden_venta_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(30) NOT NULL DEFAULT 'asignado',
    observaciones VARCHAR(1000),
    FOREIGN KEY (servicio_id) REFERENCES servicios(id),
    FOREIGN KEY (mecanico_cedula) REFERENCES mecanicos(cedula) ON UPDATE CASCADE,
    FOREIGN KEY (orden_venta_id) REFERENCES ordenes_venta(id)
);

CREATE TABLE comprobantes_pago (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_venta_id INT NOT NULL,
    imagen_url VARCHAR(255) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
    revisado_por VARCHAR(20),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observaciones VARCHAR(1000),
    FOREIGN KEY (orden_venta_id) REFERENCES ordenes_venta(id) ON DELETE CASCADE,
    INDEX idx_comprobantes_revisado_por (revisado_por)
);


CREATE TABLE tarjeta_fidelidad (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_cedula VARCHAR(20) NOT NULL,
    promocion_id INT NOT NULL,
    puntos_acumulados INT DEFAULT 0,
    canjeada TINYINT(1) DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE,
    FOREIGN KEY (promocion_id) REFERENCES promociones(id)
);

CREATE TABLE historial_puntos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tarjeta_id INT NOT NULL,
    puntos INT NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'suma',
    descripcion VARCHAR(150),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tarjeta_id) REFERENCES tarjeta_fidelidad(id) ON DELETE CASCADE
);


CREATE TABLE qr_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_cedula VARCHAR(20) NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'info',
    contenido VARCHAR(4300),
    utilidad VARCHAR(150),
    referencia_id INT DEFAULT NULL,
    promocion_id INT DEFAULT NULL,
    servicio_id INT DEFAULT NULL,
    orden_venta_id INT DEFAULT NULL,
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (promocion_id) REFERENCES promociones(id) ON DELETE SET NULL,
    FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE SET NULL,
    FOREIGN KEY (orden_venta_id) REFERENCES ordenes_venta(id) ON DELETE SET NULL,
    INDEX idx_qr_usuario_cedula (usuario_cedula),
    INDEX idx_qr_referencia (tipo, referencia_id),
    INDEX idx_qr_promocion (promocion_id),
    INDEX idx_qr_servicio (servicio_id),
    INDEX idx_qr_orden (orden_venta_id)
);

CREATE TABLE carrito (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_cedula VARCHAR(20) NOT NULL,
    producto_codigo VARCHAR(50),
    servicio_id INT,
    tipo VARCHAR(20) NOT NULL DEFAULT 'producto',
    cantidad INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE,
    FOREIGN KEY (producto_codigo) REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE CASCADE
);

CREATE TABLE exchange_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'bcv',
    monto DECIMAL(12,4) NOT NULL,
    fuente VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_exchange_fecha_tipo (fecha, tipo)
);


CREATE INDEX idx_ordenes_venta_cliente ON ordenes_venta (cliente_cedula);


DELIMITER //
CREATE TRIGGER trg_stock_compra_recibida
AFTER INSERT ON detalle_orden_compra
FOR EACH ROW
BEGIN
    DECLARE v_suc INT;
    SELECT sucursal_id INTO v_suc FROM ordenes_compra WHERE id = NEW.orden_id LIMIT 1;
    IF EXISTS (SELECT 1 FROM inventario WHERE producto_codigo = NEW.producto_codigo AND sucursal_id = v_suc) THEN
        UPDATE inventario SET stock = stock + NEW.cantidad
        WHERE producto_codigo = NEW.producto_codigo AND sucursal_id = v_suc;
    ELSE
        INSERT INTO inventario (producto_codigo, sucursal_id, stock)
        VALUES (NEW.producto_codigo, v_suc, NEW.cantidad);
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_stock_venta_aprobada
AFTER INSERT ON detalle_orden_venta
FOR EACH ROW
BEGIN
    DECLARE v_suc INT;
    IF NEW.tipo = 'producto' AND NEW.producto_codigo IS NOT NULL THEN
        SELECT sucursal_id INTO v_suc FROM ordenes_venta WHERE id = NEW.orden_id LIMIT 1;
        UPDATE inventario SET stock = stock - NEW.cantidad
        WHERE producto_codigo = NEW.producto_codigo AND sucursal_id = v_suc;
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION fn_stock_disponible(p_producto_codigo VARCHAR(50), p_sucursal_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE v_stock INT DEFAULT 0;
    IF p_sucursal_id IS NULL THEN
        SELECT COALESCE(SUM(stock), 0) INTO v_stock FROM inventario WHERE producto_codigo = p_producto_codigo;
    ELSE
        SELECT COALESCE(stock, 0) INTO v_stock FROM inventario WHERE producto_codigo = p_producto_codigo AND sucursal_id = p_sucursal_id;
    END IF;
    RETURN v_stock;
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION fn_calcular_total_orden(p_orden_id INT, p_tipo VARCHAR(10))
RETURNS DECIMAL(12,2)
DETERMINISTIC
BEGIN
    DECLARE v_total DECIMAL(12,2) DEFAULT 0.00;
    IF p_tipo = 'compra' THEN
        SELECT COALESCE(SUM(subtotal), 0) INTO v_total FROM detalle_orden_compra WHERE orden_id = p_orden_id;
    ELSE
        SELECT COALESCE(SUM(subtotal), 0) INTO v_total FROM detalle_orden_venta WHERE orden_id = p_orden_id;
    END IF;
    RETURN v_total;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_auto_canje_tarjeta
BEFORE UPDATE ON tarjeta_fidelidad
FOR EACH ROW
BEGIN
    DECLARE v_puntos_req INT DEFAULT 0;
    IF NEW.canjeada = 0 THEN
        SELECT puntos_requeridos INTO v_puntos_req FROM promociones WHERE id = NEW.promocion_id LIMIT 1;
        IF NEW.puntos_acumulados >= v_puntos_req THEN
            SET NEW.canjeada = 1;
        END IF;
    END IF;
END //
DELIMITER ;


INSERT INTO sucursales (nombre, direccion, telefono, email) VALUES
('Sede Principal', 'Av. Principal, Local 1', '0424-0000000', 'principal@transalca.com'),
('Sucursal Norte', 'Calle Norte, Centro Comercial X', '0424-1111111', 'norte@transalca.com');

INSERT INTO categorias (nombre, descripcion) VALUES
('Cauchos', 'Neumaticos para todo tipo de vehiculos'),
('Lubricantes', 'Aceites y lubricantes para motor y transmision'),
('Repuestos', 'Repuestos y autopartes en general'),
('Filtros', 'Filtros de aire, aceite y combustible'),
('Frenos', 'Pastillas, discos y sistemas de frenos'),
('Baterias', 'Baterias para vehiculos');

INSERT INTO marcas (nombre, descripcion) VALUES
('Pirelli', 'Neumaticos premium italianos'),
('Michelin', 'Neumaticos franceses de alta calidad'),
('Firestone', 'Neumaticos americanos'),
('Mobil', 'Lubricantes de alta gama'),
('Castrol', 'Lubricantes y aceites'),
('Shell', 'Lubricantes Shell Helix');

INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, sucursal_id) VALUES
('Alineacion', 'Alineacion computarizada de ruedas', 15.00, '30 min', 1),
('Balanceo', 'Balanceo dinamico de ruedas', 10.00, '20 min', 1),
('Rotacion de cauchos', 'Rotacion de 4 cauchos', 8.00, '25 min', 1),
('Cambio de aceite', 'Cambio de aceite de motor', 12.00, '30 min', 1),
('Cambio de frenos', 'Cambio de pastillas de freno', 25.00, '45 min', 2),
('Revision general', 'Revision completa del vehiculo', 20.00, '60 min', 2);

INSERT INTO configuracion (clave, valor) VALUES
('nombre_empresa', 'Transalca C.A.'),
('rif_empresa', 'J-00000000-0'),
('telefono_empresa', '0424-0000000'),
('direccion_empresa', 'Direccion Principal'),
('email_empresa', 'info@transalca.com'),
('moneda', 'USD');

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS origen_registro VARCHAR(20) DEFAULT 'cliente' AFTER estado,
    ADD COLUMN IF NOT EXISTS usuario_id INT DEFAULT NULL AFTER origen_registro;

ALTER TABLE mecanicos
    ADD COLUMN IF NOT EXISTS usuario_id INT DEFAULT NULL AFTER foto_perfil;

ALTER TABLE servicios
    ADD COLUMN IF NOT EXISTS permite_filtros TINYINT(1) DEFAULT 1 AFTER estado;

ALTER TABLE promociones
    ADD COLUMN IF NOT EXISTS compras_minimas INT DEFAULT 0 AFTER imagen_tarjeta,
    ADD COLUMN IF NOT EXISTS ticket_minimo_usd DECIMAL(10,2) DEFAULT 0.00 AFTER compras_minimas,
    ADD COLUMN IF NOT EXISTS monto_total_minimo DECIMAL(10,2) DEFAULT 0.00 AFTER ticket_minimo_usd,
    ADD COLUMN IF NOT EXISTS producto_requerido VARCHAR(50) DEFAULT NULL AFTER monto_total_minimo,
    ADD COLUMN IF NOT EXISTS servicio_requerido INT DEFAULT NULL AFTER producto_requerido,
    ADD COLUMN IF NOT EXISTS beneficio_tipo VARCHAR(30) DEFAULT 'descuento_pct' AFTER servicio_requerido,
    ADD COLUMN IF NOT EXISTS beneficio_valor DECIMAL(10,2) DEFAULT 0.00 AFTER beneficio_tipo,
    ADD COLUMN IF NOT EXISTS uso_maximo_cliente INT DEFAULT 0 AFTER beneficio_valor,
    ADD COLUMN IF NOT EXISTS uso_maximo_total INT DEFAULT 0 AFTER uso_maximo_cliente,
    ADD COLUMN IF NOT EXISTS usos_actuales INT DEFAULT 0 AFTER uso_maximo_total;

CREATE TABLE IF NOT EXISTS vehiculos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_cedula VARCHAR(20) NOT NULL,
    marca VARCHAR(100) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    anio SMALLINT,
    placa VARCHAR(20),
    color VARCHAR(50),
    tipo_vehiculo VARCHAR(50),
    tipo_combustible VARCHAR(20) DEFAULT 'gasolina',
    kilometraje_actual INT DEFAULT 0,
    km_ultimo_servicio INT DEFAULT 0,
    fecha_ultimo_servicio DATE,
    aceite_usado VARCHAR(200),
    filtros_info TEXT,
    refrigerante_info VARCHAR(200),
    observaciones TEXT,
    cauchos_json JSON,
    imagen_carnet VARCHAR(255),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_vehiculos_cliente FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE,
    UNIQUE KEY uq_vehiculos_placa (placa),
    INDEX idx_vehiculos_cliente (cliente_cedula),
    INDEX idx_vehiculos_estado (estado)
);

CREATE TABLE IF NOT EXISTS reglas_mantenimiento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    tipo_servicio VARCHAR(100) NOT NULL,
    intervalo_km INT,
    intervalo_dias INT,
    intervalo_servicios INT,
    tipo_combustible VARCHAR(20) DEFAULT 'todos',
    tipo_vehiculo VARCHAR(50),
    descripcion TEXT,
    activo TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mantenimientos_programados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehiculo_id INT NOT NULL,
    regla_id INT DEFAULT NULL,
    tipo_mantenimiento VARCHAR(100) NOT NULL,
    modo VARCHAR(20) DEFAULT 'manual',
    km_proximo INT,
    fecha_proxima DATE,
    km_realizado INT,
    fecha_realizado DATE,
    estado VARCHAR(20) DEFAULT 'pendiente',
    registrado_por VARCHAR(20),
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_mantenimientos_vehiculo FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE,
    CONSTRAINT fk_mantenimientos_regla FOREIGN KEY (regla_id) REFERENCES reglas_mantenimiento(id) ON DELETE SET NULL,
    INDEX idx_mant_vehiculo_estado (vehiculo_id, estado)
);

CREATE TABLE IF NOT EXISTS bitacora_vehiculo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehiculo_id INT NOT NULL,
    cliente_cedula VARCHAR(20) NOT NULL,
    orden_venta_id INT DEFAULT NULL,
    servicio_id INT DEFAULT NULL,
    mecanico_cedula VARCHAR(20) DEFAULT NULL,
    tipo_registro VARCHAR(30) DEFAULT 'servicio',
    descripcion TEXT,
    kilometraje INT,
    aceite_usado VARCHAR(200),
    filtros_usados TEXT,
    refrigerante_usado VARCHAR(200),
    cauchos_info TEXT,
    precio_servicio DECIMAL(10,2) DEFAULT 0.00,
    precio_productos DECIMAL(10,2) DEFAULT 0.00,
    proximo_mantenimiento TEXT,
    modo_registro VARCHAR(20) DEFAULT 'manual',
    observaciones TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bitacora_vehiculo FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE,
    CONSTRAINT fk_bitacora_cliente FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE,
    CONSTRAINT fk_bitacora_mecanico FOREIGN KEY (mecanico_cedula) REFERENCES mecanicos(cedula) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_bitacora_orden FOREIGN KEY (orden_venta_id) REFERENCES ordenes_venta(id) ON DELETE SET NULL,
    CONSTRAINT fk_bitacora_servicio FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE SET NULL,
    INDEX idx_bitacora_vehiculo_fecha (vehiculo_id, fecha),
    INDEX idx_bitacora_cliente_fecha (cliente_cedula, fecha)
);

CREATE TABLE IF NOT EXISTS consumo_combustible (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehiculo_id INT NOT NULL,
    modo VARCHAR(20) DEFAULT 'manual',
    consumo_estimado_lkm DECIMAL(6,2),
    fuente_dato VARCHAR(500),
    km_recorridos INT,
    litros_consumidos DECIMAL(8,2),
    precio_litro DECIMAL(10,2),
    fecha DATE,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_consumo_vehiculo FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE,
    INDEX idx_consumo_vehiculo_fecha (vehiculo_id, fecha)
);

CREATE TABLE IF NOT EXISTS tickets_soporte (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_cedula VARCHAR(20) NOT NULL,
    vehiculo_id INT DEFAULT NULL,
    asunto VARCHAR(300) NOT NULL,
    descripcion TEXT,
    estado VARCHAR(30) NOT NULL DEFAULT 'abierto',
    prioridad VARCHAR(20) DEFAULT 'media',
    asignado_a VARCHAR(20) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_ticket_cliente FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE,
    CONSTRAINT fk_ticket_vehiculo FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id) ON DELETE SET NULL,
    CONSTRAINT fk_ticket_asignado FOREIGN KEY (asignado_a) REFERENCES mecanicos(cedula) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_ticket_cliente (cliente_cedula),
    INDEX idx_ticket_estado (estado),
    INDEX idx_ticket_prioridad (prioridad)
);

CREATE TABLE IF NOT EXISTS ticket_respuestas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    autor_id INT NOT NULL,
    autor_tipo VARCHAR(20) NOT NULL,
    mensaje TEXT NOT NULL,
    adjunto_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ticket_respuesta_ticket FOREIGN KEY (ticket_id) REFERENCES tickets_soporte(id) ON DELETE CASCADE,
    INDEX idx_ticket_respuesta_ticket_fecha (ticket_id, created_at)
);

CREATE TABLE IF NOT EXISTS comisiones_mecanico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mecanico_cedula VARCHAR(20) NOT NULL,
    servicio_mecanico_id INT NOT NULL,
    orden_venta_id INT NOT NULL,
    precio_servicio DECIMAL(10,2) NOT NULL,
    porcentaje_comision DECIMAL(5,2) DEFAULT 30.00,
    monto_comision DECIMAL(10,2) NOT NULL,
    estado_pago VARCHAR(20) DEFAULT 'pendiente',
    fecha_pago DATE,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comision_mecanico FOREIGN KEY (mecanico_cedula) REFERENCES mecanicos(cedula) ON UPDATE CASCADE,
    CONSTRAINT fk_comision_servicio_mecanico FOREIGN KEY (servicio_mecanico_id) REFERENCES servicio_mecanico(id),
    CONSTRAINT fk_comision_orden FOREIGN KEY (orden_venta_id) REFERENCES ordenes_venta(id),
    UNIQUE KEY uq_comision_servicio_mecanico (servicio_mecanico_id),
    INDEX idx_comision_mecanico_estado (mecanico_cedula, estado_pago)
);

CREATE TABLE IF NOT EXISTS cotizaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_cedula VARCHAR(20) NOT NULL,
    exchange_rate_id INT DEFAULT NULL,
    tasa_usada DECIMAL(12,4) NOT NULL,
    tipo_tasa VARCHAR(20) NOT NULL,
    total_usd DECIMAL(12,2) NOT NULL,
    total_bs DECIMAL(14,2) NOT NULL,
    vigente_hasta DATETIME NOT NULL,
    estado VARCHAR(20) DEFAULT 'vigente',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cotizacion_cliente FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE,
    CONSTRAINT fk_cotizacion_tasa FOREIGN KEY (exchange_rate_id) REFERENCES exchange_rates(id) ON DELETE SET NULL,
    INDEX idx_cotizacion_cliente_estado (cliente_cedula, estado)
);

CREATE TABLE IF NOT EXISTS cotizacion_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cotizacion_id INT NOT NULL,
    producto_codigo VARCHAR(50),
    servicio_id INT,
    tipo VARCHAR(20) NOT NULL DEFAULT 'producto',
    cantidad INT DEFAULT 1,
    precio_usd DECIMAL(10,2) NOT NULL,
    precio_bs DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_cotizacion_item_cotizacion FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id) ON DELETE CASCADE,
    CONSTRAINT fk_cotizacion_item_producto FOREIGN KEY (producto_codigo) REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_cotizacion_item_servicio FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS notificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT DEFAULT NULL,
    cliente_cedula VARCHAR(20) DEFAULT NULL,
    tipo VARCHAR(30) NOT NULL DEFAULT 'sistema',
    titulo VARCHAR(200),
    mensaje TEXT,
    prioridad VARCHAR(20) DEFAULT 'media',
    leida TINYINT(1) DEFAULT 0,
    enlace VARCHAR(500),
    referencia_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notif_cliente FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE ON DELETE CASCADE,
    INDEX idx_notif_usuario (usuario_id),
    INDEX idx_notif_cliente (cliente_cedula),
    INDEX idx_notif_leida (leida),
    INDEX idx_notif_fecha (created_at)
);

INSERT INTO reglas_mantenimiento (nombre, tipo_servicio, intervalo_km, intervalo_dias, descripcion)
SELECT 'Cambio de aceite', 'cambio_aceite', 5000, 180, 'Cambio de aceite cada 5000 km o 6 meses'
WHERE NOT EXISTS (SELECT 1 FROM reglas_mantenimiento WHERE nombre = 'Cambio de aceite');

INSERT INTO reglas_mantenimiento (nombre, tipo_servicio, intervalo_km, intervalo_dias, descripcion)
SELECT 'Filtro de aceite', 'filtro_aceite', 5000, 180, 'Cambiar junto con aceite'
WHERE NOT EXISTS (SELECT 1 FROM reglas_mantenimiento WHERE nombre = 'Filtro de aceite');

INSERT INTO reglas_mantenimiento (nombre, tipo_servicio, intervalo_km, intervalo_dias, descripcion)
SELECT 'Filtro de aire', 'filtro_aire', 15000, 365, 'Cambio cada 15000 km o 1 ano'
WHERE NOT EXISTS (SELECT 1 FROM reglas_mantenimiento WHERE nombre = 'Filtro de aire');

INSERT INTO reglas_mantenimiento (nombre, tipo_servicio, intervalo_km, intervalo_dias, descripcion)
SELECT 'Filtro de gasolina', 'filtro_gasolina', 20000, 365, 'Cambio cada 20000 km o 1 ano'
WHERE NOT EXISTS (SELECT 1 FROM reglas_mantenimiento WHERE nombre = 'Filtro de gasolina');

INSERT INTO reglas_mantenimiento (nombre, tipo_servicio, intervalo_km, intervalo_dias, descripcion)
SELECT 'Filtro de gasoil', 'filtro_gasoil', 15000, 365, 'Solo vehiculos diesel'
WHERE NOT EXISTS (SELECT 1 FROM reglas_mantenimiento WHERE nombre = 'Filtro de gasoil');

INSERT INTO reglas_mantenimiento (nombre, tipo_servicio, intervalo_km, intervalo_dias, descripcion)
SELECT 'Refrigerante', 'refrigerante', 40000, 730, 'Cambio cada 40000 km o 2 anos'
WHERE NOT EXISTS (SELECT 1 FROM reglas_mantenimiento WHERE nombre = 'Refrigerante');

INSERT INTO reglas_mantenimiento (nombre, tipo_servicio, intervalo_km, intervalo_dias, descripcion)
SELECT 'Revision de cauchos', 'cauchos', 10000, 180, 'Revision cada 10000 km o 6 meses'
WHERE NOT EXISTS (SELECT 1 FROM reglas_mantenimiento WHERE nombre = 'Revision de cauchos');

INSERT INTO reglas_mantenimiento (nombre, tipo_servicio, intervalo_km, intervalo_dias, descripcion)
SELECT 'Rotacion de cauchos', 'rotacion_cauchos', 10000, 365, 'Rotar cada 10000 km'
WHERE NOT EXISTS (SELECT 1 FROM reglas_mantenimiento WHERE nombre = 'Rotacion de cauchos');

INSERT IGNORE INTO configuracion (clave, valor) VALUES
('margen_seguridad_pct', '3.0'),
('hora_congelamiento', '16:00'),
('banda_variacion_pct', '2.0'),
('tasa_referencia_activa', 'bcv'),
('redondeo_bs', '0.50'),
('vencimiento_cotizacion_hrs', '24'),
('auto_update_enabled', '1'),
('update_schedule', '09:00,13:00,16:00');
