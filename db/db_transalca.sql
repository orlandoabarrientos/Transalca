CREATE DATABASE IF NOT EXISTS db_transalca CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE db_transalca;

-- ============================================================
-- TABLAS CATÁLOGO — PK: nombre (clave natural)
-- Eliminan id surrogate. Queries directas: WHERE estado = 'pendiente'
-- ============================================================

CREATE TABLE cat_estados_orden_compra (
    nombre VARCHAR(30) PRIMARY KEY,
    descripcion VARCHAR(100)
);

CREATE TABLE cat_estados_orden_venta (
    nombre VARCHAR(30) PRIMARY KEY,
    descripcion VARCHAR(100)
);

CREATE TABLE cat_estados_servicio_mecanico (
    nombre VARCHAR(30) PRIMARY KEY,
    descripcion VARCHAR(100)
);

CREATE TABLE cat_estados_comprobante (
    nombre VARCHAR(30) PRIMARY KEY,
    descripcion VARCHAR(100)
);

CREATE TABLE cat_tipos_item (
    nombre VARCHAR(20) PRIMARY KEY
);

CREATE TABLE cat_tipos_promocion (
    nombre VARCHAR(20) PRIMARY KEY
);

CREATE TABLE cat_tipos_movimiento_puntos (
    nombre VARCHAR(20) PRIMARY KEY
);

CREATE TABLE cat_tipos_qr (
    nombre VARCHAR(20) PRIMARY KEY
);

-- ============================================================
-- DATOS SEMILLA — TABLAS CATÁLOGO
-- ============================================================

INSERT INTO cat_estados_orden_compra (nombre) VALUES
('pendiente'), ('recibida'), ('cancelada');

INSERT INTO cat_estados_orden_venta (nombre) VALUES
('pendiente'), ('aprobada'), ('rechazada'), ('entregada'), ('cancelada');

INSERT INTO cat_estados_servicio_mecanico (nombre) VALUES
('asignado'), ('en_proceso'), ('completado'), ('cancelado');

INSERT INTO cat_estados_comprobante (nombre) VALUES
('pendiente'), ('aprobado'), ('rechazado');

INSERT INTO cat_tipos_item (nombre) VALUES
('producto'), ('servicio');

INSERT INTO cat_tipos_promocion (nombre) VALUES
('puntos'), ('descuento'), ('gratis');

INSERT INTO cat_tipos_movimiento_puntos (nombre) VALUES
('suma'), ('resta'), ('canje');

INSERT INTO cat_tipos_qr (nombre) VALUES
('promocion'), ('servicio'), ('info'), ('pago');

-- ============================================================
-- TABLAS BASE — NIVEL 0 (sin dependencias FK)
-- ============================================================

-- sucursales: MANTIENE id — no tiene identificador natural único
CREATE TABLE sucursales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    direccion VARCHAR(300),
    telefono VARCHAR(20),
    email VARCHAR(150),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- categorias: PK = nombre (clave natural)
CREATE TABLE categorias (
    nombre VARCHAR(150) PRIMARY KEY,
    descripcion VARCHAR(500),
    imagen VARCHAR(200) DEFAULT 'default_cat.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- marcas: PK = nombre (clave natural)
CREATE TABLE marcas (
    nombre VARCHAR(150) PRIMARY KEY,
    descripcion VARCHAR(500),
    logo VARCHAR(200) DEFAULT 'default_brand.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- proveedores: PK = rif (clave natural — identificador fiscal único)
CREATE TABLE proveedores (
    rif VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(150),
    direccion VARCHAR(300),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- mecanicos: PK = cedula (clave natural — documento de identidad)
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

-- clientes: PK = cedula (clave natural — documento de identidad)
CREATE TABLE clientes (
    cedula VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(150),
    direccion VARCHAR(300),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- configuracion: PK = clave (clave natural — pares clave-valor únicos)
CREATE TABLE configuracion (
    clave VARCHAR(100) PRIMARY KEY,
    valor VARCHAR(500)
);

-- ============================================================
-- TABLAS NIVEL 1 — dependen de Nivel 0
-- ============================================================

-- usuarios: PK = cedula (clave natural — documento de identidad)
CREATE TABLE usuarios (
    cedula VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(30) DEFAULT 'vendedor',
    sucursal_id INT,
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL
);

-- productos: PK = codigo (clave natural — código de producto único)
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

-- servicios: MANTIENE id — nombre no es único entre sucursales
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

-- inventario: PK compuesta (producto_codigo, sucursal_id) — elimina id
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

-- promociones: MANTIENE id — sin clave natural estable
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tipo) REFERENCES cat_tipos_promocion(nombre) ON UPDATE CASCADE
);

-- ============================================================
-- TABLAS NIVEL 2 — Órdenes (transaccionales)
-- MANTIENEN id — número secuencial de orden obligatorio
-- ============================================================

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
    FOREIGN KEY (usuario_cedula) REFERENCES usuarios(cedula) ON UPDATE CASCADE,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL,
    FOREIGN KEY (estado) REFERENCES cat_estados_orden_compra(nombre) ON UPDATE CASCADE
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
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL,
    FOREIGN KEY (estado) REFERENCES cat_estados_orden_venta(nombre) ON UPDATE CASCADE
);

-- ============================================================
-- TABLAS NIVEL 3 — Detalles de órdenes
-- ============================================================

-- detalle_orden_compra: PK compuesta (orden_id, producto_codigo)
-- Un producto por línea de orden. Cantidades se acumulan.
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

-- detalle_orden_venta: MANTIENE id — unión discriminada producto/servicio
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
    FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE SET NULL,
    FOREIGN KEY (tipo) REFERENCES cat_tipos_item(nombre) ON UPDATE CASCADE
);

