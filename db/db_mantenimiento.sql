-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: db_mantenimiento
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bitacora`
--

DROP TABLE IF EXISTS `bitacora`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bitacora` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `accion` varchar(50) NOT NULL,
  `modulo` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `bitacora_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=190 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bitacora`
--

LOCK TABLES `bitacora` WRITE;
/*!40000 ALTER TABLE `bitacora` DISABLE KEYS */;
INSERT INTO `bitacora` VALUES (1,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-04-30 04:33:14'),(2,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-04-30 04:35:04'),(3,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-04-30 04:35:38'),(5,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-05-01 00:03:26'),(6,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-05-01 00:03:42'),(7,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-05-01 01:36:21'),(8,4,'LOGIN','AUTH','Inicio de sesion: orlandoabarrientos@gmail.com','127.0.0.1','2026-05-01 01:37:12'),(9,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-05-01 01:37:23'),(10,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-05-01 01:37:35'),(11,4,'LOGIN','AUTH','Inicio de sesion: orlandoabarrientos@gmail.com','127.0.0.1','2026-05-01 01:37:45'),(12,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-05-01 01:38:09'),(13,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-05-01 01:38:31'),(14,4,'LOGIN','AUTH','Inicio de sesion: orlandoabarrientos@gmail.com','127.0.0.1','2026-05-01 01:38:40'),(15,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-05-01 01:42:24'),(16,1,'CREAR','CATEGORIAS','Categoria creada: TestCat0507224100','127.0.0.1','2026-05-08 02:41:00'),(17,1,'CREAR','MARCAS','Marca creada: TestBrand0507224100','127.0.0.1','2026-05-08 02:41:00'),(18,1,'CREAR','PROVEEDORES','Proveedor creado: Proveedor 0507224100','127.0.0.1','2026-05-08 02:41:00'),(19,1,'CREAR','SERVICIOS','Servicio creado: Servicio 0507224100','127.0.0.1','2026-05-08 02:41:00'),(20,1,'CREAR','PRODUCTOS','Producto creado: Producto 0507224100','127.0.0.1','2026-05-08 02:41:00'),(21,1,'CREAR','USUARIOS','Usuario creado: Usuario Prueba','127.0.0.1','2026-05-08 02:41:01'),(22,1,'CREAR','INVENTARIO','Orden de compra creada ID: 1','127.0.0.1','2026-05-08 02:41:01'),(23,1,'CREAR','MECANICOS','Mecanico creado: V-07224157','127.0.0.1','2026-05-08 02:41:57'),(24,1,'CREAR','SERVICIOS','Servicio creado: Servicio afahcceccj','127.0.0.1','2026-05-08 02:42:29'),(25,1,'CREAR','MECANICOS','Mecanico creado: V-07224236','127.0.0.1','2026-05-08 02:42:30'),(26,1,'CREAR','ROLES','Rol creado: Supervisor afahcceccj','127.0.0.1','2026-05-08 02:42:30'),(27,1,'CREAR','SERVICIO_MECANICO','Registro servicio mecanico ID: 1','127.0.0.1','2026-05-08 02:42:30'),(28,1,'CREAR','CATEGORIAS','Categoria creada: Cat afahcceddi','127.0.0.1','2026-05-08 02:43:38'),(29,1,'CREAR','MARCAS','Marca creada: Marca afahcceddi','127.0.0.1','2026-05-08 02:43:38'),(30,1,'CREAR','PROVEEDORES','Proveedor creado: Proveedor afahcceddi','127.0.0.1','2026-05-08 02:43:38'),(31,1,'CREAR','SERVICIOS','Servicio creado: Servicio afahcceddi','127.0.0.1','2026-05-08 02:43:38'),(32,1,'CREAR','PRODUCTOS','Producto creado: Producto afahcceddi','127.0.0.1','2026-05-08 02:43:38'),(33,1,'CREAR','MECANICOS','Mecanico creado: V-07224351','127.0.0.1','2026-05-08 02:43:38'),(34,1,'CREAR','ROLES','Rol creado: Rol afahcceddi','127.0.0.1','2026-05-08 02:43:38'),(35,1,'CREAR','USUARIOS','Usuario creado: Lucia Usuario','127.0.0.1','2026-05-08 02:43:38'),(36,1,'CREAR','PROMOCIONES','Promocion creada: Promo afahcceddi','127.0.0.1','2026-05-08 02:43:38'),(37,1,'CREAR','SERVICIO_MECANICO','Registro servicio mecanico ID: 2','127.0.0.1','2026-05-08 02:43:38'),(38,1,'CREAR','INVENTARIO','Orden de compra creada ID: 2','127.0.0.1','2026-05-08 02:43:38'),(39,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','10.2.0.2','2026-05-08 03:10:23'),(40,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-05-18 04:19:10'),(41,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-05-18 04:19:40'),(42,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-05-18 04:19:50'),(43,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-05-18 04:20:47'),(44,1,'CREAR','ORDENES','Orden de venta creada ID: 1','127.0.0.1','2026-05-18 04:33:01'),(45,1,'CREAR','SERVICIO_MECANICO','Registro servicio mecanico ID: 3','127.0.0.1','2026-05-18 04:35:49'),(46,1,'MODIFICAR','PROMOCIONES','Promocion modificada ID: 1','127.0.0.1','2026-05-18 04:37:09'),(47,1,'MODIFICAR','PROMOCIONES','Promocion modificada ID: 1','127.0.0.1','2026-05-18 04:37:25'),(48,1,'CREAR','PRODUCTOS','Producto creado: Producto prueba','127.0.0.1','2026-05-18 05:18:50'),(49,1,'MODIFICAR','PRODUCTOS','Estado producto cambiado: CODX1779081530','127.0.0.1','2026-05-18 05:18:50'),(50,1,'CREAR','SERVICIOS','Servicio creado: Servicio prueba','127.0.0.1','2026-05-18 05:18:50'),(51,1,'ELIMINAR','SERVICIOS','Servicio desactivado ID: 10','127.0.0.1','2026-05-18 05:18:50'),(52,1,'CREAR','PROMOCIONES','Promocion creada: ded','127.0.0.1','2026-05-21 02:47:42'),(53,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-05-21 03:04:51'),(54,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-05-21 03:04:52'),(55,1,'MODIFICAR','PAGOS','Pago aprobado comprobante ID: 1','127.0.0.1','2026-05-21 03:13:52'),(56,1,'MODIFICAR','PROMOCIONES','Promocion modificada ID: 2','127.0.0.1','2026-05-21 03:14:10'),(57,1,'CREAR','ORDENES','Orden de venta creada ID: 2','127.0.0.1','2026-05-21 06:08:02'),(58,1,'MODIFICAR','PRODUCTOS','Estado producto cambiado: COD0507224100','127.0.0.1','2026-05-22 05:57:16'),(59,1,'MODIFICAR','PRODUCTOS','Estado producto cambiado: PC0507224338','127.0.0.1','2026-05-22 06:32:49'),(60,1,'ELIMINAR','CATEGORIAS','Categoria desactivada: Baterias','127.0.0.1','2026-05-22 06:33:01'),(61,1,'ELIMINAR','CATEGORIAS','Categoria desactivada: Cat afahcceddi','127.0.0.1','2026-05-22 06:43:03'),(62,1,'MODIFICAR','CREDITO','Fechas de credito actualizadas orden: 3','127.0.0.1','2026-05-29 06:40:53'),(63,1,'MODIFICAR','CREDITO','Credito pagado orden: 3','127.0.0.1','2026-05-29 06:40:53'),(64,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-05-29 07:02:05'),(65,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-05-29 07:02:16'),(66,1,'MODIFICAR','PAGOS','Pago rechazado comprobante ID: 2','127.0.0.1','2026-05-29 07:05:17'),(67,1,'MODIFICAR','CREDITO','Abono registrado orden: 5','127.0.0.1','2026-05-29 07:47:59'),(68,1,'MODIFICAR','CREDITO','Abono registrado orden: 6','127.0.0.1','2026-05-29 07:50:02'),(69,1,'MODIFICAR','CREDITO','Crédito pagado orden: 6','127.0.0.1','2026-05-29 07:50:02'),(70,1,'CREAR','CREDITO','Crédito registrado para la empresa J-55656666-5 por $777777.00','127.0.0.1','2026-05-29 08:15:01'),(71,1,'MODIFICAR','CREDITO','Abono registrado orden: 8','127.0.0.1','2026-05-29 08:15:29'),(72,1,'MODIFICAR','CREDITO','Abono registrado orden: 8','127.0.0.1','2026-05-29 08:15:46'),(73,1,'CREAR','PROMOCIONES','Promocion creada: dede','127.0.0.1','2026-06-02 21:35:32'),(74,1,'CREAR','PRODUCTOS','Producto creado: dede','127.0.0.1','2026-06-02 21:37:09'),(75,1,'CREAR','METODOS_PAGO','Método de pago creado: dede','127.0.0.1','2026-06-02 21:37:41'),(76,1,'CREAR','SERVICIO_MECANICO','Registro servicio mecanico ID: 5','127.0.0.1','2026-06-02 22:13:58'),(77,1,'CREAR','ORDEN_COMPRA','Orden de compra registrada ID: 1 para el proveedor J-50722410-0','127.0.0.1','2026-06-02 23:38:42'),(78,1,'MODIFICAR','ORDEN_COMPRA','Orden de compra ID 1 marcada como COMPRADA. Stock sumado.','127.0.0.1','2026-06-02 23:43:11'),(79,1,'MODIFICAR','TASAS_CAMBIO','Tasa modificada ID: 11','127.0.0.1','2026-06-03 05:43:36'),(80,1,'MODIFICAR','TASAS_CAMBIO','Tasa modificada ID: 11','127.0.0.1','2026-06-03 05:44:06'),(81,1,'ELIMINAR','SERVICIOS','Servicio desactivado ID: 17','127.0.0.1','2026-06-03 06:00:40'),(82,1,'CREAR','SERVICIOS','Servicio creado: ALINEACION AUTO GRA.','127.0.0.1','2026-06-03 06:00:52'),(83,1,'CREAR','SERVICIOS','Servicio creado: ALINEACION AUTO GRA.','127.0.0.1','2026-06-03 06:00:52'),(84,1,'ELIMINAR','SERVICIOS','Servicio desactivado ID: 17','127.0.0.1','2026-06-03 06:01:08'),(85,1,'ELIMINAR','SERVICIOS','Servicio desactivado ID: 21','127.0.0.1','2026-06-03 06:02:00'),(86,1,'MODIFICAR','PROVEEDORES','Estado proveedor cambiado: J-50722434-9','127.0.0.1','2026-06-03 06:04:36'),(87,1,'CREAR','PROVEEDORES','Proveedor creado: Proveedor afahcceddi','127.0.0.1','2026-06-03 06:04:46'),(88,1,'ELIMINAR','SERVICIOS','Servicio desactivado ID: 16','127.0.0.1','2026-06-03 06:05:06'),(89,1,'LEER','ESCANER','QR escaneado ID: 1 | Modo: factura_validada','127.0.0.1','2026-06-03 06:24:20'),(90,1,'MODIFICAR','SERVICIO_MECANICO','Servicio mecanico modificado ID: 5','127.0.0.1','2026-06-03 07:23:16'),(91,1,'MODIFICAR','SERVICIO_MECANICO','Servicio mecanico modificado ID: 5','127.0.0.1','2026-06-03 07:23:31'),(92,1,'CREAR','QR','QR creado ID: 4','127.0.0.1','2026-06-03 14:51:02'),(93,1,'ELIMINAR','QR','QR desactivado ID: 4','127.0.0.1','2026-06-03 14:51:13'),(94,1,'ELIMINAR','QR','QR desactivado ID: 3','127.0.0.1','2026-06-03 14:51:15'),(95,1,'ELIMINAR','QR','QR desactivado ID: 2','127.0.0.1','2026-06-03 14:51:17'),(96,1,'ELIMINAR','QR','QR desactivado ID: 1','127.0.0.1','2026-06-03 14:51:19'),(97,1,'CREAR','QR','QR creado ID: 5','127.0.0.1','2026-06-03 14:51:33'),(98,1,'LEER','ESCANER','QR escaneado ID: 5 | Modo: factura_invalida','127.0.0.1','2026-06-03 14:53:01'),(99,1,'MODIFICAR','ESCANER','Solicitud validacion ID 1 respondida como aprobar','127.0.0.1','2026-06-03 14:53:28'),(100,1,'LEER','ESCANER','QR escaneado ID: 5 | Modo: factura_invalida','127.0.0.1','2026-06-03 14:53:57'),(101,1,'LEER','ESCANER','QR escaneado ID: 6 | Modo: factura_validada','127.0.0.1','2026-06-03 14:55:42'),(102,1,'CREAR','ORDENES','Orden de venta creada ID: 9','127.0.0.1','2026-06-03 15:39:55'),(103,1,'MODIFICAR','METODOS_PAGO','Método de pago modificado: dede','127.0.0.1','2026-06-03 16:02:17'),(104,1,'MODIFICAR','METODOS_PAGO','Método de pago modificado: Pago movil','127.0.0.1','2026-06-03 16:28:28'),(105,1,'MODIFICAR','METODOS_PAGO','Método de pago modificado: pago_movil','127.0.0.1','2026-06-03 16:31:55'),(106,1,'MODIFICAR','METODOS_PAGO','Método de pago modificado: pago_movil','127.0.0.1','2026-06-03 16:32:39'),(107,1,'CREAR','QR','QR creado ID: 8','127.0.0.1','2026-06-03 16:38:09'),(108,1,'LEER','ESCANER','QR escaneado ID: 8 | Modo: promocion_info','127.0.0.1','2026-06-03 16:39:07'),(109,1,'LEER','ESCANER','QR escaneado ID: 8 | Modo: promocion_info','127.0.0.1','2026-06-03 16:40:41'),(110,1,'LEER','ESCANER','QR escaneado ID: 8 | Modo: promocion_directa_aplicada','127.0.0.1','2026-06-03 16:47:49'),(111,1,'LEER','ESCANER','QR escaneado ID: 8 | Modo: qr_sin_utilidad','127.0.0.1','2026-06-03 16:58:43'),(112,1,'LEER','ESCANER','QR escaneado ID: 8 | Modo: promocion_directa_aplicada','127.0.0.1','2026-06-03 16:59:09'),(113,1,'LEER','ESCANER','QR escaneado ID: 8 | Modo: qr_sin_utilidad','127.0.0.1','2026-06-03 17:00:54'),(114,1,'MODIFICAR','QR','QR modificado ID: 8','127.0.0.1','2026-06-03 17:01:06'),(115,1,'LEER','ESCANER','QR escaneado ID: 8 | Modo: promocion_directa_aplicada','127.0.0.1','2026-06-03 17:01:36'),(116,1,'LEER','ESCANER','QR escaneado ID: 8 | Modo: qr_sin_utilidad','127.0.0.1','2026-06-03 17:01:45'),(117,1,'MODIFICAR','QR','QR modificado ID: 8','127.0.0.1','2026-06-03 17:01:50'),(118,1,'LEER','ESCANER','QR escaneado ID: 8 | Modo: promocion_directa_aplicada','127.0.0.1','2026-06-03 17:01:57'),(119,1,'CREAR','TASA_CAMBIO','Tasa de cambio creada ID: 12','127.0.0.1','2026-06-06 00:29:15'),(120,1,'CREAR','TASA_CAMBIO','Tasa de cambio creada ID: 13','127.0.0.1','2026-06-06 20:01:09'),(121,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-06-06 20:51:08'),(122,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-06-06 20:51:11'),(123,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-06-06 20:51:14'),(124,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-06-06 20:52:32'),(125,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-06-10 20:42:35'),(126,1,'CREAR','TASA_CAMBIO','Tasa de cambio creada ID: 16','127.0.0.1','2026-06-10 20:43:24'),(127,1,'CREAR','ORDENES','Orden creada ID: 12 para cliente: V-00000000','127.0.0.1','2026-06-10 21:09:31'),(128,1,'CREAR','PAGOS','Comprobante de pago subido orden ID: 12','127.0.0.1','2026-06-10 21:09:31'),(129,1,'CREAR','QR','Codigo QR creado: factura','127.0.0.1','2026-06-10 21:09:31'),(130,1,'CREAR','VEHICULOS','Vehiculo registrado placa: DADADA','127.0.0.1','2026-06-10 22:24:01'),(131,1,'CREAR','VEHICULOS','Vehiculo registrado placa: DEDED','127.0.0.1','2026-06-10 22:24:32'),(132,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-06-11 03:28:46'),(133,1,'MODIFICAR','TASA_CAMBIO','Tasa de cambio modificada ID: 16','127.0.0.1','2026-06-11 03:28:56'),(134,1,'MODIFICAR','TASA_CAMBIO','Tasa de cambio modificada ID: 16','127.0.0.1','2026-06-11 03:36:54'),(135,1,'CREAR','VEHICULOS','Registro de servicio para placa: AB123CD','127.0.0.1','2026-06-11 03:39:05'),(136,1,'CREAR','VEHICULOS','Registro de servicio para placa: DADADA','127.0.0.1','2026-06-11 03:39:05'),(137,1,'MODIFICAR','TASA_CAMBIO','Tasa de cambio modificada ID: 16','127.0.0.1','2026-06-11 03:39:36'),(138,1,'MODIFICAR','TASA_CAMBIO','Tasa de cambio modificada ID: 16','127.0.0.1','2026-06-11 03:41:03'),(139,1,'MODIFICAR','TASA_CAMBIO','Tasa de cambio modificada ID: 16','127.0.0.1','2026-06-11 03:43:27'),(140,1,'MODIFICAR','TASA_CAMBIO','Tasa de cambio modificada ID: 16','127.0.0.1','2026-06-11 03:45:40'),(141,1,'MODIFICAR','TASA_CAMBIO','Tasa de cambio modificada ID: 16','127.0.0.1','2026-06-11 03:54:28'),(142,4,'CREAR','ORDENES','Orden creada ID: 13 para cliente: 30396029','127.0.0.1','2026-06-11 06:14:42'),(143,4,'MODIFICAR','INVENTARIO','Inventario modificado: BAT-000016 (nueva cantidad: 10)','127.0.0.1','2026-06-11 06:14:42'),(144,4,'CREAR','QR','Codigo QR creado: factura','127.0.0.1','2026-06-11 06:14:42'),(145,1,'CREAR','PAGOS','Comprobante de pago subido orden ID: 13','127.0.0.1','2026-06-11 06:14:43'),(146,1,'aceptado','PAGOS','Comprobante de pago orden ID: 13 Estado: verificado','127.0.0.1','2026-06-11 06:15:22'),(147,1,'MODIFICAR','ORDENES','Orden modificada ID: 13','127.0.0.1','2026-06-11 06:15:22'),(148,1,'CREAR','COMISIONES','Comision registrada servicio-mecanico: 7','127.0.0.1','2026-06-11 06:15:22'),(149,1,'CREAR','VEHICULOS','Registro de servicio para placa: AB123CD','127.0.0.1','2026-06-11 06:15:22'),(150,1,'CREAR','VEHICULOS','Registro de servicio para placa: AB123CD','127.0.0.1','2026-06-11 06:16:10'),(151,4,'CREAR','VEHICULOS','Vehiculo registrado placa: TEST99X','127.0.0.1','2026-06-11 06:17:13'),(152,4,'CREAR','TICKETS','Ticket creado ID: 3','127.0.0.1','2026-06-11 06:17:13'),(153,4,'CREAR','TICKETS','Ticket creado ID: 4','127.0.0.1','2026-06-11 06:17:14'),(154,1,'MODIFICAR','INVENTARIO','Inventario modificado: BAT-000016 (nueva cantidad: 11)','127.0.0.1','2026-06-11 06:17:14'),(155,1,'CREAR','ORDENES','Orden creada ID: 14 para cliente: J-55656666-5','127.0.0.1','2026-06-11 06:17:58'),(156,1,'CREAR','CREDITO','Credito registrado orden: 14','127.0.0.1','2026-06-11 06:17:58'),(157,1,'MODIFICAR','INVENTARIO','Inventario modificado: BAT-000016 (nueva cantidad: 1)','127.0.0.1','2026-06-11 06:17:58'),(158,1,'MODIFICAR','INVENTARIO','Inventario modificado: BAT-000016 (nueva cantidad: 1)','127.0.0.1','2026-06-11 06:17:59'),(159,1,'MODIFICAR','INVENTARIO','Inventario modificado: BAT-000016 (nueva cantidad: 11)','127.0.0.1','2026-06-11 06:18:00'),(160,1,'CREAR','ORDENES','Orden creada ID: 15 para cliente: J-55656666-5','127.0.0.1','2026-06-11 06:19:53'),(161,1,'CREAR','CREDITO','Credito registrado orden: 15','127.0.0.1','2026-06-11 06:19:53'),(162,1,'CREAR','CREDITO','Abono registrado credito: 5 por $40.00','127.0.0.1','2026-06-11 06:19:54'),(163,1,'CREAR','CREDITO','Abono registrado credito: 5 por $60.00','127.0.0.1','2026-06-11 06:19:54'),(164,1,'MODIFICAR','CREDITO','Credito pagado orden: 15','127.0.0.1','2026-06-11 06:19:54'),(165,4,'CREAR','ORDENES','Orden registrada ID: 16','127.0.0.1','2026-06-11 07:00:35'),(166,4,'CREAR','QR','Codigo QR creado: factura','127.0.0.1','2026-06-11 07:00:35'),(167,1,'CREAR','PAGOS','Comprobante de pago registrado orden ID: 16','127.0.0.1','2026-06-11 07:00:35'),(168,1,'MODIFICAR','ESCANER','Solicitud validacion ID 3 respondida como aprobada','127.0.0.1','2026-06-11 07:00:35'),(169,1,'MODIFICAR','INVENTARIO','Inventario modificado: BAT-000016 (nueva cantidad: 9)','127.0.0.1','2026-06-11 07:00:35'),(170,1,'MODIFICAR','ORDENES','Orden modificada ID: 16','127.0.0.1','2026-06-11 07:00:35'),(171,1,'aceptado','PAGOS','Comprobante de pago orden ID: 16 Estado: verificado','127.0.0.1','2026-06-11 07:00:35'),(172,1,'MODIFICAR','ORDENES','Orden modificada ID: 16','127.0.0.1','2026-06-11 07:00:35'),(173,1,'MODIFICAR','INVENTARIO','Inventario modificado: BAT-000016 (nueva cantidad: 11)','127.0.0.1','2026-06-11 07:00:35'),(174,1,'MODIFICAR','ORDENES','Orden modificada ID: 16','127.0.0.1','2026-06-11 07:00:35'),(175,1,'MODIFICAR','ORDENES','Orden modificada ID: 16','127.0.0.1','2026-06-11 07:00:35'),(176,4,'CREAR','ORDENES','Orden registrada ID: 17','127.0.0.1','2026-06-11 07:00:35'),(177,4,'CREAR','QR','Codigo QR creado: factura','127.0.0.1','2026-06-11 07:00:35'),(178,1,'CREAR','PAGOS','Comprobante de pago registrado orden ID: 17','127.0.0.1','2026-06-11 07:00:35'),(179,1,'rechazado','PAGOS','Comprobante de pago orden ID: 17 Estado: rechazado','127.0.0.1','2026-06-11 07:00:35'),(180,1,'MODIFICAR','ORDENES','Orden modificada ID: 17','127.0.0.1','2026-06-11 07:00:35'),(181,1,'CREAR','ORDEN_COMPRA','Orden de compra creada ID: 2','127.0.0.1','2026-06-11 07:01:22'),(182,1,'MODIFICAR','ORDEN_COMPRA','Orden de compra modificada ID: 2','127.0.0.1','2026-06-11 07:01:22'),(183,1,'CREAR','CLIENTES','Cliente registrado: V-99887766','127.0.0.1','2026-06-11 07:01:22'),(184,1,'CREAR','CLIENTES','Cliente registrado: J-99887766-1','127.0.0.1','2026-06-11 07:01:22'),(185,1,'CREAR','EMPRESAS','Empresa registrada id cliente: 17','127.0.0.1','2026-06-11 07:01:22'),(186,1,'CREAR','SERVICIOS','Servicio creado: Servicio E2E 002','127.0.0.1','2026-06-11 07:01:22'),(187,4,'CREAR','TICKETS','Ticket creado ID: 5','127.0.0.1','2026-06-11 07:01:22'),(188,1,'MODIFICAR','TICKETS','Ticket modificado ID: 5','127.0.0.1','2026-06-11 07:01:22'),(189,1,'CREAR','TICKETS','Respuesta a ticket registrada para ticket ID: 5','127.0.0.1','2026-06-11 07:01:22');
/*!40000 ALTER TABLE `bitacora` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `eventos_sistema`
--

DROP TABLE IF EXISTS `eventos_sistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `eventos_sistema` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `accion` varchar(50) NOT NULL,
  `modulo` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `ip` varchar(45) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `eventos_sistema_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `eventos_sistema`
--

LOCK TABLES `eventos_sistema` WRITE;
/*!40000 ALTER TABLE `eventos_sistema` DISABLE KEYS */;
INSERT INTO `eventos_sistema` VALUES (1,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-06-06 20:51:08'),(2,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-06-06 20:51:11'),(3,1,'LOGOUT','AUTH','Cierre de sesion','127.0.0.1','2026-06-06 20:51:14'),(4,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-06-06 20:52:32'),(5,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-06-10 20:42:35'),(6,1,'LOGIN','AUTH','Inicio de sesion: admin@transalca.com','127.0.0.1','2026-06-11 03:28:46');
/*!40000 ALTER TABLE `eventos_sistema` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_eventos_sistema_insert` AFTER INSERT ON `eventos_sistema` FOR EACH ROW BEGIN
        INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (NEW.usuario_id, NEW.accion, NEW.modulo, NEW.descripcion, NEW.ip);
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `permisos`
--

DROP TABLE IF EXISTS `permisos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `permisos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `rol_id` int(11) NOT NULL,
  `modulo` varchar(100) NOT NULL,
  `crear` tinyint(1) DEFAULT 0,
  `leer` tinyint(1) DEFAULT 0,
  `actualizar` tinyint(1) DEFAULT 0,
  `eliminar` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_rol_modulo` (`rol_id`,`modulo`),
  CONSTRAINT `permisos_ibfk_1` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=74 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `permisos`
--

LOCK TABLES `permisos` WRITE;
/*!40000 ALTER TABLE `permisos` DISABLE KEYS */;
INSERT INTO `permisos` VALUES (1,1,'usuarios',1,1,1,1),(2,1,'roles',1,1,1,1),(3,1,'productos',1,1,1,1),(4,1,'categorias',1,1,1,1),(5,1,'marcas',1,1,1,1),(6,1,'proveedores',1,1,1,1),(7,1,'mecanicos',1,1,1,1),(8,1,'stock',1,1,1,1),(9,1,'servicios',1,1,1,1),(10,1,'promociones',1,1,1,1),(11,1,'ordenes',1,1,1,1),(12,1,'pagos',1,1,1,1),(13,1,'bitacora',0,1,0,0),(14,1,'reportes',0,1,0,0),(15,1,'respaldos',1,1,0,0),(16,1,'qr',1,1,1,1),(17,1,'sucursales',1,1,1,1),(18,1,'vehiculos',1,1,1,1),(19,1,'comisiones',1,1,1,1),(20,1,'tickets',1,1,1,1),(21,1,'notificaciones',1,1,1,1),(23,1,'tasas_avanzadas',1,1,1,1),(25,1,'filtros',1,1,1,1),(26,2,'productos',0,1,0,0),(27,2,'categorias',0,1,0,0),(28,2,'marcas',0,1,0,0),(29,2,'stock',0,1,1,0),(30,2,'servicios',0,1,1,0),(31,2,'ordenes',1,1,1,0),(32,2,'pagos',0,1,1,0),(33,2,'reportes',0,1,0,0),(34,3,'vehiculos',1,1,1,0),(35,3,'tickets',1,1,0,0),(36,3,'notificaciones',0,1,1,0),(38,4,'servicios',0,1,1,0),(39,4,'mecanicos',0,1,0,0),(40,4,'ordenes',0,1,0,0),(41,4,'vehiculos',0,1,0,0),(42,4,'comisiones',0,1,0,0),(43,4,'tickets',0,1,1,0),(44,4,'notificaciones',0,1,1,0),(50,1,'clientes',1,1,1,1),(66,1,'empresas',1,1,1,1),(67,1,'creditos',1,1,1,1),(68,1,'metodos_pago',1,1,1,1),(69,2,'creditos',0,1,1,0),(70,2,'metodos_pago',0,1,0,0),(71,1,'bitacora_vehiculo',1,1,1,1),(72,3,'bitacora_vehiculo',1,1,1,0),(73,4,'bitacora_vehiculo',0,1,0,0);
/*!40000 ALTER TABLE `permisos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `roles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'Administrador','Acceso total al sistema',1,'2026-04-30 04:16:33'),(2,'Vendedor','Acceso a ventas e inventario',1,'2026-04-30 04:16:33'),(3,'Cliente','Acceso al portal de compras',1,'2026-04-30 04:16:33'),(4,'Mecanico','Acceso a servicios asignados y comisiones',1,'2026-04-30 04:16:33'),(6,'Supervisor afahcceccj','Rol operativo',1,'2026-05-08 02:42:30'),(7,'Rol afahcceddi','Desc',1,'2026-05-08 02:43:38');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_roles_insert` AFTER INSERT ON `roles` FOR EACH ROW BEGIN
        INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'ROLES', CONCAT('Rol creado: ', NEW.nombre), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_roles_update` AFTER UPDATE ON `roles` FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'ROLES', CONCAT('Rol desactivado: ', NEW.nombre), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'ROLES', CONCAT('Rol modificado: ', OLD.nombre, ' -> ', NEW.nombre), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `tokens_recuperacion`
--

DROP TABLE IF EXISTS `tokens_recuperacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tokens_recuperacion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `token` varchar(255) NOT NULL,
  `expira` datetime NOT NULL,
  `usado` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `tokens_recuperacion_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tokens_recuperacion`
--

LOCK TABLES `tokens_recuperacion` WRITE;
/*!40000 ALTER TABLE `tokens_recuperacion` DISABLE KEYS */;
/*!40000 ALTER TABLE `tokens_recuperacion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario_rol`
--

DROP TABLE IF EXISTS `usuario_rol`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `usuario_rol` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `rol_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_usuario_rol` (`usuario_id`,`rol_id`),
  KEY `rol_id` (`rol_id`),
  CONSTRAINT `usuario_rol_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `usuario_rol_ibfk_2` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario_rol`
--

LOCK TABLES `usuario_rol` WRITE;
/*!40000 ALTER TABLE `usuario_rol` DISABLE KEYS */;
INSERT INTO `usuario_rol` VALUES (1,1,1),(4,4,3),(6,7,7);
/*!40000 ALTER TABLE `usuario_rol` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `cedula` varchar(20) NOT NULL,
  `cedula_prefijo` varchar(2) DEFAULT NULL,
  `email` varchar(150) NOT NULL,
  `telefono` varchar(20) NOT NULL,
  `direccion` text DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `tipo` varchar(20) NOT NULL DEFAULT 'cliente',
  `foto_perfil` varchar(255) DEFAULT 'default.png',
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `cedula` (`cedula`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Admin','Sistema','V-00000000','V','admin@transalca.com','0424-0000000','Oficina Principal','scrypt:32768:8:1$NP7iU10YgSPJPmAh$a2320143ce75e7daa2bf829c27fde8a333c63b4f7b39ebd454d526818ae66be465d09334da3fd829335a11f6a7ff2ef3281c89929f965754d79d22a5f74d8f37','empleado','user_1_1780439124.webp',1,'2026-04-30 04:16:34','2026-06-02 22:25:24'),(4,'Orlando','Barrientos','30396029','V','orlandoabarrientos@gmail.com','04122397209','','scrypt:32768:8:1$68Kr0drnjC2wTNd6$b8eac837132f34bebeb3290e69c00855df6785d8ae3af6b0293111c1413cdf4ceab80db2161414f8509389408724d063c2bbc08fa2bbe485459586279fc5a4b3','cliente','default.png',1,'2026-05-01 01:36:53','2026-05-28 14:51:33'),(6,'Usuario','Prueba','V-07224102','V','user0507224100@mail.com','04121234567','Dir user','scrypt:32768:8:1$hcwaG7r3fLGZYhh1$7b584789708b8dbc83e3562c72acd3db87018d74c2b240f68d21d2379552290afa7af4f4c9745085a42f2408547b45de0937bacef12c6144a2fddc0881e466f5','empleado','default.png',1,'2026-05-08 02:41:01','2026-05-28 14:51:33'),(7,'Lucia','Usuario','V-07224352','V','u0507224338@mail.com','04121234567','Dir','scrypt:32768:8:1$wOZFdyFaCU7k04DK$3b6411f04509e6bd12f4f7a9fb0b7cc13a82bdbf7a323b046cb75473bbd4a55f2763ad3d68561524784488d8ada52968ee053d9faa6854e1af67887abe77f5c9','empleado','default.png',1,'2026-05-08 02:43:38','2026-05-28 14:51:33');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_usuario_insert` AFTER INSERT ON `usuarios` FOR EACH ROW BEGIN
        INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'USUARIOS', CONCAT('Usuario creado: ', NEW.nombre, ' ', NEW.apellido), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_usuario_update` AFTER UPDATE ON `usuarios` FOR EACH ROW BEGIN
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
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Dumping routines for database 'db_mantenimiento'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-11  3:05:19
