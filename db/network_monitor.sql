/*
Navicat MySQL Data Transfer

Source Server         : network_monitor
Source Server Version : 50560
Source Host           : 10.10.150.28:3306
Source Database       : network_monitor

Target Server Type    : MYSQL
Target Server Version : 50560
File Encoding         : 65001

Date: 2018-12-26 16:53:30
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for `history`
-- ----------------------------
DROP TABLE IF EXISTS `history`;
CREATE TABLE `history` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `project` varchar(256) NOT NULL,
  `req_id` varchar(256) NOT NULL,
  `receive_time` datetime NOT NULL,
  `start_time` datetime NOT NULL,
  `stop_time` datetime NOT NULL,
  `network_info` varchar(2048) NOT NULL,
  `vm_info` varchar(2048) NOT NULL,
  `result` varchar(2048) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `project_index` (`project`(255)) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of history
-- ----------------------------

-- ----------------------------
-- Table structure for `item`
-- ----------------------------
DROP TABLE IF EXISTS `item`;
CREATE TABLE `item` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `task_id` int(11) NOT NULL,
  `info` varchar(2048) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `task_id_index` (`task_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of item
-- ----------------------------

-- ----------------------------
-- Table structure for `task`
-- ----------------------------
DROP TABLE IF EXISTS `task`;
CREATE TABLE `task` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `project` varchar(256) NOT NULL,
  `req_id` varchar(256) NOT NULL,
  `status` varchar(32) NOT NULL,
  `receive_time` datetime DEFAULT NULL,
  `start_time` datetime DEFAULT NULL,
  `stop_time` datetime DEFAULT NULL,
  `network_info` varchar(2048) DEFAULT NULL,
  `vm_info` varchar(2048) DEFAULT NULL,
  `vm_num` int(11) DEFAULT NULL,
  `receive_vm_num` int(11) DEFAULT NULL,
  `network_num` int(11) DEFAULT NULL,
  `receive_network_num` int(11) DEFAULT NULL,
  `result` varchar(2048) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `project_name_index` (`project`(255)) USING HASH
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of task
-- ----------------------------