-- servicio_mecanico: MANTIENE id — sin clave natural
CREATE TABLE servicio_mecanico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    servicio_id INT NOT NULL,
    mecanico_cedula VARCHAR(20) NOT NULL,
    orden_venta_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(30) NOT NULL DEFAULT 'asignado',
    observaciones VARCHAR(1000),
    FOREIGN KEY (servicio_id) REFERENCES servicios(id),
    FOREIGN KEY (mecanico_cedula) REFERENCES mecanicos(cedula) ON UPDATE CASCADE,
    FOREIGN KEY (orden_venta_id) REFERENCES ordenes_venta(id),
    FOREIGN KEY (estado) REFERENCES cat_estados_servicio_mecanico(nombre) ON UPDATE CASCADE
);

-- comprobantes_pago: MANTIENE id — sin clave natural
CREATE TABLE comprobantes_pago (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_venta_id INT NOT NULL,
    imagen_url VARCHAR(255) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
    revisado_por VARCHAR(20),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observaciones VARCHAR(1000),
    FOREIGN KEY (orden_venta_id) REFERENCES ordenes_venta(id) ON DELETE CASCADE,
    FOREIGN KEY (revisado_por) REFERENCES usuarios(cedula) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (estado) REFERENCES cat_estados_comprobante(nombre) ON UPDATE CASCADE
);

-- ============================================================
-- TABLAS FIDELIZACIÓN
-- ============================================================

-- tarjeta_fidelidad: MANTIENE id — un cliente puede tener múltiples
-- tarjetas para la misma promoción (una canjeada, otra nueva)
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

-- historial_puntos: MANTIENE id — tabla de log/auditoría
CREATE TABLE historial_puntos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tarjeta_id INT NOT NULL,
    puntos INT NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'suma',
    descripcion VARCHAR(150),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tarjeta_id) REFERENCES tarjeta_fidelidad(id) ON DELETE CASCADE,
    FOREIGN KEY (tipo) REFERENCES cat_tipos_movimiento_puntos(nombre) ON UPDATE CASCADE
);

-- ============================================================
-- TABLAS AUXILIARES
-- ============================================================

-- qr_codes: MANTIENE id — sin clave natural
CREATE TABLE qr_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_cedula VARCHAR(20) NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'info',
    contenido VARCHAR(4300),
    utilidad VARCHAR(150),
    referencia_id INT DEFAULT NULL COMMENT 'ID contextual según tipo (promocion_id, servicio_id, orden_venta_id)',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_cedula) REFERENCES usuarios(cedula) ON UPDATE CASCADE,
    FOREIGN KEY (tipo) REFERENCES cat_tipos_qr(nombre) ON UPDATE CASCADE,
    INDEX idx_qr_referencia (tipo, referencia_id)
);

-- carrito: MANTIENE id — tipo discriminado producto/servicio
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
    FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE CASCADE,
    FOREIGN KEY (tipo) REFERENCES cat_tipos_item(nombre) ON UPDATE CASCADE
);

-- ============================================================
-- TRIGGERS Y FUNCIONES
-- Actualizados para usar claves naturales
-- ============================================================

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

-- tipo = 'producto' directamente legible (FK a cat_tipos_item)
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

-- ============================================================
-- DATOS SEMILLA
-- ============================================================

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
