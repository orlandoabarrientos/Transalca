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
    rif_prefijo VARCHAR(2),
    nombre VARCHAR(200) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(150),
    direccion VARCHAR(300),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mecanicos (
    cedula VARCHAR(20) PRIMARY KEY,
    cedula_prefijo VARCHAR(2),
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
    cedula_prefijo VARCHAR(2),
    tipo_cliente VARCHAR(20) NOT NULL DEFAULT 'persona',
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    email VARCHAR(150),
    direccion VARCHAR(300),
    estado TINYINT(1) DEFAULT 1,
    origen_registro VARCHAR(20) DEFAULT 'admin',
    usuario_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE empresas (
    cliente_cedula VARCHAR(20) PRIMARY KEY,
    rif VARCHAR(20) NOT NULL UNIQUE,
    rif_prefijo VARCHAR(2),
    razon_social VARCHAR(200) NOT NULL,
    nombre_comercial VARCHAR(200),
    representante_nombre VARCHAR(150),
    representante_cedula VARCHAR(20),
    representante_telefono VARCHAR(20),
    representante_email VARCHAR(150),
    sector VARCHAR(150),
    limite_credito DECIMAL(10,2) DEFAULT 0.00,
    dias_credito INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE ON DELETE CASCADE
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
    proveedor_rif VARCHAR(20),
    imagen VARCHAR(200) DEFAULT 'default_product.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria) REFERENCES categorias(nombre) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (marca) REFERENCES marcas(nombre) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (proveedor_rif) REFERENCES proveedores(rif) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    duracion_estimada VARCHAR(50),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE servicio_sucursal (
    servicio_id INT NOT NULL,
    sucursal_id INT NOT NULL,
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (servicio_id, sucursal_id),
    FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE CASCADE,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE CASCADE
);

CREATE TABLE stock (
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

CREATE TABLE metodos_pago (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    nombre VARCHAR(100) NOT NULL,
    datos TEXT NOT NULL,
    permite_credito TINYINT(1) DEFAULT 0,
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE ordenes_venta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_cedula VARCHAR(20) NOT NULL,
    sucursal_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0.00,
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
    metodo_pago_id INT,
    tipo_pago VARCHAR(20) NOT NULL DEFAULT 'contado',
    credito_estado VARCHAR(30) DEFAULT 'sin_credito',
    fecha_inicio_credito DATE,
    fecha_vencimiento_credito DATE,
    credito_notificacion_7d TINYINT(1) DEFAULT 0,
    credito_notificacion_2d TINYINT(1) DEFAULT 0,
    credito_notificacion_vencido TINYINT(1) DEFAULT 0,
    fecha_pago_credito DATETIME,
    comprobante_url VARCHAR(255),
    observaciones VARCHAR(1000),
    FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL,
    FOREIGN KEY (metodo_pago_id) REFERENCES metodos_pago(id) ON DELETE SET NULL
);


CREATE TABLE detalle_orden_venta_productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_id INT NOT NULL,
    producto_codigo VARCHAR(50) NOT NULL,
    cantidad INT NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (orden_id) REFERENCES ordenes_venta(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_codigo) REFERENCES productos(codigo) ON UPDATE CASCADE
);

CREATE TABLE detalle_orden_venta_servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_id INT NOT NULL,
    servicio_id INT NOT NULL,
    cantidad INT NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (orden_id) REFERENCES ordenes_venta(id) ON DELETE CASCADE,
    FOREIGN KEY (servicio_id) REFERENCES servicios(id)
);

CREATE OR REPLACE VIEW detalle_orden_venta AS
SELECT id, orden_id, producto_codigo, NULL AS servicio_id, 'producto' AS tipo, cantidad, precio_unitario, subtotal
FROM detalle_orden_venta_productos
UNION ALL
SELECT id, orden_id, NULL AS producto_codigo, servicio_id, 'servicio' AS tipo, cantidad, precio_unitario, subtotal
FROM detalle_orden_venta_servicios;

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
    FOREIGN KEY (orden_venta_id) REFERENCES ordenes_venta(id) ON DELETE CASCADE
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
    INDEX idx_qr_referencia (tipo, referencia_id)
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
    FOREIGN KEY (producto_codigo) REFERENCES productos(codigo) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE SET NULL
);

CREATE TABLE tasas_cambio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'bcv',
    monto DECIMAL(12,4) NOT NULL,
    fuente VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tasas_cambio_fecha_tipo (fecha, tipo)
);


CREATE INDEX idx_ordenes_venta_cliente ON ordenes_venta (cliente_cedula);


DELIMITER //
CREATE TRIGGER trg_stock_venta_aprobada
AFTER INSERT ON detalle_orden_venta_productos
FOR EACH ROW
BEGIN
    DECLARE v_suc INT;
    SELECT sucursal_id INTO v_suc FROM ordenes_venta WHERE id = NEW.orden_id LIMIT 1;
    UPDATE stock SET stock = stock - NEW.cantidad
    WHERE producto_codigo = NEW.producto_codigo AND sucursal_id = v_suc;
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION fn_stock_disponible(p_producto_codigo VARCHAR(50), p_sucursal_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE v_stock INT DEFAULT 0;
    IF p_sucursal_id IS NULL THEN
        SELECT COALESCE(SUM(stock), 0) INTO v_stock FROM stock WHERE producto_codigo = p_producto_codigo;
    ELSE
        SELECT COALESCE(stock, 0) INTO v_stock FROM stock WHERE producto_codigo = p_producto_codigo AND sucursal_id = p_sucursal_id;
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
    SELECT COALESCE(SUM(subtotal), 0) INTO v_total FROM detalle_orden_venta WHERE orden_id = p_orden_id;
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


INSERT INTO sucursales (id, nombre, direccion, telefono, email, estado) VALUES
(1, 'Sede Principal', 'Av. Principal, Local 1', '04240000000', 'principal@transalca.com', 1),
(2, 'Sucursal Norte', 'Calle Norte, Centro Comercial X', '04241111111', 'norte@transalca.com', 1)
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre), direccion = VALUES(direccion), telefono = VALUES(telefono), email = VALUES(email), estado = VALUES(estado);

INSERT INTO categorias (nombre, descripcion, estado) VALUES
('Cauchos', 'Neumaticos para todo tipo de vehiculos', 1),
('Lubricantes', 'Aceites y lubricantes para motor y transmision', 1),
('Baterias', 'Baterias para vehiculos', 1),
('Combos', 'Combos de aceite, filtro y servicio', 1),
('Repuestos', 'Repuestos y autopartes en general', 1),
('Filtros', 'Filtros de aire, aceite y combustible', 1),
('Frenos', 'Pastillas, discos y sistemas de frenos', 1)
ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion), estado = VALUES(estado);

