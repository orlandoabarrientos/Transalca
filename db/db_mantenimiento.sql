CREATE DATABASE IF NOT EXISTS db_mantenimiento CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE db_mantenimiento;

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    cedula_prefijo VARCHAR(2),
    email VARCHAR(150) UNIQUE NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    direccion TEXT,
    password_hash VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'cliente',
    foto_perfil VARCHAR(255) DEFAULT 'default.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE usuario_rol (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    rol_id INT NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY unique_usuario_rol (usuario_id, rol_id)
);

CREATE TABLE permisos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rol_id INT NOT NULL,
    modulo VARCHAR(100) NOT NULL,
    crear TINYINT(1) DEFAULT 0,
    leer TINYINT(1) DEFAULT 0,
    actualizar TINYINT(1) DEFAULT 0,
    eliminar TINYINT(1) DEFAULT 0,
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY unique_rol_modulo (rol_id, modulo)
);

CREATE TABLE bitacora (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    accion VARCHAR(50) NOT NULL,
    modulo VARCHAR(100) NOT NULL,
    descripcion TEXT,
    ip VARCHAR(45),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE tokens_recuperacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    expira DATETIME NOT NULL,
    usado TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

DELIMITER //
CREATE FUNCTION fn_verificar_credenciales(p_email VARCHAR(150), p_password VARCHAR(255))
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE v_id INT DEFAULT 0;
    SELECT id INTO v_id FROM usuarios WHERE email = p_email AND estado = 1 LIMIT 1;
    RETURN v_id;
END //
DELIMITER ;

CREATE TABLE IF NOT EXISTS eventos_sistema (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    accion VARCHAR(50) NOT NULL,
    modulo VARCHAR(100) NOT NULL,
    descripcion TEXT,
    ip VARCHAR(45) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DELIMITER //
CREATE TRIGGER trg_bitacora_eventos_sistema_insert
AFTER INSERT ON eventos_sistema
FOR EACH ROW
BEGIN
    INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
    VALUES (NEW.usuario_id, NEW.accion, NEW.modulo, NEW.descripcion, NEW.ip);
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_bitacora_usuario_insert
AFTER INSERT ON usuarios
FOR EACH ROW
BEGIN
    INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
    VALUES (COALESCE(@current_usuario_id, NEW.id), 'CREAR', 'USUARIOS', CONCAT('Usuario creado: ', NEW.nombre, ' ', NEW.apellido), COALESCE(@current_ip, '127.0.0.1'));
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_bitacora_usuario_update
AFTER UPDATE ON usuarios
FOR EACH ROW
BEGIN
    IF OLD.estado = 1 AND NEW.estado = 0 THEN
        INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'USUARIOS', CONCAT('Usuario eliminado ID: ', NEW.id), COALESCE(@current_ip, '127.0.0.1'));
    ELSEIF OLD.estado <> NEW.estado THEN
        INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'USUARIOS', CONCAT('Estado de usuario cambiado ID: ', NEW.id), COALESCE(@current_ip, '127.0.0.1'));
    ELSE
        INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'USUARIOS', CONCAT('Usuario modificado ID: ', NEW.id), COALESCE(@current_ip, '127.0.0.1'));
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_bitacora_roles_insert
AFTER INSERT ON roles
FOR EACH ROW
BEGIN
    INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
    VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'ROLES', CONCAT('Rol creado: ', NEW.nombre), COALESCE(@current_ip, '127.0.0.1'));
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_bitacora_roles_update
AFTER UPDATE ON roles
FOR EACH ROW
BEGIN
    IF OLD.estado = 1 AND NEW.estado = 0 THEN
        INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'ROLES', CONCAT('Rol desactivado: ', NEW.nombre), COALESCE(@current_ip, '127.0.0.1'));
    ELSE
        INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'ROLES', CONCAT('Rol modificado: ', OLD.nombre, ' -> ', NEW.nombre), COALESCE(@current_ip, '127.0.0.1'));
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE sp_crear_usuario(
    IN p_nombre VARCHAR(100),
    IN p_apellido VARCHAR(100),
    IN p_cedula VARCHAR(20),
    IN p_email VARCHAR(150),
    IN p_telefono VARCHAR(20),
    IN p_direccion TEXT,
    IN p_password VARCHAR(255),
    IN p_tipo VARCHAR(20)
)
BEGIN
    INSERT INTO usuarios (nombre, apellido, cedula, email, telefono, direccion, password_hash, tipo)
    VALUES (p_nombre, p_apellido, p_cedula, p_email, p_telefono, p_direccion, p_password, p_tipo);
END //
DELIMITER ;

INSERT INTO roles (nombre, descripcion) VALUES ('Administrador', 'Acceso total al sistema');
INSERT INTO roles (nombre, descripcion) VALUES ('Vendedor', 'Acceso a ventas y stock');
INSERT INTO roles (nombre, descripcion) VALUES ('Cliente', 'Acceso al portal de compras');

INSERT INTO usuarios (nombre, apellido, cedula, email, telefono, direccion, password_hash, tipo)
VALUES ('Admin', 'Sistema', 'V-00000000', 'admin@transalca.com', '04240000000', 'Oficina Principal',
'scrypt:32768:8:1$NP7iU10YgSPJPmAh$a2320143ce75e7daa2bf829c27fde8a333c63b4f7b39ebd454d526818ae66be465d09334da3fd829335a11f6a7ff2ef3281c89929f965754d79d22a5f74d8f37', 'empleado');

ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS cedula_prefijo VARCHAR(2) AFTER cedula;

INSERT INTO usuario_rol (usuario_id, rol_id) VALUES (1, 1);

INSERT INTO permisos (rol_id, modulo, crear, leer, actualizar, eliminar) VALUES
(1, 'usuarios', 1, 1, 1, 1),
(1, 'roles', 1, 1, 1, 1),
(1, 'productos', 1, 1, 1, 1),
(1, 'categorias', 1, 1, 1, 1),
(1, 'marcas', 1, 1, 1, 1),
(1, 'proveedores', 1, 1, 1, 1),
(1, 'empresas', 1, 1, 1, 1),
(1, 'mecanicos', 1, 1, 1, 1),
(1, 'stock', 1, 1, 1, 1),
(1, 'servicios', 1, 1, 1, 1),
(1, 'creditos', 1, 1, 1, 1),
(1, 'metodos_pago', 1, 1, 1, 1),
(1, 'promociones', 1, 1, 1, 1),
(1, 'ordenes', 1, 1, 1, 1),
(1, 'pagos', 1, 1, 1, 1),
(1, 'bitacora', 0, 1, 0, 0),
(1, 'reportes', 0, 1, 0, 0),
(1, 'respaldos', 1, 1, 0, 0),
(1, 'qr', 1, 1, 1, 1),
(1, 'sucursales', 1, 1, 1, 1),
(2, 'productos', 0, 1, 0, 0),
(2, 'categorias', 0, 1, 0, 0),
(2, 'marcas', 0, 1, 0, 0),
(2, 'stock', 0, 1, 1, 0),
(2, 'servicios', 0, 1, 1, 0),
(2, 'ordenes', 1, 1, 1, 0),
(2, 'pagos', 0, 1, 1, 0),
(2, 'creditos', 0, 1, 1, 0),
(2, 'metodos_pago', 0, 1, 0, 0),
(2, 'reportes', 0, 1, 0, 0);