INSERT INTO marcas (nombre, descripcion, estado) VALUES
('15W40 / 20W50 SEMI SINTETICO FC GARRAFA', 'Marca importada del catalogo real: 15W40 / 20W50 SEMI SINTETICO FC GARRAFA', 1),
('15W40 SEMI SINTETICO VALVOLINE GARRAFA', 'Marca importada del catalogo real: 15W40 SEMI SINTETICO VALVOLINE GARRAFA', 1),
('7.00R15 KOBATA', 'Marca importada del catalogo real: 7.00R15 KOBATA', 1),
('ACEITE 10W30 SEMI SINTETICO GULF', 'Marca importada del catalogo real: ACEITE 10W30 SEMI SINTETICO GULF', 1),
('ACEITE 10W40 SEMI SINTETICO MOBIL', 'Marca importada del catalogo real: ACEITE 10W40 SEMI SINTETICO MOBIL', 1),
('ACEITE 15W40 MINERAL FC', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL FC', 1),
('ACEITE 15W40 MINERAL GULF', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL GULF', 1),
('ACEITE 15W40 MINERAL INCA', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL INCA', 1),
('ACEITE 15W40 MINERAL MEXLUB', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL MEXLUB', 1),
('ACEITE 15W40 MINERAL RALOY', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL RALOY', 1),
('ACEITE 15W40 MINERAL ROSHFRANS', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL ROSHFRANS', 1),
('ACEITE 15W40 MINERAL VALVOLINE', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL VALVOLINE', 1),
('ACEITE 15W40 SEMI SINTETICO BOSS', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO BOSS', 1),
('ACEITE 15W40 SEMI SINTETICO FC', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO FC', 1),
('ACEITE 15W40 SEMI SINTETICO GULF', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO GULF', 1),
('ACEITE 15W40 SEMI SINTETICO INCA', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO INCA', 1),
('ACEITE 15W40 SEMI SINTETICO MEXLUB', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO MEXLUB', 1),
('ACEITE 15W40 SEMI SINTETICO RALOY', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO RALOY', 1),
('ACEITE 15W40 SEMI SINTETICO VALVOLINE', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO VALVOLINE', 1),
('ACEITE 15W40 SEMI SINTETICO WOLF', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO WOLF', 1),
('ACEITE 20W50 MINERAL BOSS', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL BOSS', 1),
('ACEITE 20W50 MINERAL FC', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL FC', 1),
('ACEITE 20W50 MINERAL GULF', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL GULF', 1),
('ACEITE 20W50 MINERAL INCA', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL INCA', 1),
('ACEITE 20W50 MINERAL MEXLUB', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL MEXLUB', 1),
('ACEITE 20W50 MINERAL MOBIL', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL MOBIL', 1),
('ACEITE 20W50 MINERAL MOTUL', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL MOTUL', 1),
('ACEITE 20W50 MINERAL RALOY', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL RALOY', 1),
('ACEITE 20W50 MINERAL ROSHFRANS', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL ROSHFRANS', 1),
('ACEITE 20W50 MINERAL VALVOLINE', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL VALVOLINE', 1),
('ACEITE 20W50 SEMI SINTETICO FC', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO FC', 1),
('ACEITE 20W50 SEMI SINTETICO GULF', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO GULF', 1),
('ACEITE 20W50 SEMI SINTETICO INCA', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO INCA', 1),
('ACEITE 20W50 SEMI SINTETICO MEXLUB', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO MEXLUB', 1),
('ACEITE 20W50 SEMI SINTETICO RALOY', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO RALOY', 1),
('ACEITE 20W50 SEMI SINTETICO VALVOLINE', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO VALVOLINE', 1),
('ACEITE 5W20 SINTETICO GULF', 'Marca importada del catalogo real: ACEITE 5W20 SINTETICO GULF', 1),
('ACEITE 5W30 SINTETICO GULF', 'Marca importada del catalogo real: ACEITE 5W30 SINTETICO GULF', 1),
('ACEITE 5W40 SINTETICO GUL', 'Marca importada del catalogo real: ACEITE 5W40 SINTETICO GUL', 1),
('AKRON', 'Marca importada del catalogo real: AKRON', 1),
('ALIX IMPACT AT PLUS', 'Marca importada del catalogo real: ALIX IMPACT AT PLUS', 1),
('ALIX IMPACT HT', 'Marca importada del catalogo real: ALIX IMPACT HT', 1),
('ALIX IMPACT HT PLUS', 'Marca importada del catalogo real: ALIX IMPACT HT PLUS', 1),
('ALIX VELOCE', 'Marca importada del catalogo real: ALIX VELOCE', 1),
('ALIX VEZETTA', 'Marca importada del catalogo real: ALIX VEZETTA', 1),
('ALIX VEZETTA PLUS', 'Marca importada del catalogo real: ALIX VEZETTA PLUS', 1),
('AMBERSTONE MIXTO', 'Marca importada del catalogo real: AMBERSTONE MIXTO', 1),
('ANCHEE', 'Marca importada del catalogo real: ANCHEE', 1),
('ANCHEE MT', 'Marca importada del catalogo real: ANCHEE MT', 1),
('ANNAITE', 'Marca importada del catalogo real: ANNAITE', 1),
('ANNAITE DIRECCIONAL 14PR', 'Marca importada del catalogo real: ANNAITE DIRECCIONAL 14PR', 1),
('AOQISHI A/T', 'Marca importada del catalogo real: AOQISHI A/T', 1),
('AOQISHI MARVEL M/T', 'Marca importada del catalogo real: AOQISHI MARVEL M/T', 1),
('ARMAX', 'Marca importada del catalogo real: ARMAX', 1),
('ARO 24 - 1100', 'Marca importada del catalogo real: ARO 24 - 1100', 1),
('ARO 24R - 1100', 'Marca importada del catalogo real: ARO 24R - 1100', 1),
('ARO 315-1100 (TORNILLO)', 'Marca importada del catalogo real: ARO 315-1100 (TORNILLO)', 1),
('ARO 42-900 (42MR)', 'Marca importada del catalogo real: ARO 42-900 (42MR)', 1),
('ARO 42R-900 (42M)', 'Marca importada del catalogo real: ARO 42R-900 (42M)', 1),
('ARO 99R-700', 'Marca importada del catalogo real: ARO 99R-700', 1),
('ATLANTIC OIL', 'Marca importada del catalogo real: ATLANTIC OIL', 1),
('BITOIL', 'Marca importada del catalogo real: BITOIL', 1),
('BOSS', 'Marca importada del catalogo real: BOSS', 1),
('BRAVA', 'Marca importada del catalogo real: BRAVA', 1),
('CHENSHANG', 'Marca importada del catalogo real: CHENSHANG', 1),
('CROSSLEADER WILDTIGER MT', 'Marca importada del catalogo real: CROSSLEADER WILDTIGER MT', 1),
('DAUER', 'Marca importada del catalogo real: DAUER', 1),
('DOUBLEKING', 'Marca importada del catalogo real: DOUBLEKING', 1),
('DOUBLEKING DK306', 'Marca importada del catalogo real: DOUBLEKING DK306', 1),
('DOUBLEKING DK306 10PR', 'Marca importada del catalogo real: DOUBLEKING DK306 10PR', 1),
('DOUBLESTAR', 'Marca importada del catalogo real: DOUBLESTAR', 1),
('DOUBLESTAR 16 PR', 'Marca importada del catalogo real: DOUBLESTAR 16 PR', 1),
('DOUBLESTAR DH05', 'Marca importada del catalogo real: DOUBLESTAR DH05', 1),
('DOUBLESTAR DS01', 'Marca importada del catalogo real: DOUBLESTAR DS01', 1),
('DURACEL 34R - 1100', 'Marca importada del catalogo real: DURACEL 34R - 1100', 1),
('DURACELL 24-1000 (24MR)', 'Marca importada del catalogo real: DURACELL 24-1000 (24MR)', 1),
('DURACELL 24F-1000 (24M)', 'Marca importada del catalogo real: DURACELL 24F-1000 (24M)', 1),
('DURACELL 31 - 1300S (TORNILLO)', 'Marca importada del catalogo real: DURACELL 31 - 1300S (TORNILLO)', 1),
('DURACELL 34 - 1100', 'Marca importada del catalogo real: DURACELL 34 - 1100', 1),
('DURACELL 42-900 (42MR)', 'Marca importada del catalogo real: DURACELL 42-900 (42MR)', 1),
('DURACELL 42R-900 (42M)', 'Marca importada del catalogo real: DURACELL 42R-900 (42M)', 1),
('DURACELL 99-650 (36MR)', 'Marca importada del catalogo real: DURACELL 99-650 (36MR)', 1),
('DURINGON CROSSMAXX', 'Marca importada del catalogo real: DURINGON CROSSMAXX', 1),
('ECOSAVER DIRECCIONAL 18PR', 'Marca importada del catalogo real: ECOSAVER DIRECCIONAL 18PR', 1),
('EVERLAND', 'Marca importada del catalogo real: EVERLAND', 1),
('EXTREMA 24AD1000-A (24MR)', 'Marca importada del catalogo real: EXTREMA 24AD1000-A (24MR)', 1),
('EXTREME 24BD-720 (42MR)', 'Marca importada del catalogo real: EXTREME 24BD-720 (42MR)', 1),
('EXTREME 24BI-720 (42M)', 'Marca importada del catalogo real: EXTREME 24BI-720 (42M)', 1),
('EXTREME 36DLM700 (36MR)', 'Marca importada del catalogo real: EXTREME 36DLM700 (36MR)', 1),
('FC FAUCI', 'Marca importada del catalogo real: FC FAUCI', 1),
('FIRESTONE DESTINATION H/T', 'Marca importada del catalogo real: FIRESTONE DESTINATION H/T', 1),
('FIRESTONE FIREHAWK', 'Marca importada del catalogo real: FIRESTONE FIREHAWK', 1),
('FIRESTONE MULTIHAWK', 'Marca importada del catalogo real: FIRESTONE MULTIHAWK', 1),
('GONHER', 'Marca importada del catalogo real: GONHER', 1),
('GULF', 'Marca importada del catalogo real: GULF', 1),
('HABILEAD', 'Marca importada del catalogo real: HABILEAD', 1),
('HABILEAD A/T', 'Marca importada del catalogo real: HABILEAD A/T', 1),
('HABILEAD AT', 'Marca importada del catalogo real: HABILEAD AT', 1),
('HABILEAD COMFORMAX', 'Marca importada del catalogo real: HABILEAD COMFORMAX', 1),
('HAIDA 16PR DIRECCIONAL', 'Marca importada del catalogo real: HAIDA 16PR DIRECCIONAL', 1),
('HEADWAY', 'Marca importada del catalogo real: HEADWAY', 1),
('HILO - VANTAGE XU1', 'Marca importada del catalogo real: HILO - VANTAGE XU1', 1),
('HILO DIRECCIONAL 14PR', 'Marca importada del catalogo real: HILO DIRECCIONAL 14PR', 1),
('HILO GENESYS', 'Marca importada del catalogo real: HILO GENESYS', 1),
('HILO GENESYS XP1', 'Marca importada del catalogo real: HILO GENESYS XP1', 1),
('HILO HT', 'Marca importada del catalogo real: HILO HT', 1),
('HILO X-TERRAIN MT1', 'Marca importada del catalogo real: HILO X-TERRAIN MT1', 1),
('HONOUR 14PR DIRECCIONAL', 'Marca importada del catalogo real: HONOUR 14PR DIRECCIONAL', 1),
('INCA', 'Marca importada del catalogo real: INCA', 1),
('MAXTREK SU-830', 'Marca importada del catalogo real: MAXTREK SU-830', 1),
('MEXLUB', 'Marca importada del catalogo real: MEXLUB', 1),
('MILEKING MT', 'Marca importada del catalogo real: MILEKING MT', 1),
('MOBIL', 'Marca importada del catalogo real: MOBIL', 1),
('MOTORCRAFT', 'Marca importada del catalogo real: MOTORCRAFT', 1),
('MOURA ME310FD (36MR)', 'Marca importada del catalogo real: MOURA ME310FD (36MR)', 1),
('MOURA ME570GI (22M)', 'Marca importada del catalogo real: MOURA ME570GI (22M)', 1),
('MOURA ME650RD (24MR)', 'Marca importada del catalogo real: MOURA ME650RD (24MR)', 1),
('MOURA ME805D (36MR)', 'Marca importada del catalogo real: MOURA ME805D (36MR)', 1),
('NOVAMAX STAR A/T', 'Marca importada del catalogo real: NOVAMAX STAR A/T', 1),
('NOVAMAX WARRIOR TERRA T/A', 'Marca importada del catalogo real: NOVAMAX WARRIOR TERRA T/A', 1),
('NOVAMAXX', 'Marca importada del catalogo real: NOVAMAXX', 1),
('NOVAMAXX AT', 'Marca importada del catalogo real: NOVAMAXX AT', 1),
('OILSTONE', 'Marca importada del catalogo real: OILSTONE', 1),
('POWERTAC ECOCOMFORT', 'Marca importada del catalogo real: POWERTAC ECOCOMFORT', 1),
('POWERTRAC', 'Marca importada del catalogo real: POWERTRAC', 1),
('POWERTRAC ADAMAS', 'Marca importada del catalogo real: POWERTRAC ADAMAS', 1),
('POWERTRAC CITYROVER', 'Marca importada del catalogo real: POWERTRAC CITYROVER', 1),
('POWERTRAC DIRECCIONAL', 'Marca importada del catalogo real: POWERTRAC DIRECCIONAL', 1),
('POWERTRAC ECO SPORT X77', 'Marca importada del catalogo real: POWERTRAC ECO SPORT X77', 1),
('POWERTRAC ECOCOMFORT', 'Marca importada del catalogo real: POWERTRAC ECOCOMFORT', 1),
('POWERTRAC ECOCOMFORT X66', 'Marca importada del catalogo real: POWERTRAC ECOCOMFORT X66', 1),
('POWERTRAC MIXTO', 'Marca importada del catalogo real: POWERTRAC MIXTO', 1),
('POWERTRAC TRAC PRO (SET)', 'Marca importada del catalogo real: POWERTRAC TRAC PRO (SET)', 1),
('POWERTRAC TRACCION', 'Marca importada del catalogo real: POWERTRAC TRACCION', 1),
('POWERTRAC VANTOUR', 'Marca importada del catalogo real: POWERTRAC VANTOUR', 1),
('POWERTRAC WILDRANGER A/T', 'Marca importada del catalogo real: POWERTRAC WILDRANGER A/T', 1),
('POWERTRAC WILDRANGER AT', 'Marca importada del catalogo real: POWERTRAC WILDRANGER AT', 1),
('POWERTRAC WILDRANGER M/T', 'Marca importada del catalogo real: POWERTRAC WILDRANGER M/T', 1),
('POWERTRAC WILDRANGER MT', 'Marca importada del catalogo real: POWERTRAC WILDRANGER MT', 1),
('RALOY', 'Marca importada del catalogo real: RALOY', 1),
('RAPID', 'Marca importada del catalogo real: RAPID', 1),
('RAPID ECOLANDER', 'Marca importada del catalogo real: RAPID ECOLANDER', 1),
('RAPID ECOLANDER A/T', 'Marca importada del catalogo real: RAPID ECOLANDER A/T', 1),
('RAPID ECOSAVER', 'Marca importada del catalogo real: RAPID ECOSAVER', 1),
('RAPID MUD CONTENDER M/T', 'Marca importada del catalogo real: RAPID MUD CONTENDER M/T', 1),
('RAPID P329', 'Marca importada del catalogo real: RAPID P329', 1),
('RAPID P609', 'Marca importada del catalogo real: RAPID P609', 1),
('RAPID SHARK Z02', 'Marca importada del catalogo real: RAPID SHARK Z02', 1),
('RAPID TUFTRAIL A/T', 'Marca importada del catalogo real: RAPID TUFTRAIL A/T', 1),
('ROADSHINE 16PR DIRECCIONAL', 'Marca importada del catalogo real: ROADSHINE 16PR DIRECCIONAL', 1),
('ROCKBLADE 14PR DIRECCIONAL', 'Marca importada del catalogo real: ROCKBLADE 14PR DIRECCIONAL', 1),
('ROCKBLADE 787RT', 'Marca importada del catalogo real: ROCKBLADE 787RT', 1),
('ROCKBLADE H/T', 'Marca importada del catalogo real: ROCKBLADE H/T', 1),
('ROYAL BLACK', 'Marca importada del catalogo real: ROYAL BLACK', 1),
('ROYAL BLACK A/T', 'Marca importada del catalogo real: ROYAL BLACK A/T', 1),
('SHELL HELIX', 'Marca importada del catalogo real: SHELL HELIX', 1),
('SKY', 'Marca importada del catalogo real: SKY', 1),
('SUPERMEALLIR DIRECCIONAL', 'Marca importada del catalogo real: SUPERMEALLIR DIRECCIONAL', 1),
('TAITONG 18 PR MIXTO HS268', 'Marca importada del catalogo real: TAITONG 18 PR MIXTO HS268', 1),
('TDI TIRES R/T', 'Marca importada del catalogo real: TDI TIRES R/T', 1),
('V-RICH A/T', 'Marca importada del catalogo real: V-RICH A/T', 1),
('V-RICH ALL TERRAIN', 'Marca importada del catalogo real: V-RICH ALL TERRAIN', 1),
('V-RICH AT', 'Marca importada del catalogo real: V-RICH AT', 1),
('V-RICH AT 10PR', 'Marca importada del catalogo real: V-RICH AT 10PR', 1),
('VALVOLINE', 'Marca importada del catalogo real: VALVOLINE', 1),
('VM LUB', 'Marca importada del catalogo real: VM LUB', 1),
('VM LUBRICANTES', 'Marca importada del catalogo real: VM LUBRICANTES', 1),
('WIDEWAY', 'Marca importada del catalogo real: WIDEWAY', 1),
('WIDEWAY A/T', 'Marca importada del catalogo real: WIDEWAY A/T', 1),
('WIDEWAY AK3 6PR', 'Marca importada del catalogo real: WIDEWAY AK3 6PR', 1),
('WIDEWAY SAFEWAY', 'Marca importada del catalogo real: WIDEWAY SAFEWAY', 1),
('WIDEWAY WEYONE AK3', 'Marca importada del catalogo real: WIDEWAY WEYONE AK3', 1),
('WIDEWAY XT ALL-TERRAIN', 'Marca importada del catalogo real: WIDEWAY XT ALL-TERRAIN', 1),
('WOLF', 'Marca importada del catalogo real: WOLF', 1)
ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion), estado = VALUES(estado);

UPDATE productos SET estado = 0;

INSERT INTO productos (codigo, nombre, descripcion, precio, categoria, marca, imagen, estado) VALUES
('NEU-000013', '165/65R13 HILO GENESYS', 'Caucho 165/65R13. HILO GENESYS. seccion RIN 13 PCR', 35.00, 'Cauchos', 'HILO GENESYS', 'default_product.png', 1),
('NEU-000014', '165/70R13 FIRESTONE MULTIHAWK', 'Caucho 165/70R13. FIRESTONE MULTIHAWK. seccion RIN 13 PCR', 52.00, 'Cauchos', 'FIRESTONE MULTIHAWK', 'default_product.png', 1),
('NEU-000015', '165/70R13 POWERTRAC ECOCOMFORT', 'Caucho 165/70R13. POWERTRAC ECOCOMFORT. seccion RIN 13 PCR', 33.00, 'Cauchos', 'POWERTRAC ECOCOMFORT', 'default_product.png', 1),
('NEU-000016', '165/70R13 ALIX VEZETTA', 'Caucho 165/70R13. ALIX VEZETTA. seccion RIN 13 PCR', 39.00, 'Cauchos', 'ALIX VEZETTA', 'default_product.png', 1),
('NEU-000017', '165/70R13 ROYAL BLACK', 'Caucho 165/70R13. ROYAL BLACK. seccion RIN 13 PCR', 36.00, 'Cauchos', 'ROYAL BLACK', 'default_product.png', 1),
('NEU-000018', '175/70R13 ALIX VEZETTA', 'Caucho 175/70R13. ALIX VEZETTA. seccion RIN 13 PCR', 43.00, 'Cauchos', 'ALIX VEZETTA', 'default_product.png', 1),
('NEU-000019', '175/70R13 FIRESTONE MULTIHAWK', 'Caucho 175/70R13. FIRESTONE MULTIHAWK. seccion RIN 13 PCR', 57.00, 'Cauchos', 'FIRESTONE MULTIHAWK', 'default_product.png', 1),
('NEU-000020', '175/70R13 ROYAL BLACK', 'Caucho 175/70R13. ROYAL BLACK. seccion RIN 13 PCR', 34.00, 'Cauchos', 'ROYAL BLACK', 'default_product.png', 1),
('NEU-000021', '175/70R13 POWERTRAC ADAMAS', 'Caucho 175/70R13. POWERTRAC ADAMAS. seccion RIN 13 PCR', 32.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1),
('NEU-000022', '175/70R13 POWERTRAC ECOCOMFORT', 'Caucho 175/70R13. POWERTRAC ECOCOMFORT. seccion RIN 13 PCR', 32.00, 'Cauchos', 'POWERTRAC ECOCOMFORT', 'default_product.png', 1),
('NEU-000023', '175/70R13 HILO GENESYS XP1', 'Caucho 175/70R13. HILO GENESYS XP1. seccion RIN 13 PCR', 36.00, 'Cauchos', 'HILO GENESYS XP1', 'default_product.png', 1),
('NEU-000024', '175/70R13 DOUBLESTAR', 'Caucho 175/70R13. DOUBLESTAR. seccion RIN 13 PCR', 29.00, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1),
('NEU-000025', '175/70R13 RAPID P329', 'Caucho 175/70R13. RAPID P329. seccion RIN 13 PCR', 37.00, 'Cauchos', 'RAPID P329', 'default_product.png', 1),
('NEU-000026', '175/70R13 HILO GENESYS XP1', 'Caucho 175/70R13. HILO GENESYS XP1. seccion RIN 13 PCR', 36.00, 'Cauchos', 'HILO GENESYS XP1', 'default_product.png', 1),
('NEU-000028', '175/65R14 EVERLAND', 'Caucho 175/65R14. EVERLAND. seccion RIN 14 PCR', 38.00, 'Cauchos', 'EVERLAND', 'default_product.png', 1),
('NEU-000029', '175/65R14 POWERTRAC ADAMAS', 'Caucho 175/65R14. POWERTRAC ADAMAS. seccion RIN 14 PCR', 35.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1),
('NEU-000030', '175/65R14 ALIX VEZETTA', 'Caucho 175/65R14. ALIX VEZETTA. seccion RIN 14 PCR', 47.00, 'Cauchos', 'ALIX VEZETTA', 'default_product.png', 1),
('NEU-000031', '175/65R14 DOUBLESTAR', 'Caucho 175/65R14. DOUBLESTAR. seccion RIN 14 PCR', 32.00, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1),
('NEU-000032', '185/60R14 POWERTRAC ADAMAS', 'Caucho 185/60R14. POWERTRAC ADAMAS. seccion RIN 14 PCR', 36.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1),
('NEU-000033', '185/60R14 DOUBLESTAR', 'Caucho 185/60R14. DOUBLESTAR. seccion RIN 14 PCR', 33.50, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1),
('NEU-000034', '185/65R14 DOUBLESTAR', 'Caucho 185/65R14. DOUBLESTAR. seccion RIN 14 PCR', 35.00, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1),
('NEU-000035', '185/65R14 ALIX VEZETTA', 'Caucho 185/65R14. ALIX VEZETTA. seccion RIN 14 PCR', 53.00, 'Cauchos', 'ALIX VEZETTA', 'default_product.png', 1),
('NEU-000036', '185/65R14 WIDEWAY SAFEWAY', 'Caucho 185/65R14. WIDEWAY SAFEWAY. seccion RIN 14 PCR', 39.00, 'Cauchos', 'WIDEWAY SAFEWAY', 'default_product.png', 1),
('NEU-000037', '185/65R14 FIRESTONE MULTIHAWK', 'Caucho 185/65R14. FIRESTONE MULTIHAWK. seccion RIN 14 PCR', 66.00, 'Cauchos', 'FIRESTONE MULTIHAWK', 'default_product.png', 1),
('NEU-000038', '185/65R14 POWERTRAC ECOCOMFORT X66', 'Caucho 185/65R14. POWERTRAC ECOCOMFORT X66. seccion RIN 14 PCR', 38.00, 'Cauchos', 'POWERTRAC ECOCOMFORT X66', 'default_product.png', 1),
('NEU-000039', '185/65R14 ANCHEE', 'Caucho 185/65R14. ANCHEE. seccion RIN 14 PCR', 41.00, 'Cauchos', 'ANCHEE', 'default_product.png', 1),
('NEU-000040', '185/65R14 ANNAITE', 'Caucho 185/65R14. ANNAITE. seccion RIN 14 PCR', 45.00, 'Cauchos', 'ANNAITE', 'default_product.png', 1),
('NEU-000041', '185/65R14 RAPID P329', 'Caucho 185/65R14. RAPID P329. seccion RIN 14 PCR', 42.00, 'Cauchos', 'RAPID P329', 'default_product.png', 1),
('NEU-000042', '195/70R14 HABILEAD COMFORMAX', 'Caucho 195/70R14. HABILEAD COMFORMAX. seccion RIN 14 PCR', 45.00, 'Cauchos', 'HABILEAD COMFORMAX', 'default_product.png', 1),
('NEU-000043', '205/70R14 HABILEAD', 'Caucho 205/70R14. HABILEAD. seccion RIN 14 PCR', 55.00, 'Cauchos', 'HABILEAD', 'default_product.png', 1),
('NEU-000044', '195R14C WIDEWAY', 'Caucho 195R14C. WIDEWAY. seccion RIN 14 PCR', 75.00, 'Cauchos', 'WIDEWAY', 'default_product.png', 1),
('NEU-000046', '195/60R15 WIDEWAY', 'Caucho 195/60R15. WIDEWAY. seccion RIN 15 PCR', 50.00, 'Cauchos', 'WIDEWAY', 'default_product.png', 1),
('NEU-000047', '195/60R15 ALIX VEZETTA PLUS', 'Caucho 195/60R15. ALIX VEZETTA PLUS. seccion RIN 15 PCR', 68.00, 'Cauchos', 'ALIX VEZETTA PLUS', 'default_product.png', 1),
('NEU-000048', '195/60R15 RAPID', 'Caucho 195/60R15. RAPID. seccion RIN 15 PCR', 53.00, 'Cauchos', 'RAPID', 'default_product.png', 1),
('NEU-000049', '195/60R15 POWERTRAC ADAMAS', 'Caucho 195/60R15. POWERTRAC ADAMAS. seccion RIN 15 PCR', 47.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1),
('NEU-000050', '195/60R15 POWERTAC ECOCOMFORT', 'Caucho 195/60R15. POWERTAC ECOCOMFORT. seccion RIN 15 PCR', 47.00, 'Cauchos', 'POWERTAC ECOCOMFORT', 'default_product.png', 1),
('NEU-000051', '195/65R15 WIDEWAY SAFEWAY', 'Caucho 195/65R15. WIDEWAY SAFEWAY. seccion RIN 15 PCR', 52.00, 'Cauchos', 'WIDEWAY SAFEWAY', 'default_product.png', 1),
('NEU-000052', '195/65R15 POWERTRAC ADAMAS', 'Caucho 195/65R15. POWERTRAC ADAMAS. seccion RIN 15 PCR', 45.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1),
('NEU-000053', '195/65R15 RAPID', 'Caucho 195/65R15. RAPID. seccion RIN 15 PCR', 55.00, 'Cauchos', 'RAPID', 'default_product.png', 1),
('NEU-000054', '195/65R15 DOUBLESTAR', 'Caucho 195/65R15. DOUBLESTAR. seccion RIN 15 PCR', 41.00, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1),
('NEU-000055', '205/70R15 MAXTREK SU-830', 'Caucho 205/70R15. MAXTREK SU-830. seccion RIN 15 PCR', 65.00, 'Cauchos', 'MAXTREK SU-830', 'default_product.png', 1),
('NEU-000056', '205/70R15 FIRESTONE DESTINATION H/T', 'Caucho 205/70R15. FIRESTONE DESTINATION H/T. seccion RIN 15 PCR', 100.00, 'Cauchos', 'FIRESTONE DESTINATION H/T', 'default_product.png', 1),
('NEU-000057', '215/65R15 HEADWAY', 'Caucho 215/65R15. HEADWAY. seccion RIN 15 PCR', 40.00, 'Cauchos', 'HEADWAY', 'default_product.png', 1),
('NEU-000058', '215/70R15 WIDEWAY SAFEWAY', 'Caucho 215/70R15. WIDEWAY SAFEWAY. seccion RIN 15 PCR', 80.00, 'Cauchos', 'WIDEWAY SAFEWAY', 'default_product.png', 1),
('NEU-000059', '205/70R15C POWERTRAC VANTOUR', 'Caucho 205/70R15C. POWERTRAC VANTOUR. seccion RIN 15 PCR', 68.00, 'Cauchos', 'POWERTRAC VANTOUR', 'default_product.png', 1),
('NEU-000060', 'LT235/75R15 POWERTRAC WILDRANGER M/T', 'Caucho LT235/75R15. POWERTRAC WILDRANGER M/T. seccion RIN 15 PCR', 90.00, 'Cauchos', 'POWERTRAC WILDRANGER M/T', 'default_product.png', 1),
('NEU-000061', 'LT235/75R15 POWERTRAC WILDRANGER A/T', 'Caucho LT235/75R15. POWERTRAC WILDRANGER A/T. seccion RIN 15 PCR', 100.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1),
('NEU-000062', '235/75R15 NOVAMAXX AT', 'Caucho 235/75R15. NOVAMAXX AT. seccion RIN 15 PCR', 85.00, 'Cauchos', 'NOVAMAXX AT', 'default_product.png', 1),
('NEU-000063', 'P235/75R15 POWERTRAC WILDRANGER A/T', 'Caucho P235/75R15. POWERTRAC WILDRANGER A/T. seccion RIN 15 PCR', 90.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1),
('NEU-000064', '235/75R15 RAPID ECOSAVER', 'Caucho 235/75R15. RAPID ECOSAVER. seccion RIN 15 PCR', 90.00, 'Cauchos', 'RAPID ECOSAVER', 'default_product.png', 1),
('NEU-000065', '235/75R15 WIDEWAY AK3 6PR', 'Caucho 235/75R15. WIDEWAY AK3 6PR. seccion RIN 15 PCR', 130.00, 'Cauchos', 'WIDEWAY AK3 6PR', 'default_product.png', 1),
('NEU-000067', '235/75R15 HILO HT', 'Caucho 235/75R15. HILO HT. seccion RIN 15 PCR', 100.00, 'Cauchos', 'HILO HT', 'default_product.png', 1),
('NEU-000068', '235/75R15 NOVAMAXX', 'Caucho 235/75R15. NOVAMAXX. seccion RIN 15 PCR', 85.00, 'Cauchos', 'NOVAMAXX', 'default_product.png', 1),
('NEU-000069', 'P235/75R15 DOUBLEKING DK306', 'Caucho P235/75R15. DOUBLEKING DK306. seccion RIN 15 PCR', 80.00, 'Cauchos', 'DOUBLEKING DK306', 'default_product.png', 1),
('NEU-000070', 'LT235/75R15 DOUBLEKING DK306 10PR', 'Caucho LT235/75R15. DOUBLEKING DK306 10PR. seccion RIN 15 PCR', 90.00, 'Cauchos', 'DOUBLEKING DK306 10PR', 'default_product.png', 1),
('NEU-000071', '295/50R15 RAPID SHARK Z02', 'Caucho 295/50R15. RAPID SHARK Z02. seccion RIN 15 PCR', 127.00, 'Cauchos', 'RAPID SHARK Z02', 'default_product.png', 1),
('NEU-000072', '31X10.50R15 ANCHEE MT', 'Caucho 31X10.50R15. ANCHEE MT. seccion RIN 15 PCR', 165.00, 'Cauchos', 'ANCHEE MT', 'default_product.png', 1),
('NEU-000073', '31X10.50R15 HILO X-TERRAIN MT1', 'Caucho 31X10.50R15. HILO X-TERRAIN MT1. seccion RIN 15 PCR', 165.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1),
('NEU-000074', '31X10.50R15 WIDEWAY A/T', 'Caucho 31X10.50R15. WIDEWAY A/T. seccion RIN 15 PCR', 165.00, 'Cauchos', 'WIDEWAY A/T', 'default_product.png', 1),
('NEU-000075', '31X10.50R15 V-RICH A/T', 'Caucho 31X10.50R15. V-RICH A/T. seccion RIN 15 PCR', 170.00, 'Cauchos', 'V-RICH A/T', 'default_product.png', 1),
('NEU-000076', '31X10.50R15 LT ROCKBLADE 787RT', 'Caucho 31X10.50R15 LT. ROCKBLADE 787RT. seccion RIN 15 PCR', 135.00, 'Cauchos', 'ROCKBLADE 787RT', 'default_product.png', 1),
('NEU-000077', '31X10.50R15 LT HABILEAD AT', 'Caucho 31X10.50R15 LT. HABILEAD AT. seccion RIN 15 PCR', 125.00, 'Cauchos', 'HABILEAD AT', 'default_product.png', 1),
('NEU-000078', '31X10.50R15 POWERTRAC WILDRANGER A/T', 'Caucho 31X10.50R15. POWERTRAC WILDRANGER A/T. seccion RIN 15 PCR', 130.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1),
('NEU-000079', '31X10.50R15 POWERTRAC WILDRANGER M/T', 'Caucho 31X10.50R15. POWERTRAC WILDRANGER M/T. seccion RIN 15 PCR', 137.00, 'Cauchos', 'POWERTRAC WILDRANGER M/T', 'default_product.png', 1),
('NEU-000081', '31X10.50R15 AOQISHI MARVEL M/T', 'Caucho 31X10.50R15. AOQISHI MARVEL M/T. seccion RIN 15 PCR', 140.00, 'Cauchos', 'AOQISHI MARVEL M/T', 'default_product.png', 1),
('NEU-000082', '31X10.50R15 DURINGON CROSSMAXX', 'Caucho 31X10.50R15. DURINGON CROSSMAXX. seccion RIN 15 PCR', 140.00, 'Cauchos', 'DURINGON CROSSMAXX', 'default_product.png', 1),
('NEU-000083', '31X10.50R15 CROSSLEADER WILDTIGER MT', 'Caucho 31X10.50R15. CROSSLEADER WILDTIGER MT. seccion RIN 15 PCR', 115.00, 'Cauchos', 'CROSSLEADER WILDTIGER MT', 'default_product.png', 1),
('NEU-000084', '31X10.50R15 RAPID TUFTRAIL A/T', 'Caucho 31X10.50R15. RAPID TUFTRAIL A/T. seccion RIN 15 PCR', 135.00, 'Cauchos', 'RAPID TUFTRAIL A/T', 'default_product.png', 1),
('NEU-000085', '31X10.50R15 RAPID MUD CONTENDER M/T', 'Caucho 31X10.50R15. RAPID MUD CONTENDER M/T. seccion RIN 15 PCR', 145.00, 'Cauchos', 'RAPID MUD CONTENDER M/T', 'default_product.png', 1),
('NEU-000086', 'LT32X11.5R15 HILO X-TERRAIN MT1', 'Caucho LT32X11.5R15. HILO X-TERRAIN MT1. seccion RIN 15 PCR', 200.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1),
('NEU-000087', '33X12.5R15LT HILO X-TERRAIN MT1', 'Caucho 33X12.5R15LT. HILO X-TERRAIN MT1. seccion RIN 15 PCR', 210.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1),
('NEU-000088', 'LT7.00R15 7.00R15 KOBATA', 'Caucho LT7.00R15. 7.00R15 KOBATA. seccion RIN 15 PCR', 95.00, 'Cauchos', '7.00R15 KOBATA', 'default_product.png', 1),
('NEU-000089', 'LT35X12.5R15 HILO X-TERRAIN MT1', 'Caucho LT35X12.5R15. HILO X-TERRAIN MT1. seccion RIN 15 PCR', 225.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1),
('NEU-000091', '195/55R16 POWERTRAC ADAMAS', 'Caucho 195/55R16. POWERTRAC ADAMAS. seccion RIN 16 PCR', 45.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1),
('NEU-000092', '195/55R16 WIDEWAY', 'Caucho 195/55R16. WIDEWAY. seccion RIN 16 PCR', 58.00, 'Cauchos', 'WIDEWAY', 'default_product.png', 1),
('NEU-000093', '205/55R16 ANCHEE', 'Caucho 205/55R16. ANCHEE. seccion RIN 16 PCR', 53.00, 'Cauchos', 'ANCHEE', 'default_product.png', 1),
('NEU-000094', '205/55R16 ALIX VELOCE', 'Caucho 205/55R16. ALIX VELOCE. seccion RIN 16 PCR', 70.00, 'Cauchos', 'ALIX VELOCE', 'default_product.png', 1),
('NEU-000095', '205/55R16 POWERTRAC ECOCOMFORT X66', 'Caucho 205/55R16. POWERTRAC ECOCOMFORT X66. seccion RIN 16 PCR', 54.00, 'Cauchos', 'POWERTRAC ECOCOMFORT X66', 'default_product.png', 1),
('NEU-000096', '205/55R16 DOUBLESTAR DH05', 'Caucho 205/55R16. DOUBLESTAR DH05. seccion RIN 16 PCR', 41.00, 'Cauchos', 'DOUBLESTAR DH05', 'default_product.png', 1),
('NEU-000097', '215/60R16 POWERTRAC', 'Caucho 215/60R16. POWERTRAC. seccion RIN 16 PCR', 56.00, 'Cauchos', 'POWERTRAC', 'default_product.png', 1),
('NEU-000098', '235/60R16 ALIX IMPACT HT', 'Caucho 235/60R16. ALIX IMPACT HT. seccion RIN 16 PCR', 93.00, 'Cauchos', 'ALIX IMPACT HT', 'default_product.png', 1),
('NEU-000099', '235/60R16 POWERTRAC ADAMAS', 'Caucho 235/60R16. POWERTRAC ADAMAS. seccion RIN 16 PCR', 75.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1),
('NEU-000100', '235/70R16 NOVAMAXX AT', 'Caucho 235/70R16. NOVAMAXX AT. seccion RIN 16 PCR', 100.00, 'Cauchos', 'NOVAMAXX AT', 'default_product.png', 1),
('NEU-000101', '245/70R16 DOUBLESTAR DS01', 'Caucho 245/70R16. DOUBLESTAR DS01. seccion RIN 16 PCR', 87.00, 'Cauchos', 'DOUBLESTAR DS01', 'default_product.png', 1),
('NEU-000102', '245/70R16 POWERTRAC WILDRANGER A/T', 'Caucho 245/70R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR', 100.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1),
('NEU-000103', 'LT245/75R16 POWERTRAC WILDRANGER A/T', 'Caucho LT245/75R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR', 110.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1),
('NEU-000104', 'P255/70R16 ALIX IMPACT HT PLUS', 'Caucho P255/70R16. ALIX IMPACT HT PLUS. seccion RIN 16 PCR', 135.00, 'Cauchos', 'ALIX IMPACT HT PLUS', 'default_product.png', 1),
('NEU-000105', '255/70R16 TDI TIRES R/T', 'Caucho 255/70R16. TDI TIRES R/T. seccion RIN 16 PCR', 110.00, 'Cauchos', 'TDI TIRES R/T', 'default_product.png', 1),
('NEU-000106', 'LT265/70R16 V-RICH AT', 'Caucho LT265/70R16. V-RICH AT. seccion RIN 16 PCR', 175.00, 'Cauchos', 'V-RICH AT', 'default_product.png', 1),
('NEU-000107', 'LT265/75R16 POWERTRAC WILDRANGER A/T', 'Caucho LT265/75R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR', 145.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1),
('NEU-000108', 'P265/75R16 NOVAMAX WARRIOR TERRA T/A', 'Caucho P265/75R16. NOVAMAX WARRIOR TERRA T/A. seccion RIN 16 PCR', 140.00, 'Cauchos', 'NOVAMAX WARRIOR TERRA T/A', 'default_product.png', 1),
('NEU-000109', 'LT265/75R16 ROYAL BLACK A/T', 'Caucho LT265/75R16. ROYAL BLACK A/T. seccion RIN 16 PCR', 150.00, 'Cauchos', 'ROYAL BLACK A/T', 'default_product.png', 1),
('NEU-000110', '265/75R16 V-RICH AT 10PR', 'Caucho 265/75R16. V-RICH AT 10PR. seccion RIN 16 PCR', 195.00, 'Cauchos', 'V-RICH AT 10PR', 'default_product.png', 1),
('NEU-000112', 'P265/75R16 TDI TIRES R/T', 'Caucho P265/75R16. TDI TIRES R/T. seccion RIN 16 PCR', 127.00, 'Cauchos', 'TDI TIRES R/T', 'default_product.png', 1),
('NEU-000114', 'LT265/75R16 ALIX IMPACT AT PLUS', 'Caucho LT265/75R16. ALIX IMPACT AT PLUS. seccion RIN 16 PCR', 175.00, 'Cauchos', 'ALIX IMPACT AT PLUS', 'default_product.png', 1),
('NEU-000115', 'LT265/75R16 V-RICH ALL TERRAIN', 'Caucho LT265/75R16. V-RICH ALL TERRAIN. seccion RIN 16 PCR', 185.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1),
('NEU-000116', 'LT265/75R16 HILO X-TERRAIN MT1', 'Caucho LT265/75R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR', 200.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1),
('NEU-000117', 'LT265/75R16 RAPID TUFTRAIL A/T', 'Caucho LT265/75R16. RAPID TUFTRAIL A/T. seccion RIN 16 PCR', 165.00, 'Cauchos', 'RAPID TUFTRAIL A/T', 'default_product.png', 1),
('NEU-000118', 'LT265/75R16 NOVAMAX STAR A/T', 'Caucho LT265/75R16. NOVAMAX STAR A/T. seccion RIN 16 PCR', 127.00, 'Cauchos', 'NOVAMAX STAR A/T', 'default_product.png', 1),
('NEU-000119', 'LT285/75R16 POWERTRAC WILDRANGER A/T', 'Caucho LT285/75R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR', 160.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1),
('NEU-000120', '285/75R16 V-RICH A/T', 'Caucho 285/75R16. V-RICH A/T. seccion RIN 16 PCR', 195.00, 'Cauchos', 'V-RICH A/T', 'default_product.png', 1),
('NEU-000121', '285/75R16 HILO X-TERRAIN MT1', 'Caucho 285/75R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR', 210.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1),
('NEU-000123', '285/75R16 RAPID ECOLANDER A/T', 'Caucho 285/75R16. RAPID ECOLANDER A/T. seccion RIN 16 PCR', 175.00, 'Cauchos', 'RAPID ECOLANDER A/T', 'default_product.png', 1),
('NEU-000124', 'LT285/75R16 AOQISHI A/T', 'Caucho LT285/75R16. AOQISHI A/T. seccion RIN 16 PCR', 160.00, 'Cauchos', 'AOQISHI A/T', 'default_product.png', 1),
('NEU-000126', 'LT285/75R16 WIDEWAY XT ALL-TERRAIN', 'Caucho LT285/75R16. WIDEWAY XT ALL-TERRAIN. seccion RIN 16 PCR', 200.00, 'Cauchos', 'WIDEWAY XT ALL-TERRAIN', 'default_product.png', 1),
('NEU-000127', '305/70R16 HILO X-TERRAIN MT1', 'Caucho 305/70R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR', 220.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1),
('NEU-000128', '315/75R16 POWERTRAC WILDRANGER M/T', 'Caucho 315/75R16. POWERTRAC WILDRANGER M/T. seccion RIN 16 PCR', 215.00, 'Cauchos', 'POWERTRAC WILDRANGER M/T', 'default_product.png', 1),
('NEU-000129', '315/75R16 HILO X-TERRAIN MT1', 'Caucho 315/75R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR', 240.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1),
('NEU-000131', '7.50R16 HILO DIRECCIONAL 14PR', 'Caucho 7.50R16. HILO DIRECCIONAL 14PR. seccion RIN 16 TBR', 120.00, 'Cauchos', 'HILO DIRECCIONAL 14PR', 'default_product.png', 1),
('NEU-000132', '7.50R16 ANNAITE DIRECCIONAL 14PR', 'Caucho 7.50R16. ANNAITE DIRECCIONAL 14PR. seccion RIN 16 TBR', 120.00, 'Cauchos', 'ANNAITE DIRECCIONAL 14PR', 'default_product.png', 1),
('NEU-000133', '7.50-16 POWERTRAC TRAC PRO (SET)', 'Caucho 7.50-16. POWERTRAC TRAC PRO (SET). seccion RIN 16 TBR', 126.00, 'Cauchos', 'POWERTRAC TRAC PRO (SET)', 'default_product.png', 1),
('NEU-000134', '7.50R16 HONOUR 14PR DIRECCIONAL', 'Caucho 7.50R16. HONOUR 14PR DIRECCIONAL. seccion RIN 16 TBR', 105.00, 'Cauchos', 'HONOUR 14PR DIRECCIONAL', 'default_product.png', 1),
('NEU-000135', '7.50R16 HAIDA 16PR DIRECCIONAL', 'Caucho 7.50R16. HAIDA 16PR DIRECCIONAL. seccion RIN 16 TBR', 135.00, 'Cauchos', 'HAIDA 16PR DIRECCIONAL', 'default_product.png', 1),
('NEU-000136', '7.50R16 ROCKBLADE 14PR DIRECCIONAL', 'Caucho 7.50R16. ROCKBLADE 14PR DIRECCIONAL. seccion RIN 16 TBR', 100.00, 'Cauchos', 'ROCKBLADE 14PR DIRECCIONAL', 'default_product.png', 1),
('NEU-000137', '7.50R16 ROADSHINE 16PR DIRECCIONAL', 'Caucho 7.50R16. ROADSHINE 16PR DIRECCIONAL. seccion RIN 16 TBR', 135.00, 'Cauchos', 'ROADSHINE 16PR DIRECCIONAL', 'default_product.png', 1),
('NEU-000139', '215/60R17 POWERTRAC CITYROVER', 'Caucho 215/60R17. POWERTRAC CITYROVER. seccion RIN 17 PCR', 70.00, 'Cauchos', 'POWERTRAC CITYROVER', 'default_product.png', 1),
('NEU-000140', '225/50ZR17 HILO - VANTAGE XU1', 'Caucho 225/50ZR17. HILO - VANTAGE XU1. seccion RIN 17 PCR', 90.00, 'Cauchos', 'HILO - VANTAGE XU1', 'default_product.png', 1),
('NEU-000141', '205/45R17 RAPID P609', 'Caucho 205/45R17. RAPID P609. seccion RIN 17 PCR', 80.00, 'Cauchos', 'RAPID P609', 'default_product.png', 1),
('NEU-000145', '215/45R17 RAPID P609', 'Caucho 215/45R17. RAPID P609. seccion RIN 17 PCR', 80.00, 'Cauchos', 'RAPID P609', 'default_product.png', 1),
('NEU-000146', '215/45R17 DOUBLESTAR', 'Caucho 215/45R17. DOUBLESTAR. seccion RIN 17 PCR', 60.00, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1),
('NEU-000147', '215/60R17 FIRESTONE FIREHAWK', 'Caucho 215/60R17. FIRESTONE FIREHAWK. seccion RIN 17 PCR', 109.00, 'Cauchos', 'FIRESTONE FIREHAWK', 'default_product.png', 1),
('NEU-000150', '245/65R17 DOUBLEKING', 'Caucho 245/65R17. DOUBLEKING. seccion RIN 17 PCR', 115.00, 'Cauchos', 'DOUBLEKING', 'default_product.png', 1),
('NEU-000151', '265/70R17 RAPID ECOLANDER', 'Caucho 265/70R17. RAPID ECOLANDER. seccion RIN 17 PCR', 145.00, 'Cauchos', 'RAPID ECOLANDER', 'default_product.png', 1),
('NEU-000152', 'LT265/70R17 V-RICH ALL TERRAIN', 'Caucho LT265/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR', 180.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1),
('NEU-000153', 'LT265/70R17 AOQISHI A/T', 'Caucho LT265/70R17. AOQISHI A/T. seccion RIN 17 PCR', 150.00, 'Cauchos', 'AOQISHI A/T', 'default_product.png', 1),
('NEU-000154', '275/70R17 AOQISHI A/T', 'Caucho 275/70R17. AOQISHI A/T. seccion RIN 17 PCR', 160.00, 'Cauchos', 'AOQISHI A/T', 'default_product.png', 1),
('NEU-000155', 'LT275/70R17 V-RICH ALL TERRAIN', 'Caucho LT275/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR', 190.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1),
('NEU-000157', 'LT285/70R17 POWERTRAC WILDRANGER AT', 'Caucho LT285/70R17. POWERTRAC WILDRANGER AT. seccion RIN 17 PCR', 170.00, 'Cauchos', 'POWERTRAC WILDRANGER AT', 'default_product.png', 1),
('NEU-000158', 'LT285/70R17 POWERTRAC WILDRANGER MT', 'Caucho LT285/70R17. POWERTRAC WILDRANGER MT. seccion RIN 17 PCR', 175.00, 'Cauchos', 'POWERTRAC WILDRANGER MT', 'default_product.png', 1),
('NEU-000159', 'LT285/70R17 HILO X-TERRAIN MT1', 'Caucho LT285/70R17. HILO X-TERRAIN MT1. seccion RIN 17 PCR', 210.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1),
('NEU-000160', 'LT285/70R17 WIDEWAY XT ALL-TERRAIN', 'Caucho LT285/70R17. WIDEWAY XT ALL-TERRAIN. seccion RIN 17 PCR', 185.00, 'Cauchos', 'WIDEWAY XT ALL-TERRAIN', 'default_product.png', 1),
('NEU-000161', 'LT285/70R17 V-RICH ALL TERRAIN', 'Caucho LT285/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR', 195.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1),
('NEU-000162', 'LT315/70R17 V-RICH ALL TERRAIN', 'Caucho LT315/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR', 220.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1),
('NEU-000165', '215/75R17.5 POWERTRAC', 'Caucho 215/75R17.5. POWERTRAC. seccion RIN 17.5 TBR', 140.00, 'Cauchos', 'POWERTRAC', 'default_product.png', 1),
('NEU-000166', '235/75R17.5 POWERTRAC', 'Caucho 235/75R17.5. POWERTRAC. seccion RIN 17.5 TBR', 165.00, 'Cauchos', 'POWERTRAC', 'default_product.png', 1),
('NEU-000167', '235/75R17.5 CHENSHANG', 'Caucho 235/75R17.5. CHENSHANG. seccion RIN 17.5 TBR', 160.00, 'Cauchos', 'CHENSHANG', 'default_product.png', 1),
('NEU-000169', '225/40ZR18 POWERTRAC ECO SPORT X77', 'Caucho 225/40ZR18. POWERTRAC ECO SPORT X77. seccion RIN 18 PCR', 80.00, 'Cauchos', 'POWERTRAC ECO SPORT X77', 'default_product.png', 1),
('NEU-000170', '235/50ZR18 POWERTRAC ECO SPORT X77', 'Caucho 235/50ZR18. POWERTRAC ECO SPORT X77. seccion RIN 18 PCR', 85.00, 'Cauchos', 'POWERTRAC ECO SPORT X77', 'default_product.png', 1),
('NEU-000171', '245/60R18 POWERTRAC CITYROVER', 'Caucho 245/60R18. POWERTRAC CITYROVER. seccion RIN 18 PCR', 105.00, 'Cauchos', 'POWERTRAC CITYROVER', 'default_product.png', 1),
('NEU-000172', '35X12.50R18 WIDEWAY', 'Caucho 35X12.50R18. WIDEWAY. seccion RIN 18 PCR', 235.00, 'Cauchos', 'WIDEWAY', 'default_product.png', 1),
('NEU-000174', '265/60R18 HABILEAD A/T', 'Caucho 265/60R18. HABILEAD A/T. seccion RIN 18 PCR', 105.00, 'Cauchos', 'HABILEAD A/T', 'default_product.png', 1),
('NEU-000175', '265/60R18 ROCKBLADE H/T', 'Caucho 265/60R18. ROCKBLADE H/T. seccion RIN 18 PCR', 110.00, 'Cauchos', 'ROCKBLADE H/T', 'default_product.png', 1),
('NEU-000176', '37x13.5R18 MILEKING MT', 'Caucho 37x13.5R18. MILEKING MT. seccion RIN 18 PCR', 295.00, 'Cauchos', 'MILEKING MT', 'default_product.png', 1),
('NEU-000178', '275/55R20 WIDEWAY WEYONE AK3', 'Caucho 275/55R20. WIDEWAY WEYONE AK3. seccion RIN 20 PCR', 205.00, 'Cauchos', 'WIDEWAY WEYONE AK3', 'default_product.png', 1),
('NEU-000179', '275/55R20 V-RICH ALL TERRAIN', 'Caucho 275/55R20. V-RICH ALL TERRAIN. seccion RIN 20 PCR', 205.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1),
('NEU-000181', '35X12.5R20 POWERTRAC WILDRANGER M/T', 'Caucho 35X12.5R20. POWERTRAC WILDRANGER M/T. seccion RIN 20 PCR', 250.00, 'Cauchos', 'POWERTRAC WILDRANGER M/T', 'default_product.png', 1),
('NEU-000182', '8.25R20 DOUBLESTAR 16 PR', 'Caucho 8.25R20. DOUBLESTAR 16 PR. seccion RIN 20 PCR', 150.00, 'Cauchos', 'DOUBLESTAR 16 PR', 'default_product.png', 1),
('NEU-000184', '295/80R22.5 TAITONG 18 PR MIXTO HS268', 'Caucho 295/80R22.5. TAITONG 18 PR MIXTO HS268. seccion RIN 22.5 TBR', 220.00, 'Cauchos', 'TAITONG 18 PR MIXTO HS268', 'default_product.png', 1),
('NEU-000185', '295/80R22.5 ECOSAVER DIRECCIONAL 18PR', 'Caucho 295/80R22.5. ECOSAVER DIRECCIONAL 18PR. seccion RIN 22.5 TBR', 200.00, 'Cauchos', 'ECOSAVER DIRECCIONAL 18PR', 'default_product.png', 1),
('NEU-000186', '295/80R22.5 POWERTRAC DIRECCIONAL', 'Caucho 295/80R22.5. POWERTRAC DIRECCIONAL. seccion RIN 22.5 TBR', 210.00, 'Cauchos', 'POWERTRAC DIRECCIONAL', 'default_product.png', 1),
('NEU-000187', '295/80R22.5 POWERTRAC MIXTO', 'Caucho 295/80R22.5. POWERTRAC MIXTO. seccion RIN 22.5 TBR', 220.00, 'Cauchos', 'POWERTRAC MIXTO', 'default_product.png', 1),
('NEU-000188', '295/80R22.5 POWERTRAC TRACCION', 'Caucho 295/80R22.5. POWERTRAC TRACCION. seccion RIN 22.5 TBR', 238.00, 'Cauchos', 'POWERTRAC TRACCION', 'default_product.png', 1),
('NEU-000190', '315/80R22.5 SUPERMEALLIR DIRECCIONAL', 'Caucho 315/80R22.5. SUPERMEALLIR DIRECCIONAL. seccion RIN 22.5 TBR', 200.00, 'Cauchos', 'SUPERMEALLIR DIRECCIONAL', 'default_product.png', 1),
('NEU-000191', '12RR2.5 POWERTRAC MIXTO', 'Caucho 12RR2.5. POWERTRAC MIXTO. seccion RIN 22.5 TBR', 230.00, 'Cauchos', 'POWERTRAC MIXTO', 'default_product.png', 1),
('NEU-000192', '315/80R22.5 SUPERMEALLIR DIRECCIONAL', 'Caucho 315/80R22.5. SUPERMEALLIR DIRECCIONAL. seccion RIN 22.5 TBR', 200.00, 'Cauchos', 'SUPERMEALLIR DIRECCIONAL', 'default_product.png', 1),
('NEU-000193', '315/80R22.5 AMBERSTONE MIXTO', 'Caucho 315/80R22.5. AMBERSTONE MIXTO. seccion RIN 22.5 TBR', 215.00, 'Cauchos', 'AMBERSTONE MIXTO', 'default_product.png', 1),
('NEU-000194', '315/80R22.5 POWERTRAC DIRECCIONAL', 'Caucho 315/80R22.5. POWERTRAC DIRECCIONAL. seccion RIN 22.5 TBR', 235.00, 'Cauchos', 'POWERTRAC DIRECCIONAL', 'default_product.png', 1),
('LUB-000005', '15W40 MINERAL BRAVA S/N', 'Lubricante 15W40 MINERAL. BRAVA', 7.00, 'Lubricantes', 'BRAVA', 'default_product.png', 1),
('LUB-000006', '15W40 MINERAL ARMAX', 'Lubricante 15W40 MINERAL. ARMAX', 5.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1),
('LUB-000007', '15W40 MINERAL FC', 'Lubricante 15W40 MINERAL. FC FAUCI', 5.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1),
('LUB-000008', '15W40 MINERAL GULF MAX GDI', 'Lubricante 15W40 MINERAL. GULF', 9.00, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000009', '15W40 MINERAL DAUER', 'Lubricante 15W40 MINERAL. DAUER', 7.50, 'Lubricantes', 'DAUER', 'default_product.png', 1),
('LUB-000010', '15W40 MINERAL AKRON', 'Lubricante 15W40 MINERAL. AKRON', 7.50, 'Lubricantes', 'AKRON', 'default_product.png', 1),
('LUB-000011', '15W40 MINERAL INCA', 'Lubricante 15W40 MINERAL. INCA', 8.50, 'Lubricantes', 'INCA', 'default_product.png', 1),
('LUB-000012', '15W40 MINERAL VALVOLINE CLASSIC', 'Lubricante 15W40 MINERAL. VALVOLINE', 7.50, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1),
('LUB-000013', '20W50 MINERAL ATLANTIC', 'Lubricante 20W50 MINERAL. ATLANTIC OIL', 4.50, 'Lubricantes', 'ATLANTIC OIL', 'default_product.png', 1),
('LUB-000014', '20W50 MINERAL FC', 'Lubricante 20W50 MINERAL. FC FAUCI', 6.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1),
('LUB-000015', '15W40 MINERAL ARMAX', 'Lubricante 20W50 MINERAL. ARMAX', 5.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1),
('LUB-000016', '20W50 MINERAL GONHER', 'Lubricante 20W50 MINERAL. GONHER', 6.50, 'Lubricantes', 'GONHER', 'default_product.png', 1),
('LUB-000017', '20W50 MINERAL AKRON', 'Lubricante 20W50 MINERAL. AKRON', 7.50, 'Lubricantes', 'AKRON', 'default_product.png', 1),
('LUB-000018', '20W50 MINERAL BITOIL', 'Lubricante 20W50 MINERAL. BITOIL', 4.00, 'Lubricantes', 'BITOIL', 'default_product.png', 1),
('LUB-000019', '20W50 MINERAL RALOY RACING OIL MULTIGRADE', 'Lubricante 20W50 MINERAL. RALOY', 7.00, 'Lubricantes', 'RALOY', 'default_product.png', 1),
('LUB-000020', '20W50 MINERAL DAUER', 'Lubricante 20W50 MINERAL. DAUER', 7.50, 'Lubricantes', 'DAUER', 'default_product.png', 1),
('LUB-000021', '20W50 MINERAL BRAVA S/N', 'Lubricante 20W50 MINERAL. BRAVA', 7.00, 'Lubricantes', 'BRAVA', 'default_product.png', 1),
('LUB-000022', '20W50 MINERAL GULF MAX GDI', 'Lubricante 20W50 MINERAL. GULF', 9.00, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000023', '20W50 MINERAL INCA', 'Lubricante 20W50 MINERAL. INCA', 8.50, 'Lubricantes', 'INCA', 'default_product.png', 1),
('LUB-000024', '20W50 MINERAL MEXLUB RACING SL 946ML', 'Lubricante 20W50 MINERAL. MEXLUB', 6.00, 'Lubricantes', 'MEXLUB', 'default_product.png', 1),
('LUB-000025', '20W50 VALVOLINE MINERAL 0.946L', 'Lubricante 20W50 MINERAL. VALVOLINE', 7.50, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1),
('LUB-000026', '20W50 MINERAL MOBIL SUPER 1000', 'Lubricante 20W50 MINERAL. MOBIL', 8.00, 'Lubricantes', 'MOBIL', 'default_product.png', 1),
('LUB-000027', '20W50 MINERAL VM LUB', 'Lubricante 20W50 MINERAL. VM LUB', 5.00, 'Lubricantes', 'VM LUB', 'default_product.png', 1),
('LUB-000028', '25W60 MINERAL BOSS', 'Lubricante 25W60 MINERAL. BOSS', 4.50, 'Lubricantes', 'BOSS', 'default_product.png', 1),
('LUB-000029', '10W30 SEMI SINTETICO GULF TEC GDI', 'Lubricante 10W30 SEMI SINTETICO. GULF', 11.00, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000030', '10W30 SEMI SINTETICO VALVOLINE', 'Lubricante 10W30 SEMI SINTETICO. VALVOLINE', 7.50, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1),
('LUB-000031', '10W30 SEMI SINTETICO DAUER', 'Lubricante 10W30 SEMI SINTETICO. DAUER', 9.00, 'Lubricantes', 'DAUER', 'default_product.png', 1),
('LUB-000032', '10W30 SEMI SINTETICO MOBIL', 'Lubricante 10W30 SEMI SINTETICO. MOBIL', 9.50, 'Lubricantes', 'MOBIL', 'default_product.png', 1),
('LUB-000033', '10W40 SEMI SINTETICO MOBIL SUPER 2000', 'Lubricante 10W40 SEMI SINTETICO. MOBIL', 10.00, 'Lubricantes', 'MOBIL', 'default_product.png', 1),
('LUB-000034', '15W40 SEMI SINTETICO BOSS', 'Lubricante 15W40 SEMI SINTETICO. BOSS', 5.00, 'Lubricantes', 'BOSS', 'default_product.png', 1),
('LUB-000035', 'ACEITE 20W50 SEMI SINTETICO BRAVA', 'Lubricante 15W40 SEMI SINTETICO. BRAVA', 7.40, 'Lubricantes', 'BRAVA', 'default_product.png', 1),
('LUB-000036', '15W40 SEMI SINTETICO ARMAX', 'Lubricante 15W40 SEMI SINTETICO. ARMAX', 5.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1),
('LUB-000037', '15W40 SEMI SINTETICO GONHER', 'Lubricante 15W40 SEMI SINTETICO. GONHER', 8.00, 'Lubricantes', 'GONHER', 'default_product.png', 1),
('LUB-000038', '15W40 SEMI SINTETICO AKRON', 'Lubricante 15W40 SEMI SINTETICO. AKRON', 8.00, 'Lubricantes', 'AKRON', 'default_product.png', 1),
('LUB-000039', '15W40 SEMI SINTETICO BRAVA', 'Lubricante 15W40 SEMI SINTETICO. BRAVA', 7.00, 'Lubricantes', 'BRAVA', 'default_product.png', 1),
('LUB-000040', '15W40 SEMI SINTETICO FC', 'Lubricante 15W40 SEMI SINTETICO. FC FAUCI', 7.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1),
('LUB-000041', '15W40 TEC GDI GULF SEMI-SINTETICO AVANZADO 1L', 'Lubricante 15W40 SEMI SINTETICO. GULF', 11.00, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000042', '15W40 SEMI SINTETICO OILSTONE', 'Lubricante 15W40 SEMI SINTETICO. OILSTONE', 7.00, 'Lubricantes', 'OILSTONE', 'default_product.png', 1),
('LUB-000043', '15W40 SEMI SINTETICO DAUER', 'Lubricante 15W40 SEMI SINTETICO. DAUER', 8.00, 'Lubricantes', 'DAUER', 'default_product.png', 1),
('LUB-000044', '15W40 SEMI SINTETICO 3.78L VALVOLINE', 'Lubricante 15W40 SEMI SINTETICO. VALVOLINE', 29.00, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1),
('LUB-000045', '15W40 VALVOLINE PREMIUM PROTETION SEMI-SINTETICO', 'Lubricante 15W40 SEMI SINTETICO. VALVOLINE', 7.50, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1),
('LUB-000046', '15W40 SEMI SINTETICO INCA', 'Lubricante 15W40 SEMI SINTETICO. INCA', 9.00, 'Lubricantes', 'INCA', 'default_product.png', 1),
('LUB-000047', '15W40 SEMI SINTETICO VM LUB', 'Lubricante 15W40 SEMI SINTETICO. VM LUBRICANTES', 5.00, 'Lubricantes', 'VM LUBRICANTES', 'default_product.png', 1),
('LUB-000048', '15W40 EVOLUB SKY', 'Lubricante 15W40 SEMI SINTETICO. SKY', 8.00, 'Lubricantes', 'SKY', 'default_product.png', 1),
('LUB-000049', '20W50 PREMIUM BLEND VALVOLINE SEMI-SINTETICO 0.946L', 'Lubricante 20W50 SEMI SINTETICO. VALVOLINE', 7.50, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1),
('LUB-000050', '20W50 SEMI SINTETICO FC', 'Lubricante 20W50 SEMI SINTETICO. FC FAUCI', 7.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1),
('LUB-000051', '20W50 SEMI SINTETICO BRAVA', 'Lubricante 20W50 SEMI SINTETICO. BRAVA', 7.00, 'Lubricantes', 'BRAVA', 'default_product.png', 1),
('LUB-000052', '20W50 SEMI SINTETICO ARMAX', 'Lubricante 20W50 SEMI SINTETICO. ARMAX', 5.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1),
('LUB-000053', '20W50 SEMI SINTETICO VM LUB', 'Lubricante 20W50 SEMI SINTETICO. VM LUBRICANTES', 5.00, 'Lubricantes', 'VM LUBRICANTES', 'default_product.png', 1),
('LUB-000054', '20W50 SEMI SINTETICO BOSS', 'Lubricante 20W50 SEMI SINTETICO. BOSS', 5.00, 'Lubricantes', 'BOSS', 'default_product.png', 1),
('LUB-000055', '20W50 SEMI SINTETICO DAUER', 'Lubricante 20W50 SEMI SINTETICO. DAUER', 8.00, 'Lubricantes', 'DAUER', 'default_product.png', 1),
('LUB-000056', '20W50 SEMI SINTETICO FC GALON 3.78L', 'Lubricante 20W50 SEMI SINTETICO. FC FAUCI', 22.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1),
('LUB-000057', '20W50 MAX ULTRA GULF SEMI-SINTETICO', 'Lubricante 20W50 SEMI SINTETICO. GULF', 10.00, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000058', '20W50 SEMI SINTETICO INCA', 'Lubricante 20W50 SEMI SINTETICO. INCA', 9.00, 'Lubricantes', 'INCA', 'default_product.png', 1),
('LUB-000059', '20W50 EVOLUB SKY SENI SINTETICO', 'Lubricante 20W50 SEMI SINTETICO. SKY', 8.00, 'Lubricantes', 'SKY', 'default_product.png', 1),
('LUB-000060', 'OW20 GONHER NANOTEK GOLD 100% SINTETICO 946 ML', 'Lubricante 0W20 SINTETICO. GONHER', 7.00, 'Lubricantes', 'GONHER', 'default_product.png', 1),
('LUB-000061', '5W20 GONHER SINTETICO NANOTEK GOLD DE 946ML', 'Lubricante 5W20 SINTETICO. GONHER', 7.00, 'Lubricantes', 'GONHER', 'default_product.png', 1),
('LUB-000062', '5W20 GULF ULTRASYNTH GDI', 'Lubricante 5W20 SINTETICO. GULF', 8.00, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000063', '5W-20 SHELL HELIX HX7 SP SINTETICO 1L', 'Lubricante 5W20 SINTETICO. SHELL HELIX', 8.00, 'Lubricantes', 'SHELL HELIX', 'default_product.png', 1),
('LUB-000064', '5W30 GULF FORMULA CX FULL SINTETICO', 'Lubricante 5W30 SINTETICO. GULF', 8.00, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000065', '5W30 FULL SINTETICO VALVOLINE', 'Lubricante 5W30 SINTETICO. VALVOLINE', 10.00, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1),
('LUB-000066', '5W30 SINTETICO MOBIL', 'Lubricante 5W30 SINTETICO. MOBIL', 8.00, 'Lubricantes', 'MOBIL', 'default_product.png', 1),
('LUB-000067', '5W30 SINTETICO MOTORCRAFT', 'Lubricante 5W30 SINTETICO. MOTORCRAFT', 9.50, 'Lubricantes', 'MOTORCRAFT', 'default_product.png', 1),
('LUB-000068', '5W30 SINTETICO WOLF ECOTECH SP-RP G6', 'Lubricante 5W30 SINTETICO. WOLF', 11.00, 'Lubricantes', 'WOLF', 'default_product.png', 1),
('LUB-000069', '5W40 GULF FORMULA CX FULL SINTETICO', 'Lubricante 5W40 SINTETICO. GULF', 8.00, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000070', '20W50 MINERAL GULF PRIDE 4T PLUS', 'Lubricante 20W50 4T MINERAL. GULF', 9.50, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000071', '20W50 MINERAL 4T VM LUB', 'Lubricante 20W50 4T MINERAL. VM LUB', 4.50, 'Lubricantes', 'VM LUB', 'default_product.png', 1),
('LUB-000072', '20W50 4TCH VALVOLINE MINERAL', 'Lubricante 20W50 4T MINERAL. VALVOLINE', 7.00, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1),
('LUB-000073', '10W40 4T SINTETICO GULF POWER TRACK', 'Lubricante 10W40 4T SINTETICO. GULF', 15.00, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000074', '15W50 4T INCA', 'Lubricante 10W50 4T SINTETICO. INCA', 4.00, 'Lubricantes', 'INCA', 'default_product.png', 1),
('LUB-000075', 'ACEITE CK-4 10W30 RALOY GARRAFA 3.75L', 'Lubricante 10W30 DIESEL. RALOY', 26.00, 'Lubricantes', 'RALOY', 'default_product.png', 1),
('LUB-000076', 'ACEITE ATF DEXRON III BITOIL 1L', 'Lubricante DEXRON III. BITOIL', 4.00, 'Lubricantes', 'BITOIL', 'default_product.png', 1),
('LUB-000077', 'ACEITE SAE 15W40 BITOIL MINERAL', 'Lubricante DEXRON III. BITOIL', 3.98, 'Lubricantes', 'BITOIL', 'default_product.png', 1),
('LUB-000078', 'ATF DEXRON III BITOIL PAILA 19L', 'Lubricante DEXRON III. BITOIL', 51.00, 'Lubricantes', 'BITOIL', 'default_product.png', 1),
('LUB-000079', 'ACEITE HIDRAULICO ATF III DAUER', 'Lubricante DEXRON III. DAUER', 7.50, 'Lubricantes', 'DAUER', 'default_product.png', 1),
('LUB-000080', 'ATF DX III GULF CAJA DE ACEITE AUTOMATICO DE 1L', 'Lubricante DEXRON III. GULF', 8.00, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000081', 'ACEITE ATF-3 MEXLUB PARA TRANSMISIONES AUT', 'Lubricante DEXRON III. MEXLUB', 7.00, 'Lubricantes', 'MEXLUB', 'default_product.png', 1),
('LUB-000082', 'VALVULINA 80W90 BITOIL 1L', 'Lubricante 89W90. BITOIL', 4.00, 'Lubricantes', 'BITOIL', 'default_product.png', 1),
('LUB-000083', 'VALVULINA 85W140 BITOIL 1L', 'Lubricante 89W90. BITOIL', 3.98, 'Lubricantes', 'BITOIL', 'default_product.png', 1),
('LUB-000084', 'ACEITE FC 20W50 SEMI SINTETICO', 'Lubricante 89W90. FC FAUCI', 5.84, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1),
('LUB-000085', 'VALVULINA 80W90 GULF GEAR MP', 'Lubricante 89W90. GULF', 6.50, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000086', 'VALVULINA 85W140 GULF GEAR MP', 'Lubricante 89W90. GULF', 6.48, 'Lubricantes', 'GULF', 'default_product.png', 1),
('LUB-000087', 'ACEITE INCA 15W40 SEMI SINTETICO', 'Lubricante 89W90. INCA', 7.44, 'Lubricantes', 'INCA', 'default_product.png', 1),
('LUB-000088', 'SAE 80W90 TRANSMISION RALOY EXTREMA PRESION', 'Lubricante 89W90. RALOY', 5.00, 'Lubricantes', 'RALOY', 'default_product.png', 1),
('LUB-000089', 'ACEITE 25W50 MINERAL MEXLUB ALTO KILOMETRAJE', 'Lubricante 89W90. MEXLUB', 7.59, 'Lubricantes', 'MEXLUB', 'default_product.png', 1),
('LUB-000090', 'VALVULINA 80W90 GL-5 MEXLUB', 'Lubricante 89W90. MEXLUB', 7.96, 'Lubricantes', 'MEXLUB', 'default_product.png', 1),
('LUB-000091', 'VALVULINA 85W140 GL-5 MEXLUB', 'Lubricante 89W90. MEXLUB', 7.96, 'Lubricantes', 'MEXLUB', 'default_product.png', 1),
('LUB-000092', 'ACEITE OILSTONE 20W50 SEMI SINTETICO', 'Lubricante 89W90. OILSTONE', 6.78, 'Lubricantes', 'OILSTONE', 'default_product.png', 1),
('LUB-000093', 'SAE 85W140 VALVULINA RALOY EXTREMA PRESION 946ML', 'Lubricante 85W140. RALOY', 6.00, 'Lubricantes', 'RALOY', 'default_product.png', 1),
('LUB-000094', 'ACEITE ARMAX SAE50 PAILA 20L', 'Lubricante SAE50 DIESEL. ARMAX', 80.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1),
('LUB-000095', 'ACEITE SAE50 BITOIL PAILA 19L', 'Lubricante SAE50 DIESEL. BITOIL', 55.00, 'Lubricantes', 'BITOIL', 'default_product.png', 1),
('LUB-000096', 'ACEITE BOSS SAE50 PAILA 20 LITROS', 'Lubricante SAE50 DIESEL. BOSS', 65.00, 'Lubricantes', 'BOSS', 'default_product.png', 1),
('LUB-000097', 'ACEITE SAE50 FC PAILA 19L', 'Lubricante SAE50 DIESEL. FC FAUCI', 75.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1),
('LUB-000098', 'ACEITE DE MOTOR MOBIL DIESEL DELVAC MODERN 15W40', 'Lubricante 15W40 DIESEL. MOBIL', 8.50, 'Lubricantes', 'MOBIL', 'default_product.png', 1),
('LUB-000099', 'ACEITE ARMAX 15W40 MINERAL DIESEL PAILA 20L', 'Lubricante 15W40 DIESEL. ARMAX', 80.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1),
('LUB-000100', 'ACEITE 15W40 DIESEL MEXLUB 5L CL-4', 'Lubricante 15W40 DIESEL. MEXLUB', 33.00, 'Lubricantes', 'MEXLUB', 'default_product.png', 1),
('LUB-000101', 'ISO 68 HIDRALOY 300 ACEITE HIDRAULICO 68 RALOY PAILA 19L', 'Lubricante HIDRAULICO 68. RALOY', 71.00, 'Lubricantes', 'RALOY', 'default_product.png', 1),
('LUB-000102', 'SAE 15W40 SEMI SINTETICO TURBO RALOY API SN PLUS', 'Lubricante HIDRAULICO 68. RALOY', 7.31, 'Lubricantes', 'RALOY', 'default_product.png', 1),
('LUB-000103', 'TRANS-FLUID RDX-III RALOY P/TRANSMISION AUTOMATICA', 'Lubricante HIDRAULICO 68. RALOY', 5.65, 'Lubricantes', 'RALOY', 'default_product.png', 1),
('LUB-000104', 'SAE 20W50 RALOY TURBO SEMI-SINTETICO', 'Lubricante HIDRAULICO 68. RALOY', 7.50, 'Lubricantes', 'RALOY', 'default_product.png', 1),
('LUB-000105', 'SAE 20W50 RALOY RACING OIL MULTIGRADE', 'Lubricante HIDRAULICO 68. RALOY', 6.94, 'Lubricantes', 'RALOY', 'default_product.png', 1),
('LUB-000106', 'ACEITE SHELL HELIX HX8 PROFESIONAL SINTETICO', 'Lubricante HIDRAULICO 68. SHELL HELIX', 11.12, 'Lubricantes', 'SHELL HELIX', 'default_product.png', 1),
('LUB-000107', 'ACEITE ATF DEXRON 3 SHELL SPIRAX S3 MD3 1L', 'Lubricante HIDRAULICO 68. SHELL HELIX', 8.46, 'Lubricantes', 'SHELL HELIX', 'default_product.png', 1),
('LUB-000108', 'ACEITE VITALTECH 5W40 SINTETICO WOLF', 'Lubricante HIDRAULICO 68. WOLF', 11.00, 'Lubricantes', 'WOLF', 'default_product.png', 1),
('LUB-000109', 'VALVULINA SINTETICA 75W90 GL-5 VITAL TECH WOLF', 'Lubricante HIDRAULICO 68. WOLF', 15.00, 'Lubricantes', 'WOLF', 'default_product.png', 1),
('BAT-000016', '600 AMP EXTREME 36DLM700 (36MR)', 'Bateria 600 AMP. EXTREME 36DLM700 (36MR)', 50.00, 'Baterias', 'EXTREME 36DLM700 (36MR)', 'default_product.png', 1),
('BAT-000017', '650 AMP MOURA ME310FD (36MR)', 'Bateria 650 AMP. MOURA ME310FD (36MR)', 70.00, 'Baterias', 'MOURA ME310FD (36MR)', 'default_product.png', 1),
('BAT-000018', '650 AMP DURACELL 99-650 (36MR)', 'Bateria 650 AMP. DURACELL 99-650 (36MR)', 65.00, 'Baterias', 'DURACELL 99-650 (36MR)', 'default_product.png', 1),
('BAT-000019', '700 AMP ARO 99R-700', 'Bateria 700 AMP. ARO 99R-700', 62.00, 'Baterias', 'ARO 99R-700', 'default_product.png', 1),
('BAT-000020', '650 AMP MOURA ME805D (36MR)', 'Bateria 650 AMP. MOURA ME805D (36MR)', 85.00, 'Baterias', 'MOURA ME805D (36MR)', 'default_product.png', 1),
('BAT-000023', '800 AMP MOURA ME570GI (22M)', 'Bateria 800 AMP. MOURA ME570GI (22M)', 92.00, 'Baterias', 'MOURA ME570GI (22M)', 'default_product.png', 1),
('BAT-000024', '850 AMP EXTREME 24BI-720 (42M)', 'Bateria 850 AMP. EXTREME 24BI-720 (42M)', 65.00, 'Baterias', 'EXTREME 24BI-720 (42M)', 'default_product.png', 1),
('BAT-000025', '850 AMP EXTREME 24BD-720 (42MR)', 'Bateria 850 AMP. EXTREME 24BD-720 (42MR)', 65.00, 'Baterias', 'EXTREME 24BD-720 (42MR)', 'default_product.png', 1),
('BAT-000033', '900 AMP DURACELL 42-900 (42MR)', 'Bateria 900 AMP. DURACELL 42-900 (42MR)', 81.00, 'Baterias', 'DURACELL 42-900 (42MR)', 'default_product.png', 1),
('BAT-000034', '900 AMP DURACELL 42R-900 (42M)', 'Bateria 900 AMP. DURACELL 42R-900 (42M)', 81.00, 'Baterias', 'DURACELL 42R-900 (42M)', 'default_product.png', 1),
('BAT-000035', '900 AMP ARO 42-900 (42MR)', 'Bateria 900 AMP. ARO 42-900 (42MR)', 80.00, 'Baterias', 'ARO 42-900 (42MR)', 'default_product.png', 1),
('BAT-000036', '900 AMP ARO 42R-900 (42M)', 'Bateria 900 AMP. ARO 42R-900 (42M)', 80.00, 'Baterias', 'ARO 42R-900 (42M)', 'default_product.png', 1),
('BAT-000039', '1000 AMP MOURA ME650RD (24MR)', 'Bateria 1000 AMP. MOURA ME650RD (24MR)', 122.00, 'Baterias', 'MOURA ME650RD (24MR)', 'default_product.png', 1),
('BAT-000040', '1100 AMP ARO 315-1100 (TORNILLO)', 'Bateria 1100 AMP. ARO 315-1100 (TORNILLO)', 112.00, 'Baterias', 'ARO 315-1100 (TORNILLO)', 'default_product.png', 1),
('BAT-000041', '1000 AMP DURACELL 24-1000 (24MR)', 'Bateria 1000 AMP. DURACELL 24-1000 (24MR)', 89.00, 'Baterias', 'DURACELL 24-1000 (24MR)', 'default_product.png', 1),
('BAT-000042', '1000 AMP DURACELL 24F-1000 (24M)', 'Bateria 1000 AMP. DURACELL 24F-1000 (24M)', 89.00, 'Baterias', 'DURACELL 24F-1000 (24M)', 'default_product.png', 1),
('BAT-000043', '1000 AMP EXTREMA 24AD1000-A (24MR)', 'Bateria 1000 AMP. EXTREMA 24AD1000-A (24MR)', 85.00, 'Baterias', 'EXTREMA 24AD1000-A (24MR)', 'default_product.png', 1),
('BAT-000044', '1100 AMP ARO 24R - 1100', 'Bateria 1100 AMP. ARO 24R - 1100', 92.00, 'Baterias', 'ARO 24R - 1100', 'default_product.png', 1),
('BAT-000045', '1100 AMP ARO 24 - 1100', 'Bateria 1100 AMP. ARO 24 - 1100', 92.00, 'Baterias', 'ARO 24 - 1100', 'default_product.png', 1),
('BAT-000046', '1100 AMP DURACELL 34 - 1100', 'Bateria 1100 AMP. DURACELL 34 - 1100', 94.00, 'Baterias', 'DURACELL 34 - 1100', 'default_product.png', 1),
('BAT-000047', '1100 AMP DURACEL 34R - 1100', 'Bateria 1100 AMP. DURACEL 34R - 1100', 94.00, 'Baterias', 'DURACEL 34R - 1100', 'default_product.png', 1),
('BAT-000048', '1300 AMP DURACELL 31 - 1300S (TORNILLO)', 'Bateria 1300 AMP. DURACELL 31 - 1300S (TORNILLO)', 120.00, 'Baterias', 'DURACELL 31 - 1300S (TORNILLO)', 'default_product.png', 1),
('CMB-000004', 'ACEITE 20W50 MINERAL GULF', 'Combo de producto y servicio. GULF', 9.60, 'Combos', 'ACEITE 20W50 MINERAL GULF', 'default_product.png', 1),
('CMB-000005', 'ACEITE 20W50 SEMI SINTETICO GULF', 'Combo de producto y servicio. GULF', 11.95, 'Combos', 'ACEITE 20W50 SEMI SINTETICO GULF', 'default_product.png', 1),
('CMB-000006', 'ACEITE 15W40 MINERAL GULF', 'Combo de producto y servicio. GULF', 9.60, 'Combos', 'ACEITE 15W40 MINERAL GULF', 'default_product.png', 1),
('CMB-000007', 'ACEITE 15W40 SEMI SINTETICO GULF', 'Combo de producto y servicio. GULF', 11.95, 'Combos', 'ACEITE 15W40 SEMI SINTETICO GULF', 'default_product.png', 1),
('CMB-000008', 'ACEITE 10W30 SEMI SINTETICO GULF', 'Combo de producto y servicio. GULF', 12.05, 'Combos', 'ACEITE 10W30 SEMI SINTETICO GULF', 'default_product.png', 1),
('CMB-000009', 'ACEITE 5W20 SINTETICO GULF', 'Combo de producto y servicio. GULF', 13.22, 'Combos', 'ACEITE 5W20 SINTETICO GULF', 'default_product.png', 1),
('CMB-000010', 'ACEITE 5W30 SINTETICO GULF', 'Combo de producto y servicio. GULF', 13.22, 'Combos', 'ACEITE 5W30 SINTETICO GULF', 'default_product.png', 1),
('CMB-000011', 'ACEITE 5W40 SINTETICO GUL', 'Combo de producto y servicio. GULF', 13.22, 'Combos', 'ACEITE 5W40 SINTETICO GUL', 'default_product.png', 1),
('CMB-000016', 'ACEITE 20W50 MINERAL RALOY', 'Combo de producto y servicio. RALOY / INCA / BOSS', 7.69, 'Combos', 'ACEITE 20W50 MINERAL RALOY', 'default_product.png', 1),
('CMB-000017', 'ACEITE 20W50 MINERAL INCA', 'Combo de producto y servicio. RALOY / INCA / BOSS', 7.55, 'Combos', 'ACEITE 20W50 MINERAL INCA', 'default_product.png', 1),
('CMB-000018', 'ACEITE 20W50 SEMI SINTETICO RALOY', 'Combo de producto y servicio. RALOY / INCA / BOSS', 8.30, 'Combos', 'ACEITE 20W50 SEMI SINTETICO RALOY', 'default_product.png', 1),
('CMB-000019', 'ACEITE 20W50 SEMI SINTETICO INCA', 'Combo de producto y servicio. RALOY / INCA / BOSS', 8.11, 'Combos', 'ACEITE 20W50 SEMI SINTETICO INCA', 'default_product.png', 1),
('CMB-000020', 'ACEITE 15W40 MINERAL RALOY', 'Combo de producto y servicio. RALOY / INCA / BOSS', 7.69, 'Combos', 'ACEITE 15W40 MINERAL RALOY', 'default_product.png', 1),
('CMB-000021', 'ACEITE 15W40 MINERAL INCA', 'Combo de producto y servicio. RALOY / INCA / BOSS', 7.52, 'Combos', 'ACEITE 15W40 MINERAL INCA', 'default_product.png', 1),
('CMB-000022', 'ACEITE 15W40 SEMI SINTETICO RALOY', 'Combo de producto y servicio. RALOY / INCA / BOSS', 8.30, 'Combos', 'ACEITE 15W40 SEMI SINTETICO RALOY', 'default_product.png', 1),
('CMB-000023', 'ACEITE 15W40 SEMI SINTETICO INCA', 'Combo de producto y servicio. RALOY / INCA / BOSS', 8.04, 'Combos', 'ACEITE 15W40 SEMI SINTETICO INCA', 'default_product.png', 1),
('CMB-000024', 'ACEITE 20W50 MINERAL BOSS', 'Combo de producto y servicio. RALOY / INCA / BOSS', 5.15, 'Combos', 'ACEITE 20W50 MINERAL BOSS', 'default_product.png', 1),
('CMB-000025', 'ACEITE 15W40 SEMI SINTETICO BOSS', 'Combo de producto y servicio. RALOY / INCA / BOSS', 5.34, 'Combos', 'ACEITE 15W40 SEMI SINTETICO BOSS', 'default_product.png', 1),
('CMB-000030', 'ACEITE 20W50 MINERAL VALVOLINE', 'Combo de producto y servicio. VALVOLINE / FC', 8.20, 'Combos', 'ACEITE 20W50 MINERAL VALVOLINE', 'default_product.png', 1),
('CMB-000031', 'ACEITE 20W50 MINERAL FC', 'Combo de producto y servicio. VALVOLINE / FC', 5.66, 'Combos', 'ACEITE 20W50 MINERAL FC', 'default_product.png', 1),
('CMB-000032', 'ACEITE 20W50 MINERAL MOBIL', 'Combo de producto y servicio. VALVOLINE / FC', 6.38, 'Combos', 'ACEITE 20W50 MINERAL MOBIL', 'default_product.png', 1),
('CMB-000033', 'ACEITE 20W50 SEMI SINTETICO VALVOLINE', 'Combo de producto y servicio. VALVOLINE / FC', 8.34, 'Combos', 'ACEITE 20W50 SEMI SINTETICO VALVOLINE', 'default_product.png', 1),
('CMB-000034', 'ACEITE 20W50 SEMI SINTETICO FC', 'Combo de producto y servicio. VALVOLINE / FC', 8.34, 'Combos', 'ACEITE 20W50 SEMI SINTETICO FC', 'default_product.png', 1),
('CMB-000035', 'ACEITE 10W40 SEMI SINTETICO MOBIL', 'Combo de producto y servicio. VALVOLINE / FC', 7.93, 'Combos', 'ACEITE 10W40 SEMI SINTETICO MOBIL', 'default_product.png', 1),
('CMB-000036', 'ACEITE 15W40 MINERAL VALVOLINE', 'Combo de producto y servicio. VALVOLINE / FC', 8.20, 'Combos', 'ACEITE 15W40 MINERAL VALVOLINE', 'default_product.png', 1),
('CMB-000037', 'ACEITE 15W40 MINERAL FC', 'Combo de producto y servicio. VALVOLINE / FC', 5.66, 'Combos', 'ACEITE 15W40 MINERAL FC', 'default_product.png', 1),
('CMB-000038', 'ACEITE 15W40 SEMI SINTETICO VALVOLINE', 'Combo de producto y servicio. VALVOLINE / FC', 8.34, 'Combos', 'ACEITE 15W40 SEMI SINTETICO VALVOLINE', 'default_product.png', 1),
('CMB-000039', '15W40 SEMI SINTETICO VALVOLINE GARRAFA', 'Combo de producto y servicio. VALVOLINE / FC', 29.90, 'Combos', '15W40 SEMI SINTETICO VALVOLINE GARRAFA', 'default_product.png', 1),
('CMB-000040', 'ACEITE 15W40 SEMI SINTETICO FC', 'Combo de producto y servicio. VALVOLINE / FC', 6.45, 'Combos', 'ACEITE 15W40 SEMI SINTETICO FC', 'default_product.png', 1),
('CMB-000041', '15W40 / 20W50 SEMI SINTETICO FC GARRAFA', 'Combo de producto y servicio. VALVOLINE / FC', 23.23, 'Combos', '15W40 / 20W50 SEMI SINTETICO FC GARRAFA', 'default_product.png', 1),
('CMB-000046', 'ACEITE 20W50 MINERAL ROSHFRANS', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 8.22, 'Combos', 'ACEITE 20W50 MINERAL ROSHFRANS', 'default_product.png', 1),
('CMB-000047', 'ACEITE 20W50 MINERAL MEXLUB', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 8.92, 'Combos', 'ACEITE 20W50 MINERAL MEXLUB', 'default_product.png', 1),
('CMB-000048', 'ACEITE 20W50 SEMI SINTETICO MEXLUB', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 8.67, 'Combos', 'ACEITE 20W50 SEMI SINTETICO MEXLUB', 'default_product.png', 1),
('CMB-000049', 'ACEITE 15W40 MINERAL ROSHFRANS', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 8.22, 'Combos', 'ACEITE 15W40 MINERAL ROSHFRANS', 'default_product.png', 1),
('CMB-000050', 'ACEITE 15W40 MINERAL MEXLUB', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 9.16, 'Combos', 'ACEITE 15W40 MINERAL MEXLUB', 'default_product.png', 1),
('CMB-000051', 'ACEITE 15W40 SEMI SINTETICO MEXLUB', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 9.06, 'Combos', 'ACEITE 15W40 SEMI SINTETICO MEXLUB', 'default_product.png', 1),
('CMB-000052', 'ACEITE 15W40 SEMI SINTETICO WOLF', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 8.22, 'Combos', 'ACEITE 15W40 SEMI SINTETICO WOLF', 'default_product.png', 1),
('CMB-000053', 'ACEITE 20W50 MINERAL MOTUL', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 10.62, 'Combos', 'ACEITE 20W50 MINERAL MOTUL', 'default_product.png', 1)
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre), descripcion = VALUES(descripcion), precio = VALUES(precio), categoria = VALUES(categoria), marca = VALUES(marca), imagen = VALUES(imagen), estado = VALUES(estado);

DELETE FROM stock;

INSERT INTO stock (producto_codigo, sucursal_id, stock, stock_minimo, ubicacion) VALUES
('NEU-000013', 1, 7, 2, 'RIN 13 PCR'),
('NEU-000014', 1, 5, 2, 'RIN 13 PCR'),
('NEU-000015', 1, 17, 2, 'RIN 13 PCR'),
('NEU-000016', 1, 8, 2, 'RIN 13 PCR'),
('NEU-000017', 1, 0, 2, 'RIN 13 PCR'),
('NEU-000018', 1, 13, 2, 'RIN 13 PCR'),
('NEU-000019', 1, 8, 2, 'RIN 13 PCR'),
('NEU-000020', 1, 7, 2, 'RIN 13 PCR'),
('NEU-000021', 1, 0, 2, 'RIN 13 PCR'),
('NEU-000022', 1, 19, 2, 'RIN 13 PCR'),
('NEU-000023', 1, 0, 2, 'RIN 13 PCR'),
('NEU-000024', 1, 0, 2, 'RIN 13 PCR'),
('NEU-000025', 1, 2, 2, 'RIN 13 PCR'),
('NEU-000026', 1, 0, 2, 'RIN 13 PCR'),
('NEU-000028', 1, 0, 2, 'RIN 14 PCR'),
('NEU-000029', 1, 0, 2, 'RIN 14 PCR'),
('NEU-000030', 1, 0, 2, 'RIN 14 PCR'),
('NEU-000031', 1, 137, 2, 'RIN 14 PCR'),
('NEU-000032', 1, 21, 2, 'RIN 14 PCR'),
('NEU-000033', 1, 172, 2, 'RIN 14 PCR'),
('NEU-000034', 1, 5, 2, 'RIN 14 PCR'),
('NEU-000035', 1, 20, 2, 'RIN 14 PCR'),
('NEU-000036', 1, 0, 2, 'RIN 14 PCR'),
('NEU-000037', 1, 8, 2, 'RIN 14 PCR'),
('NEU-000038', 1, 16, 2, 'RIN 14 PCR'),
('NEU-000039', 1, 0, 2, 'RIN 14 PCR'),
('NEU-000040', 1, 0, 2, 'RIN 14 PCR'),
('NEU-000041', 1, 0, 2, 'RIN 14 PCR'),
('NEU-000042', 1, 20, 2, 'RIN 14 PCR'),
('NEU-000043', 1, 18, 2, 'RIN 14 PCR'),
('NEU-000044', 1, 3, 2, 'RIN 14 PCR'),
('NEU-000046', 1, 0, 2, 'RIN 15 PCR'),
('NEU-000047', 1, 13, 2, 'RIN 15 PCR'),
('NEU-000048', 1, 19, 2, 'RIN 15 PCR'),
('NEU-000049', 1, 10, 2, 'RIN 15 PCR'),
('NEU-000050', 1, 7, 2, 'RIN 15 PCR'),
('NEU-000051', 1, 4, 2, 'RIN 15 PCR'),
('NEU-000052', 1, 19, 2, 'RIN 15 PCR'),
('NEU-000053', 1, 4, 2, 'RIN 15 PCR'),
('NEU-000054', 1, 32, 2, 'RIN 15 PCR'),
('NEU-000055', 1, 2, 2, 'RIN 15 PCR'),
('NEU-000056', 1, 2, 2, 'RIN 15 PCR'),
('NEU-000057', 1, 30, 2, 'RIN 15 PCR'),
('NEU-000058', 1, 6, 2, 'RIN 15 PCR'),
('NEU-000059', 1, 0, 2, 'RIN 15 PCR'),
('NEU-000060', 1, 0, 2, 'RIN 15 PCR'),
('NEU-000061', 1, 2, 2, 'RIN 15 PCR'),
('NEU-000062', 1, 14, 2, 'RIN 15 PCR'),
('NEU-000063', 1, 2, 2, 'RIN 15 PCR'),
('NEU-000064', 1, 10, 2, 'RIN 15 PCR'),
('NEU-000065', 1, 2, 2, 'RIN 15 PCR'),
('NEU-000067', 1, 4, 2, 'RIN 15 PCR'),
('NEU-000068', 1, 0, 2, 'RIN 15 PCR'),
('NEU-000069', 1, 40, 2, 'RIN 15 PCR'),
('NEU-000070', 1, 40, 2, 'RIN 15 PCR'),
('NEU-000071', 1, 4, 2, 'RIN 15 PCR'),
('NEU-000072', 1, 0, 2, 'RIN 15 PCR'),
('NEU-000073', 1, 0, 2, 'RIN 15 PCR'),
('NEU-000074', 1, 0, 2, 'RIN 15 PCR'),
('NEU-000075', 1, 4, 2, 'RIN 15 PCR'),
('NEU-000076', 1, 2, 2, 'RIN 15 PCR'),
('NEU-000077', 1, 12, 2, 'RIN 15 PCR'),
('NEU-000078', 1, 0, 2, 'RIN 15 PCR'),
('NEU-000079', 1, 2, 2, 'RIN 15 PCR'),
('NEU-000081', 1, 2, 2, 'RIN 15 PCR'),
('NEU-000082', 1, 4, 2, 'RIN 15 PCR'),
('NEU-000083', 1, 18, 2, 'RIN 15 PCR'),
('NEU-000084', 1, 8, 2, 'RIN 15 PCR'),
('NEU-000085', 1, 4, 2, 'RIN 15 PCR'),
('NEU-000086', 1, 4, 2, 'RIN 15 PCR'),
('NEU-000087', 1, 0, 2, 'RIN 15 PCR'),
('NEU-000088', 1, 2, 2, 'RIN 15 PCR'),
('NEU-000089', 1, 0, 2, 'RIN 15 PCR'),
('NEU-000091', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000092', 1, 8, 2, 'RIN 16 PCR'),
('NEU-000093', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000094', 1, 8, 2, 'RIN 16 PCR'),
('NEU-000095', 1, 17, 2, 'RIN 16 PCR'),
('NEU-000096', 1, 165, 2, 'RIN 16 PCR'),
('NEU-000097', 1, 1, 2, 'RIN 16 PCR'),
('NEU-000098', 1, 6, 2, 'RIN 16 PCR'),
('NEU-000099', 1, 4, 2, 'RIN 16 PCR'),
('NEU-000100', 1, 4, 2, 'RIN 16 PCR'),
('NEU-000101', 1, 50, 2, 'RIN 16 PCR'),
('NEU-000102', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000103', 1, 4, 2, 'RIN 16 PCR'),
('NEU-000104', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000105', 1, 12, 2, 'RIN 16 PCR'),
('NEU-000106', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000107', 1, 4, 2, 'RIN 16 PCR'),
('NEU-000108', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000109', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000110', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000112', 1, 8, 2, 'RIN 16 PCR'),
('NEU-000114', 1, 2, 2, 'RIN 16 PCR'),
('NEU-000115', 1, 4, 2, 'RIN 16 PCR'),
('NEU-000116', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000117', 1, 4, 2, 'RIN 16 PCR'),
('NEU-000118', 1, 4, 2, 'RIN 16 PCR'),
('NEU-000119', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000120', 1, 2, 2, 'RIN 16 PCR'),
('NEU-000121', 1, 4, 2, 'RIN 16 PCR'),
('NEU-000123', 1, 8, 2, 'RIN 16 PCR'),
('NEU-000124', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000126', 1, 6, 2, 'RIN 16 PCR'),
('NEU-000127', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000128', 1, 0, 2, 'RIN 16 PCR'),
('NEU-000129', 1, 4, 2, 'RIN 16 PCR'),
('NEU-000131', 1, 0, 2, 'RIN 16 TBR'),
('NEU-000132', 1, 4, 2, 'RIN 16 TBR'),
('NEU-000133', 1, 0, 2, 'RIN 16 TBR'),
('NEU-000134', 1, 1, 2, 'RIN 16 TBR'),
('NEU-000135', 1, 24, 2, 'RIN 16 TBR'),
('NEU-000136', 1, 40, 2, 'RIN 16 TBR'),
('NEU-000137', 1, 11, 2, 'RIN 16 TBR'),
('NEU-000139', 1, 6, 2, 'RIN 17 PCR'),
('NEU-000140', 1, 0, 2, 'RIN 17 PCR'),
('NEU-000141', 1, 2, 2, 'RIN 17 PCR'),
('NEU-000145', 1, 0, 2, 'RIN 17 PCR'),
('NEU-000146', 1, 6, 2, 'RIN 17 PCR'),
('NEU-000147', 1, 3, 2, 'RIN 17 PCR'),
('NEU-000150', 1, 2, 2, 'RIN 17 PCR'),
('NEU-000151', 1, 8, 2, 'RIN 17 PCR'),
('NEU-000152', 1, 0, 2, 'RIN 17 PCR'),
('NEU-000153', 1, 2, 2, 'RIN 17 PCR'),
('NEU-000154', 1, 4, 2, 'RIN 17 PCR'),
('NEU-000155', 1, 4, 2, 'RIN 17 PCR'),
('NEU-000157', 1, 0, 2, 'RIN 17 PCR'),
('NEU-000158', 1, 0, 2, 'RIN 17 PCR'),
('NEU-000159', 1, 0, 2, 'RIN 17 PCR'),
('NEU-000160', 1, 0, 2, 'RIN 17 PCR'),
('NEU-000161', 1, 4, 2, 'RIN 17 PCR'),
('NEU-000162', 1, 4, 2, 'RIN 17 PCR'),
('NEU-000165', 1, 0, 2, 'RIN 17.5 TBR'),
('NEU-000166', 1, 0, 2, 'RIN 17.5 TBR'),
('NEU-000167', 1, 2, 2, 'RIN 17.5 TBR'),
('NEU-000169', 1, 0, 2, 'RIN 18 PCR'),
('NEU-000170', 1, 0, 2, 'RIN 18 PCR'),
('NEU-000171', 1, 0, 2, 'RIN 18 PCR'),
('NEU-000172', 1, 0, 2, 'RIN 18 PCR'),
('NEU-000174', 1, 8, 2, 'RIN 18 PCR'),
('NEU-000175', 1, 2, 2, 'RIN 18 PCR'),
('NEU-000176', 1, 0, 2, 'RIN 18 PCR'),
('NEU-000178', 1, 2, 2, 'RIN 20 PCR'),
('NEU-000179', 1, 0, 2, 'RIN 20 PCR'),
('NEU-000181', 1, 0, 2, 'RIN 20 PCR'),
('NEU-000182', 1, 200, 2, 'RIN 20 PCR'),
('NEU-000184', 1, 1, 2, 'RIN 22.5 TBR'),
('NEU-000185', 1, 0, 2, 'RIN 22.5 TBR'),
('NEU-000186', 1, 0, 2, 'RIN 22.5 TBR'),
('NEU-000187', 1, 0, 2, 'RIN 22.5 TBR'),
('NEU-000188', 1, 0, 2, 'RIN 22.5 TBR'),
('NEU-000190', 1, 0, 2, 'RIN 22.5 TBR'),
('NEU-000191', 1, 1, 2, 'RIN 22.5 TBR'),
('NEU-000192', 1, 0, 2, 'RIN 22.5 TBR'),
('NEU-000193', 1, 0, 2, 'RIN 22.5 TBR'),
('NEU-000194', 1, 0, 2, 'RIN 22.5 TBR'),
('LUB-000005', 1, 25, 2, '15W40 MINERAL'),
('LUB-000006', 1, 0, 2, '15W40 MINERAL'),
('LUB-000007', 1, 3, 2, '15W40 MINERAL'),
('LUB-000008', 1, 0, 2, '15W40 MINERAL'),
('LUB-000009', 1, 17, 2, '15W40 MINERAL'),
('LUB-000010', 1, 12, 2, '15W40 MINERAL'),
('LUB-000011', 1, 4, 2, '15W40 MINERAL'),
('LUB-000012', 1, 39, 2, '15W40 MINERAL'),
('LUB-000013', 1, 0, 2, '20W50 MINERAL'),
('LUB-000014', 1, 0, 2, '20W50 MINERAL'),
('LUB-000015', 1, 0, 2, '20W50 MINERAL'),
('LUB-000016', 1, 11, 2, '20W50 MINERAL'),
('LUB-000017', 1, 0, 2, '20W50 MINERAL'),
('LUB-000018', 1, 0, 2, '20W50 MINERAL'),
('LUB-000019', 1, 2, 2, '20W50 MINERAL'),
('LUB-000020', 1, 11, 2, '20W50 MINERAL'),
('LUB-000021', 1, 14, 2, '20W50 MINERAL'),
('LUB-000022', 1, 11, 2, '20W50 MINERAL'),
('LUB-000023', 1, 12, 2, '20W50 MINERAL'),
('LUB-000024', 1, 3, 2, '20W50 MINERAL'),
('LUB-000025', 1, 3, 2, '20W50 MINERAL'),
('LUB-000026', 1, 2, 2, '20W50 MINERAL'),
('LUB-000027', 1, 0, 2, '20W50 MINERAL'),
('LUB-000028', 1, 7, 2, '25W60 MINERAL'),
('LUB-000029', 1, 4, 2, '10W30 SEMI SINTETICO'),
('LUB-000030', 1, 0, 2, '10W30 SEMI SINTETICO'),
('LUB-000031', 1, 12, 2, '10W30 SEMI SINTETICO'),
('LUB-000032', 1, 16, 2, '10W30 SEMI SINTETICO'),
('LUB-000033', 1, 26, 2, '10W40 SEMI SINTETICO'),
('LUB-000034', 1, 0, 2, '15W40 SEMI SINTETICO'),
('LUB-000035', 1, 0, 2, '15W40 SEMI SINTETICO'),
('LUB-000036', 1, 0, 2, '15W40 SEMI SINTETICO'),
('LUB-000037', 1, 12, 2, '15W40 SEMI SINTETICO'),
('LUB-000038', 1, 1, 2, '15W40 SEMI SINTETICO'),
('LUB-000039', 1, 37, 2, '15W40 SEMI SINTETICO'),
('LUB-000040', 1, 9, 2, '15W40 SEMI SINTETICO'),
('LUB-000041', 1, 11, 2, '15W40 SEMI SINTETICO'),
('LUB-000042', 1, 7, 2, '15W40 SEMI SINTETICO'),
('LUB-000043', 1, 4, 2, '15W40 SEMI SINTETICO'),
('LUB-000044', 1, 0, 2, '15W40 SEMI SINTETICO'),
('LUB-000045', 1, 202, 2, '15W40 SEMI SINTETICO'),
('LUB-000046', 1, 0, 2, '15W40 SEMI SINTETICO'),
('LUB-000047', 1, 0, 2, '15W40 SEMI SINTETICO'),
('LUB-000048', 1, 0, 2, '15W40 SEMI SINTETICO'),
('LUB-000049', 1, 37, 2, '20W50 SEMI SINTETICO'),
('LUB-000050', 1, 21, 2, '20W50 SEMI SINTETICO'),
('LUB-000051', 1, 14, 2, '20W50 SEMI SINTETICO'),
('LUB-000052', 1, 0, 2, '20W50 SEMI SINTETICO'),
('LUB-000053', 1, 0, 2, '20W50 SEMI SINTETICO'),
('LUB-000054', 1, 1, 2, '20W50 SEMI SINTETICO'),
('LUB-000055', 1, 23, 2, '20W50 SEMI SINTETICO'),
('LUB-000056', 1, 0, 2, '20W50 SEMI SINTETICO'),
('LUB-000057', 1, 10, 2, '20W50 SEMI SINTETICO'),
('LUB-000058', 1, 20, 2, '20W50 SEMI SINTETICO'),
('LUB-000059', 1, 2, 2, '20W50 SEMI SINTETICO'),
('LUB-000060', 1, 12, 2, '0W20 SINTETICO'),
('LUB-000061', 1, 4, 2, '5W20 SINTETICO'),
('LUB-000062', 1, 18, 2, '5W20 SINTETICO'),
('LUB-000063', 1, 1, 2, '5W20 SINTETICO'),
('LUB-000064', 1, 9, 2, '5W30 SINTETICO'),
('LUB-000065', 1, 2, 2, '5W30 SINTETICO'),
('LUB-000066', 1, 6, 2, '5W30 SINTETICO'),
('LUB-000067', 1, 8, 2, '5W30 SINTETICO'),
('LUB-000068', 1, 1, 2, '5W30 SINTETICO'),
('LUB-000069', 1, 9, 2, '5W40 SINTETICO'),
('LUB-000070', 1, 5, 2, '20W50 4T MINERAL'),
('LUB-000071', 1, 23, 2, '20W50 4T MINERAL'),
('LUB-000072', 1, 1, 2, '20W50 4T MINERAL'),
('LUB-000073', 1, 2, 2, '10W40 4T SINTETICO'),
('LUB-000074', 1, 0, 2, '10W50 4T SINTETICO'),
('LUB-000075', 1, 4, 2, '10W30 DIESEL'),
('LUB-000076', 1, 4, 2, 'DEXRON III'),
('LUB-000077', 1, 0, 2, 'DEXRON III'),
('LUB-000078', 1, 3, 2, 'DEXRON III'),
('LUB-000079', 1, 6, 2, 'DEXRON III'),
('LUB-000080', 1, 0, 2, 'DEXRON III'),
('LUB-000081', 1, 1, 2, 'DEXRON III'),
('LUB-000082', 1, 0, 2, '89W90'),
('LUB-000083', 1, 0, 2, '89W90'),
('LUB-000084', 1, 0, 2, '89W90'),
('LUB-000085', 1, 10, 2, '89W90'),
('LUB-000086', 1, 0, 2, '89W90'),
('LUB-000087', 1, 0, 2, '89W90'),
('LUB-000088', 1, 3, 2, '89W90'),
('LUB-000089', 1, 0, 2, '89W90'),
('LUB-000090', 1, 0, 2, '89W90'),
('LUB-000091', 1, 0, 2, '89W90'),
('LUB-000092', 1, 0, 2, '89W90'),
('LUB-000093', 1, 0, 2, '85W140'),
('LUB-000094', 1, 0, 2, 'SAE50 DIESEL'),
('LUB-000095', 1, 0, 2, 'SAE50 DIESEL'),
('LUB-000096', 1, 0, 2, 'SAE50 DIESEL'),
('LUB-000097', 1, 0, 2, 'SAE50 DIESEL'),
('LUB-000098', 1, 12, 2, '15W40 DIESEL'),
('LUB-000099', 1, 0, 2, '15W40 DIESEL'),
('LUB-000100', 1, 0, 2, '15W40 DIESEL'),
('LUB-000101', 1, 2, 2, 'HIDRAULICO 68'),
('LUB-000102', 1, 0, 2, 'HIDRAULICO 68'),
('LUB-000103', 1, 0, 2, 'HIDRAULICO 68'),
('LUB-000104', 1, 0, 2, 'HIDRAULICO 68'),
('LUB-000105', 1, 0, 2, 'HIDRAULICO 68'),
('LUB-000106', 1, 0, 2, 'HIDRAULICO 68'),
('LUB-000107', 1, 0, 2, 'HIDRAULICO 68'),
('LUB-000108', 1, 0, 2, 'HIDRAULICO 68'),
('LUB-000109', 1, 0, 2, 'HIDRAULICO 68'),
('BAT-000016', 1, 11, 2, '650 - 700'),
('BAT-000017', 1, 1, 2, '650 - 700'),
('BAT-000018', 1, 1, 2, '650 - 700'),
('BAT-000019', 1, 1, 2, '650 - 700'),
('BAT-000020', 1, 1, 2, '650 - 700'),
('BAT-000023', 1, 1, 2, '800'),
('BAT-000024', 1, 5, 2, '800'),
('BAT-000025', 1, 6, 2, '800'),
('BAT-000033', 1, 0, 2, '900'),
('BAT-000034', 1, 1, 2, '900'),
('BAT-000035', 1, 1, 2, '900'),
('BAT-000036', 1, 0, 2, '900'),
('BAT-000039', 1, 2, 2, '1000 - 1350'),
('BAT-000040', 1, 0, 2, '1000 - 1350'),
('BAT-000041', 1, 0, 2, '1000 - 1350'),
('BAT-000042', 1, 0, 2, '1000 - 1350'),
('BAT-000043', 1, 1, 2, '1000 - 1350'),
('BAT-000044', 1, 1, 2, '1000 - 1350'),
('BAT-000045', 1, 1, 2, '1000 - 1350'),
('BAT-000046', 1, 1, 2, '1000 - 1350'),
('BAT-000047', 1, 1, 2, '1000 - 1350'),
('BAT-000048', 1, 2, 2, '1000 - 1350'),
('CMB-000004', 1, 0, 2, 'GULF'),
('CMB-000005', 1, 0, 2, 'GULF'),
('CMB-000006', 1, 0, 2, 'GULF'),
('CMB-000007', 1, 0, 2, 'GULF'),
('CMB-000008', 1, 0, 2, 'GULF'),
('CMB-000009', 1, 0, 2, 'GULF'),
('CMB-000010', 1, 0, 2, 'GULF'),
('CMB-000011', 1, 0, 2, 'GULF'),
('CMB-000016', 1, 0, 2, 'RALOY / INCA / BOSS'),
('CMB-000017', 1, 0, 2, 'RALOY / INCA / BOSS'),
('CMB-000018', 1, 0, 2, 'RALOY / INCA / BOSS'),
('CMB-000019', 1, 0, 2, 'RALOY / INCA / BOSS'),
('CMB-000020', 1, 0, 2, 'RALOY / INCA / BOSS'),
('CMB-000021', 1, 0, 2, 'RALOY / INCA / BOSS'),
('CMB-000022', 1, 0, 2, 'RALOY / INCA / BOSS'),
('CMB-000023', 1, 0, 2, 'RALOY / INCA / BOSS'),
('CMB-000024', 1, 0, 2, 'RALOY / INCA / BOSS'),
('CMB-000025', 1, 0, 2, 'RALOY / INCA / BOSS'),
('CMB-000030', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000031', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000032', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000033', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000034', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000035', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000036', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000037', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000038', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000039', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000040', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000041', 1, 0, 2, 'VALVOLINE / FC'),
('CMB-000046', 1, 0, 2, 'WOLF / MEXLUB / ROSHFRANS'),
('CMB-000047', 1, 0, 2, 'WOLF / MEXLUB / ROSHFRANS'),
('CMB-000048', 1, 0, 2, 'WOLF / MEXLUB / ROSHFRANS'),
('CMB-000049', 1, 0, 2, 'WOLF / MEXLUB / ROSHFRANS'),
('CMB-000050', 1, 0, 2, 'WOLF / MEXLUB / ROSHFRANS'),
('CMB-000051', 1, 0, 2, 'WOLF / MEXLUB / ROSHFRANS'),
('CMB-000052', 1, 0, 2, 'WOLF / MEXLUB / ROSHFRANS'),
('CMB-000053', 1, 0, 2, 'WOLF / MEXLUB / ROSHFRANS')
ON DUPLICATE KEY UPDATE stock = VALUES(stock), stock_minimo = VALUES(stock_minimo), ubicacion = VALUES(ubicacion);

UPDATE servicios SET estado = 0 WHERE id <> 0;

INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'ALINEACION AUTOMOVIL', 'ALINEACION AUTOMOVIL', 10.50, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'ALINEACION AUTOMOVIL');
UPDATE servicios SET descripcion = 'ALINEACION AUTOMOVIL', precio = 10.50, duracion_estimada = '60', estado = 1 WHERE nombre = 'ALINEACION AUTOMOVIL';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'ALINEACION AUTO GRA.', 'ALINEACION AUTO GRA.', 13.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'ALINEACION AUTO GRA.');
UPDATE servicios SET descripcion = 'ALINEACION AUTO GRA.', precio = 13.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'ALINEACION AUTO GRA.';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'ALINEACION CAMIONETA PEQ.', 'ALINEACION CAMIONETA PEQ.', 15.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'ALINEACION CAMIONETA PEQ.');
UPDATE servicios SET descripcion = 'ALINEACION CAMIONETA PEQ.', precio = 15.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'ALINEACION CAMIONETA PEQ.';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'ALINEACION CAMIONETA GRANDE', 'ALINEACION CAMIONETA GRANDE', 17.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'ALINEACION CAMIONETA GRANDE');
UPDATE servicios SET descripcion = 'ALINEACION CAMIONETA GRANDE', precio = 17.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'ALINEACION CAMIONETA GRANDE';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'ALINEACION CAMIONETA GRAND.PLUS', 'ALINEACION CAMIONETA GRAND.PLUS', 20.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'ALINEACION CAMIONETA GRAND.PLUS');
UPDATE servicios SET descripcion = 'ALINEACION CAMIONETA GRAND.PLUS', precio = 20.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'ALINEACION CAMIONETA GRAND.PLUS';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'ALINEACION CAMION (16 17.5 )', 'ALINEACION CAMION (16 17.5 )', 20.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'ALINEACION CAMION (16 17.5 )');
UPDATE servicios SET descripcion = 'ALINEACION CAMION (16 17.5 )', precio = 20.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'ALINEACION CAMION (16 17.5 )';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'ALINEACION CAMION (22.5 )', 'ALINEACION CAMION (22.5 )', 20.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'ALINEACION CAMION (22.5 )');
UPDATE servicios SET descripcion = 'ALINEACION CAMION (22.5 )', precio = 20.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'ALINEACION CAMION (22.5 )';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'MONTURA AUTOMOVIL (POR RUEDA)', 'MONTURA AUTOMOVIL (POR RUEDA)', 3.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'MONTURA AUTOMOVIL (POR RUEDA)');
UPDATE servicios SET descripcion = 'MONTURA AUTOMOVIL (POR RUEDA)', precio = 3.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'MONTURA AUTOMOVIL (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'MONTURA CAMIONETA (POR RUEDA)', 'MONTURA CAMIONETA (POR RUEDA)', 2.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'MONTURA CAMIONETA (POR RUEDA)');
UPDATE servicios SET descripcion = 'MONTURA CAMIONETA (POR RUEDA)', precio = 2.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'MONTURA CAMIONETA (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'MONTURA CAMION (16 17.5 ) (POR RUEDA )', 'MONTURA CAMION (16 17.5 ) (POR RUEDA )', 3.50, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'MONTURA CAMION (16 17.5 ) (POR RUEDA )');
UPDATE servicios SET descripcion = 'MONTURA CAMION (16 17.5 ) (POR RUEDA )', precio = 3.50, duracion_estimada = '60', estado = 1 WHERE nombre = 'MONTURA CAMION (16 17.5 ) (POR RUEDA )';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'MONTURA CAMION (22.5 20 ) (POR RUEDA)', 'MONTURA CAMION (22.5 20 ) (POR RUEDA)', 5.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'MONTURA CAMION (22.5 20 ) (POR RUEDA)');
UPDATE servicios SET descripcion = 'MONTURA CAMION (22.5 20 ) (POR RUEDA)', precio = 5.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'MONTURA CAMION (22.5 20 ) (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO AUTOMOVIL (POR RUEDA)', 'BALANCEO AUTOMOVIL (POR RUEDA)', 2.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO AUTOMOVIL (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO AUTOMOVIL (POR RUEDA)', precio = 2.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO AUTOMOVIL (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO AUTOMOVIL ADHESIVO (POR RUEDA)', 'BALANCEO AUTOMOVIL ADHESIVO (POR RUEDA)', 5.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO AUTOMOVIL ADHESIVO (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO AUTOMOVIL ADHESIVO (POR RUEDA)', precio = 5.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO AUTOMOVIL ADHESIVO (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO CAMIONETA (POR RUEDA)', 'BALANCEO CAMIONETA (POR RUEDA)', 2.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO CAMIONETA (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO CAMIONETA (POR RUEDA)', precio = 2.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO CAMIONETA (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO CAMIONETA ADHESIVO (POR RUEDA)', 'BALANCEO CAMIONETA ADHESIVO (POR RUEDA)', 6.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO CAMIONETA ADHESIVO (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO CAMIONETA ADHESIVO (POR RUEDA)', precio = 6.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO CAMIONETA ADHESIVO (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO CAMION (16" 17.5") (POR RUEDA)', 'BALANCEO CAMION (16" 17.5") (POR RUEDA)', 8.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO CAMION (16" 17.5") (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO CAMION (16" 17.5") (POR RUEDA)', precio = 8.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO CAMION (16" 17.5") (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO DINAMICO AUTO/CAMIONETA (POR RUEDA)', 'BALANCEO DINAMICO AUTO/CAMIONETA (POR RUEDA)', 8.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO DINAMICO AUTO/CAMIONETA (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO DINAMICO AUTO/CAMIONETA (POR RUEDA)', precio = 8.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO DINAMICO AUTO/CAMIONETA (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO DINAMICO CAMION (16 17.5 ) (POR RUEDA)', 'BALANCEO DINAMICO CAMION (16 17.5 ) (POR RUEDA)', 15.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO DINAMICO CAMION (16 17.5 ) (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO DINAMICO CAMION (16 17.5 ) (POR RUEDA)', precio = 15.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO DINAMICO CAMION (16 17.5 ) (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO DINAMICO CAMION (20 22.5 ) (POR RUEDA)', 'BALANCEO DINAMICO CAMION (20 22.5 ) (POR RUEDA)', 10.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO DINAMICO CAMION (20 22.5 ) (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO DINAMICO CAMION (20 22.5 ) (POR RUEDA)', precio = 10.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO DINAMICO CAMION (20 22.5 ) (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'ROTACION AUTOMOVIL', 'ROTACION AUTOMOVIL', 2.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'ROTACION AUTOMOVIL');
UPDATE servicios SET descripcion = 'ROTACION AUTOMOVIL', precio = 2.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'ROTACION AUTOMOVIL';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'ROTACION CAMIONETA', 'ROTACION CAMIONETA', 3.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'ROTACION CAMIONETA');
UPDATE servicios SET descripcion = 'ROTACION CAMIONETA', precio = 3.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'ROTACION CAMIONETA';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'ROTACION CAMION (MOROCHA)', 'ROTACION CAMION (MOROCHA)', 4.50, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'ROTACION CAMION (MOROCHA)');
UPDATE servicios SET descripcion = 'ROTACION CAMION (MOROCHA)', precio = 4.50, duracion_estimada = '60', estado = 1 WHERE nombre = 'ROTACION CAMION (MOROCHA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'REVISION AUTOMOVIL PEQUENO', 'REVISION AUTOMOVIL PEQUENO', 2.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'REVISION AUTOMOVIL PEQUENO');
UPDATE servicios SET descripcion = 'REVISION AUTOMOVIL PEQUENO', precio = 2.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'REVISION AUTOMOVIL PEQUENO';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'REVISION AUTOMOVIL GRANDE', 'REVISION AUTOMOVIL GRANDE', 3.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'REVISION AUTOMOVIL GRANDE');
UPDATE servicios SET descripcion = 'REVISION AUTOMOVIL GRANDE', precio = 3.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'REVISION AUTOMOVIL GRANDE';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'REVISION CAMIONETA', 'REVISION CAMIONETA', 3.50, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'REVISION CAMIONETA');
UPDATE servicios SET descripcion = 'REVISION CAMIONETA', precio = 3.50, duracion_estimada = '60', estado = 1 WHERE nombre = 'REVISION CAMIONETA';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'REVISION CAMION', 'REVISION CAMION', 4.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'REVISION CAMION');
UPDATE servicios SET descripcion = 'REVISION CAMION', precio = 4.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'REVISION CAMION';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'REPARACION SENCILLA', 'REPARACION SENCILLA', 6.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'REPARACION SENCILLA');
UPDATE servicios SET descripcion = 'REPARACION SENCILLA', precio = 6.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'REPARACION SENCILLA';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'VALVULA TR413 N', 'VALVULA TR413 N', 1.50, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'VALVULA TR413 N');
UPDATE servicios SET descripcion = 'VALVULA TR413 N', precio = 1.50, duracion_estimada = '60', estado = 1 WHERE nombre = 'VALVULA TR413 N';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'VALVULA TR413 HIERRO', 'VALVULA TR413 HIERRO', 5.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'VALVULA TR413 HIERRO');
UPDATE servicios SET descripcion = 'VALVULA TR413 HIERRO', precio = 5.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'VALVULA TR413 HIERRO';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'VALVULA TR413 HIERRO CURVA', 'VALVULA TR413 HIERRO CURVA', 5.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'VALVULA TR413 HIERRO CURVA');
UPDATE servicios SET descripcion = 'VALVULA TR413 HIERRO CURVA', precio = 5.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'VALVULA TR413 HIERRO CURVA';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'VALVULA TR415 N', 'VALVULA TR415 N', 3.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'VALVULA TR415 N');
UPDATE servicios SET descripcion = 'VALVULA TR415 N', precio = 3.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'VALVULA TR415 N';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'VALVULA TR415 HIERRO', 'VALVULA TR415 HIERRO', 5.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'VALVULA TR415 HIERRO');
UPDATE servicios SET descripcion = 'VALVULA TR415 HIERRO', precio = 5.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'VALVULA TR415 HIERRO';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'VALVULA 17.5 BRONCE', 'VALVULA 17.5 BRONCE', 8.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'VALVULA 17.5 BRONCE');
UPDATE servicios SET descripcion = 'VALVULA 17.5 BRONCE', precio = 8.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'VALVULA 17.5 BRONCE';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'VALVULA 22.5 BRONCE', 'VALVULA 22.5 BRONCE', 10.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'VALVULA 22.5 BRONCE');
UPDATE servicios SET descripcion = 'VALVULA 22.5 BRONCE', precio = 10.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'VALVULA 22.5 BRONCE';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'CAMBIO DE ACEITE', 'CAMBIO DE ACEITE', 50.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'CAMBIO DE ACEITE');
UPDATE servicios SET descripcion = 'CAMBIO DE ACEITE', precio = 50.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'CAMBIO DE ACEITE';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'COMPACTO BASICO', 'BAL GANCHO, CALIBRACION AIRE, ROTACION', 10.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'COMPACTO BASICO');
UPDATE servicios SET descripcion = 'BAL GANCHO, CALIBRACION AIRE, ROTACION', precio = 10.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'COMPACTO BASICO';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'COMPACTO FULL', 'BAL PEGA, CALIBRACION AIRE, ROTACION, VALVULAS 5 RUEDAS, MANT. PESTANAS', 15.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'COMPACTO FULL');
UPDATE servicios SET descripcion = 'BAL PEGA, CALIBRACION AIRE, ROTACION, VALVULAS 5 RUEDAS, MANT. PESTANAS', precio = 15.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'COMPACTO FULL';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'CARRO GRANDE-CAMIONETA PEQ BASICO', 'BAL GANCHO, CALIBRACION AIRE, ROTACION', 12.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'CARRO GRANDE-CAMIONETA PEQ BASICO');
UPDATE servicios SET descripcion = 'BAL GANCHO, CALIBRACION AIRE, ROTACION', precio = 12.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'CARRO GRANDE-CAMIONETA PEQ BASICO';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'CARRO GRANDE-CAMIONETA PEQ FULL', 'BAL PEGA, CALIBRACION AIRE, ROTACION, VALVULAS 5 RUEDAS, MANT. PESTANAS', 20.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'CARRO GRANDE-CAMIONETA PEQ FULL');
UPDATE servicios SET descripcion = 'BAL PEGA, CALIBRACION AIRE, ROTACION, VALVULAS 5 RUEDAS, MANT. PESTANAS', precio = 20.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'CARRO GRANDE-CAMIONETA PEQ FULL';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'CAMIONETA GRANDE BASICO', 'BAL GANCHO, CALIBRACION AIRE, ROTACION', 16.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'CAMIONETA GRANDE BASICO');
UPDATE servicios SET descripcion = 'BAL GANCHO, CALIBRACION AIRE, ROTACION', precio = 16.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'CAMIONETA GRANDE BASICO';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'CAMIONETA GRANDE FULL', 'BAL PEGA, CALIBRACION AIRE, ROTACION, VALVULAS 5 RUEDAS, MANT. PESTANAS', 35.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'CAMIONETA GRANDE FULL');
UPDATE servicios SET descripcion = 'BAL PEGA, CALIBRACION AIRE, ROTACION, VALVULAS 5 RUEDAS, MANT. PESTANAS', precio = 35.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'CAMIONETA GRANDE FULL';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO CAMIONETA PEQ. (POR RUEDA)', 'BALANCEO CAMIONETA PEQ. (POR RUEDA)', 4.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO CAMIONETA PEQ. (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO CAMIONETA PEQ. (POR RUEDA)', precio = 4.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO CAMIONETA PEQ. (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO CAMIONETA PEQ. ADHESIVO (POR RUEDA)', 'BALANCEO CAMIONETA PEQ. ADHESIVO (POR RUEDA)', 6.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO CAMIONETA PEQ. ADHESIVO (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO CAMIONETA PEQ. ADHESIVO (POR RUEDA)', precio = 6.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO CAMIONETA PEQ. ADHESIVO (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO CAMIONETA GRANDE (POR RUEDA)', 'BALANCEO CAMIONETA GRANDE (POR RUEDA)', 8.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO CAMIONETA GRANDE (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO CAMIONETA GRANDE (POR RUEDA)', precio = 8.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO CAMIONETA GRANDE (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'BALANCEO CAMIONETA GR. ADHESIVO (POR RUEDA)', 'BALANCEO CAMIONETA GR. ADHESIVO (POR RUEDA)', 10.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'BALANCEO CAMIONETA GR. ADHESIVO (POR RUEDA)');
UPDATE servicios SET descripcion = 'BALANCEO CAMIONETA GR. ADHESIVO (POR RUEDA)', precio = 10.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'BALANCEO CAMIONETA GR. ADHESIVO (POR RUEDA)';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'VALVULA TR413 NEGRA', 'VALVULA TR413 NEGRA', 1.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'VALVULA TR413 NEGRA');
UPDATE servicios SET descripcion = 'VALVULA TR413 NEGRA', precio = 1.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'VALVULA TR413 NEGRA';
INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, estado) SELECT 'VALVULA TR415 NEGRA', 'VALVULA TR415 NEGRA', 3.00, '60', 1 WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'VALVULA TR415 NEGRA');
UPDATE servicios SET descripcion = 'VALVULA TR415 NEGRA', precio = 3.00, duracion_estimada = '60', estado = 1 WHERE nombre = 'VALVULA TR415 NEGRA';

INSERT IGNORE INTO servicio_sucursal (servicio_id, sucursal_id, estado) SELECT id, 1, 1 FROM servicios WHERE estado = 1;

INSERT INTO configuracion (clave, valor) VALUES
('nombre_empresa', 'Transalca C.A.'),
('rif_empresa', 'J-00000000-0'),
('telefono_empresa', '04240000000'),
('direccion_empresa', 'Direccion Principal'),
('email_empresa', 'info@transalca.com'),
('moneda', 'USD')
ON DUPLICATE KEY UPDATE valor = VALUES(valor);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS cedula_prefijo VARCHAR(2) AFTER cedula,
    ADD COLUMN IF NOT EXISTS tipo_cliente VARCHAR(20) NOT NULL DEFAULT 'persona' AFTER cedula_prefijo,
    ADD COLUMN IF NOT EXISTS origen_registro VARCHAR(20) DEFAULT 'cliente' AFTER estado,
    ADD COLUMN IF NOT EXISTS usuario_id INT DEFAULT NULL AFTER origen_registro;

ALTER TABLE mecanicos
    ADD COLUMN IF NOT EXISTS cedula_prefijo VARCHAR(2) AFTER cedula,
    ADD COLUMN IF NOT EXISTS usuario_id INT DEFAULT NULL AFTER foto_perfil;

ALTER TABLE proveedores
    ADD COLUMN IF NOT EXISTS rif_prefijo VARCHAR(2) AFTER rif;

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
    cliente_cedula VARCHAR(20) NOT NULL,
    marca VARCHAR(100) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    anio SMALLINT,
    placa VARCHAR(20) PRIMARY KEY,
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
    titulo_vehiculo VARCHAR(255),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_vehiculos_cliente FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE
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
    vehiculo_placa VARCHAR(20) NOT NULL,
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
    CONSTRAINT fk_mantenimientos_vehiculo FOREIGN KEY (vehiculo_placa) REFERENCES vehiculos(placa) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_mantenimientos_regla FOREIGN KEY (regla_id) REFERENCES reglas_mantenimiento(id) ON DELETE SET NULL,
    INDEX idx_mant_vehiculo_estado (vehiculo_placa, estado)
);

CREATE TABLE IF NOT EXISTS bitacora_vehiculo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehiculo_placa VARCHAR(20) NOT NULL,
    servicio_mecanico_id INT DEFAULT NULL,
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
    CONSTRAINT fk_bitacora_vehiculo FOREIGN KEY (vehiculo_placa) REFERENCES vehiculos(placa) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_bitacora_servicio_mecanico FOREIGN KEY (servicio_mecanico_id) REFERENCES servicio_mecanico(id) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_bitacora_vehiculo_fecha (vehiculo_placa, fecha)
);

CREATE TABLE IF NOT EXISTS consumo_combustible (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehiculo_placa VARCHAR(20) NOT NULL,
    modo VARCHAR(20) DEFAULT 'manual',
    consumo_estimado_lkm DECIMAL(6,2),
    fuente_dato VARCHAR(500),
    km_recorridos INT,
    litros_consumidos DECIMAL(8,2),
    precio_litro DECIMAL(10,2),
    fecha DATE,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_consumo_vehiculo FOREIGN KEY (vehiculo_placa) REFERENCES vehiculos(placa) ON UPDATE CASCADE ON DELETE CASCADE,
    INDEX idx_consumo_vehiculo_fecha (vehiculo_placa, fecha)
);

CREATE TABLE IF NOT EXISTS tickets_soporte (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_cedula VARCHAR(20) NOT NULL,
    asunto VARCHAR(300) NOT NULL,
    descripcion TEXT,
    estado VARCHAR(30) NOT NULL DEFAULT 'abierto',
    prioridad VARCHAR(20) DEFAULT 'media',
    referencia_tipo VARCHAR(30) DEFAULT 'general',
    referencia_id VARCHAR(50) DEFAULT NULL,
    asignado_a VARCHAR(20) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_ticket_cliente FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE,
    CONSTRAINT fk_ticket_asignado FOREIGN KEY (asignado_a) REFERENCES mecanicos(cedula) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_ticket_cliente (cliente_cedula)
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
    servicio_mecanico_id INT NOT NULL,
    precio_servicio DECIMAL(10,2) NOT NULL,
    porcentaje_comision DECIMAL(5,2) DEFAULT 30.00,
    monto_comision DECIMAL(10,2) NOT NULL,
    estado_pago VARCHAR(20) DEFAULT 'pendiente',
    fecha_pago DATE,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comision_servicio_mecanico FOREIGN KEY (servicio_mecanico_id) REFERENCES servicio_mecanico(id),
    UNIQUE KEY uq_comision_servicio_mecanico (servicio_mecanico_id),
    INDEX idx_comision_estado (estado_pago)
);

CREATE TABLE IF NOT EXISTS cotizaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_cedula VARCHAR(20) NOT NULL,
    tasa_cambio_id INT DEFAULT NULL,
    tasa_usada DECIMAL(12,4) NOT NULL,
    tipo_tasa VARCHAR(20) NOT NULL,
    total_usd DECIMAL(12,2) NOT NULL,
    total_bs DECIMAL(14,2) NOT NULL,
    vigente_hasta DATETIME NOT NULL,
    estado VARCHAR(20) DEFAULT 'vigente',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cotizacion_cliente FOREIGN KEY (cliente_cedula) REFERENCES clientes(cedula) ON UPDATE CASCADE,
    CONSTRAINT fk_cotizacion_tasa FOREIGN KEY (tasa_cambio_id) REFERENCES tasas_cambio(id) ON DELETE SET NULL,
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
    INDEX idx_notif_usuario_leida (usuario_id, leida, created_at),
    INDEX idx_notif_cliente_leida (cliente_cedula, leida, created_at)
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
