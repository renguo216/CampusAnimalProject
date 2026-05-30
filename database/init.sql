CREATE DATABASE  IF NOT EXISTS `campus_animal` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `campus_animal`;
-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: localhost    Database: campus_animal
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `t_adoptionapply`
--

DROP TABLE IF EXISTS `t_adoptionapply`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_adoptionapply` (
  `apply_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '申请单号',
  `pet_id` int NOT NULL COMMENT '领养宠物ID',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '申请人ID',
  `status` int DEFAULT '0' COMMENT '状态：0-审核中，1-通过，2-驳回',
  `content` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '申请理由',
  `review_comment` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审核意见',
  `created_at` datetime DEFAULT NULL COMMENT '申请时间',
  PRIMARY KEY (`apply_id`),
  KEY `fk_adoption_pet` (`pet_id`),
  KEY `fk_adoption_user` (`user_id`),
  CONSTRAINT `fk_adoption_pet` FOREIGN KEY (`pet_id`) REFERENCES `t_animal` (`pet_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_adoption_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='领养申请表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_adoptionapply`
--

LOCK TABLES `t_adoptionapply` WRITE;
/*!40000 ALTER TABLE `t_adoptionapply` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_adoptionapply` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_animal`
--

DROP TABLE IF EXISTS `t_animal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_animal` (
  `pet_id` int NOT NULL AUTO_INCREMENT COMMENT '宠物档案ID',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '宠物名字',
  `breed` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品种',
  `color` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '毛色',
  `vector` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '特征向量（JSON格式）',
  `status` int DEFAULT '0' COMMENT '状态：0-在校，1-已领养，2-需医疗',
  `age` int DEFAULT '0' COMMENT '年龄（单位：月）',
  `gender` tinyint DEFAULT '0' COMMENT '性别：0-未知，1-弟弟，2-妹妹',
  `is_neutered` tinyint DEFAULT '0' COMMENT '是否绝育：0-未知，1-是，2-否',
  `is_vaccinated` tinyint DEFAULT '0' COMMENT '是否疫苗：0-未知，1-是，2-否',
  `personality` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '性格描述（简短）',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '详细描述（故事）',
  `photo_urls` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '照片链接（JSON数组）',
  `found_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发现地点',
  `created_at` datetime DEFAULT NULL COMMENT '档案创建时间',
  PRIMARY KEY (`pet_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='动物档案表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_animal`
--

LOCK TABLES `t_animal` WRITE;
/*!40000 ALTER TABLE `t_animal` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_animal` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_comment`
--

DROP TABLE IF EXISTS `t_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_comment` (
  `comment_id` int NOT NULL AUTO_INCREMENT COMMENT '评论ID',
  `post_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联帖子ID',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '评论人ID',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '评论内容',
  `parent_comment_id` int DEFAULT NULL COMMENT '父评论ID（实现楼中楼回复）',
  `like_count` int DEFAULT '0' COMMENT '点赞数',
  `created_at` datetime DEFAULT NULL COMMENT '评论时间',
  PRIMARY KEY (`comment_id`),
  KEY `fk_comment_post` (`post_id`),
  KEY `fk_comment_user` (`user_id`),
  KEY `fk_comment_parent` (`parent_comment_id`),
  CONSTRAINT `fk_comment_parent` FOREIGN KEY (`parent_comment_id`) REFERENCES `t_comment` (`comment_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_comment_post` FOREIGN KEY (`post_id`) REFERENCES `t_post` (`post_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_comment_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_comment`
--

LOCK TABLES `t_comment` WRITE;
/*!40000 ALTER TABLE `t_comment` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_donation`
--

DROP TABLE IF EXISTS `t_donation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_donation` (
  `donation_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '捐赠单号',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '捐款人ID',
  `project_id` int NOT NULL COMMENT '募捐项目ID',
  `amount` decimal(10,2) NOT NULL COMMENT '捐赠金额',
  `created_at` datetime DEFAULT NULL COMMENT '捐款时间',
  `status` tinyint DEFAULT '0' COMMENT '捐赠状态：0-待确认，1-已到账，2-已驳回，3-已取消',
  `reviewed_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审核人ID',
  `reviewed_at` datetime DEFAULT NULL COMMENT '审核时间',
  `review_comment` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审核意见/驳回原因',
  PRIMARY KEY (`donation_id`),
  KEY `fk_donation_user` (`user_id`),
  KEY `fk_donation_project` (`project_id`),
  CONSTRAINT `fk_donation_project` FOREIGN KEY (`project_id`) REFERENCES `t_donation_project` (`project_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_donation_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='捐赠记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_donation`
--

LOCK TABLES `t_donation` WRITE;
/*!40000 ALTER TABLE `t_donation` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_donation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_donation_project`
--

DROP TABLE IF EXISTS `t_donation_project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_donation_project` (
  `project_id` int NOT NULL AUTO_INCREMENT COMMENT '项目ID',
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '项目标题',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '项目描述',
  `target_amount` decimal(10,2) NOT NULL COMMENT '目标金额',
  `current_amount` decimal(10,2) DEFAULT '0.00' COMMENT '已筹金额',
  `participant_count` int DEFAULT '0' COMMENT '参与人数',
  `status` tinyint DEFAULT '1' COMMENT '状态：0-已结束，1-进行中',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='募捐项目表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_donation_project`
--

LOCK TABLES `t_donation_project` WRITE;
/*!40000 ALTER TABLE `t_donation_project` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_donation_project` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_exchange`
--

DROP TABLE IF EXISTS `t_exchange`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_exchange` (
  `exchange_id` int NOT NULL AUTO_INCREMENT COMMENT '兑换记录ID',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户ID',
  `product_id` int NOT NULL COMMENT '兑换商品ID',
  `points_used` int NOT NULL COMMENT '消耗积分数',
  `status` int DEFAULT '0' COMMENT '状态：0-待发货，1-已完成，2-已取消',
  `created_at` datetime DEFAULT NULL COMMENT '兑换时间',
  `updated_at` datetime DEFAULT NULL COMMENT '最后更新时间',
  `reviewed_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审核人ID',
  `reviewed_at` datetime DEFAULT NULL COMMENT '审核时间',
  `review_comment` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审核意见/拒绝原因',
  `contact_info` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户联系方式',
  PRIMARY KEY (`exchange_id`),
  KEY `fk_exchange_user` (`user_id`),
  KEY `fk_exchange_product` (`product_id`),
  CONSTRAINT `fk_exchange_product` FOREIGN KEY (`product_id`) REFERENCES `t_exchange_product` (`product_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_exchange_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='积分兑换记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_exchange`
--

LOCK TABLES `t_exchange` WRITE;
/*!40000 ALTER TABLE `t_exchange` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_exchange` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_exchange_product`
--

DROP TABLE IF EXISTS `t_exchange_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_exchange_product` (
  `product_id` int NOT NULL AUTO_INCREMENT COMMENT '商品ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '商品描述',
  `points_required` int NOT NULL COMMENT '所需积分',
  `image_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品图片',
  `stock` int DEFAULT '0' COMMENT '库存数量',
  `status` tinyint DEFAULT '1' COMMENT '状态：0-下架，1-上架',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='积分商品表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_exchange_product`
--

LOCK TABLES `t_exchange_product` WRITE;
/*!40000 ALTER TABLE `t_exchange_product` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_exchange_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_follow`
--

DROP TABLE IF EXISTS `t_follow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_follow` (
  `follow_id` int NOT NULL AUTO_INCREMENT COMMENT '关注记录ID',
  `from_user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关注者ID',
  `to_user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '被关注者ID',
  `created_at` datetime DEFAULT NULL COMMENT '关注时间',
  PRIMARY KEY (`follow_id`),
  KEY `fk_follow_from` (`from_user_id`),
  KEY `fk_follow_to` (`to_user_id`),
  CONSTRAINT `fk_follow_from` FOREIGN KEY (`from_user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_follow_to` FOREIGN KEY (`to_user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关注表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_follow`
--

LOCK TABLES `t_follow` WRITE;
/*!40000 ALTER TABLE `t_follow` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_follow` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_like`
--

DROP TABLE IF EXISTS `t_like`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_like` (
  `like_id` int NOT NULL AUTO_INCREMENT COMMENT '点赞记录ID',
  `target_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '点赞目标类型：post-帖子，comment-评论',
  `target_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '点赞目标ID（对应帖子或评论的ID）',
  `target_owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标作者ID（冗余存储，用于性能优化，可选）',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '点赞人ID',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '逻辑删除标记：0-未删除，1-已删除',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',
  PRIMARY KEY (`like_id`),
  KEY `idx_target` (`target_type`,`target_id`,`is_deleted`),
  KEY `fk_like_user` (`user_id`),
  CONSTRAINT `fk_like_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='点赞表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_like`
--

LOCK TABLES `t_like` WRITE;
/*!40000 ALTER TABLE `t_like` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_like` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_notice`
--

DROP TABLE IF EXISTS `t_notice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_notice` (
  `notice_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公告编号',
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公告标题',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '公告内容',
  `is_top` tinyint DEFAULT '0' COMMENT '是否置顶: 0-普通, 1-置顶',
  `created_at` datetime DEFAULT NULL COMMENT '发布时间',
  PRIMARY KEY (`notice_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统公告表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_notice`
--

LOCK TABLES `t_notice` WRITE;
/*!40000 ALTER TABLE `t_notice` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_notice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_points_log`
--

DROP TABLE IF EXISTS `t_points_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_points_log` (
  `log_id` int NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户ID',
  `delta` int NOT NULL COMMENT '积分变动值（可为负）',
  `before_points` int NOT NULL COMMENT '变动前积分',
  `after_points` int NOT NULL COMMENT '变动后积分',
  `reason` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '变动原因',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '变动时间',
  PRIMARY KEY (`log_id`),
  KEY `fk_points_log_user` (`user_id`),
  CONSTRAINT `fk_points_log_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='积分变动日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_points_log`
--

LOCK TABLES `t_points_log` WRITE;
/*!40000 ALTER TABLE `t_points_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_points_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_post`
--

DROP TABLE IF EXISTS `t_post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_post` (
  `post_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '帖子编号',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发帖人ID',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '帖子内容',
  `image_urls` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '图片链接（JSON数组）',
  `like_count` int DEFAULT '0' COMMENT '点赞数',
  `comment_count` int DEFAULT '0' COMMENT '评论数',
  `share_count` int DEFAULT '0' COMMENT '转发/分享数',
  `status` tinyint DEFAULT '1' COMMENT '审核状态：0-待审核，1-已通过，2-驳回',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`post_id`),
  KEY `fk_post_user` (`user_id`),
  CONSTRAINT `fk_post_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区帖子表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_post`
--

LOCK TABLES `t_post` WRITE;
/*!40000 ALTER TABLE `t_post` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_post` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_reimbursement`
--

DROP TABLE IF EXISTS `t_reimbursement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_reimbursement` (
  `reimb_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '报销单号',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '申请人ID',
  `amount` decimal(10,2) NOT NULL COMMENT '申请金额',
  `status` int DEFAULT '0' COMMENT '状态：0-待审，1-通过，2-驳回，3-已撤销',
  `type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '报销类型',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '报销说明',
  `receipt_urls` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '收据图片链接',
  `review_comment` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审核意见',
  `reviewed_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审核人ID',
  `reviewed_at` datetime DEFAULT NULL COMMENT '审核时间',
  `updated_at` datetime DEFAULT NULL COMMENT '最后修改时间',
  `pet_id` int DEFAULT NULL COMMENT '关联动物ID',
  `project_id` int DEFAULT NULL COMMENT '关联募捐项目',
  `created_at` datetime DEFAULT NULL COMMENT '申请时间',
  PRIMARY KEY (`reimb_id`),
  KEY `fk_reimbursement_user` (`user_id`),
  KEY `fk_reimbursement_pet` (`pet_id`),
  KEY `fk_reimbursement_project` (`project_id`),
  CONSTRAINT `fk_reimbursement_pet` FOREIGN KEY (`pet_id`) REFERENCES `t_animal` (`pet_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_reimbursement_project` FOREIGN KEY (`project_id`) REFERENCES `t_donation_project` (`project_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_reimbursement_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报销单表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_reimbursement`
--

LOCK TABLES `t_reimbursement` WRITE;
/*!40000 ALTER TABLE `t_reimbursement` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_reimbursement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_rescuerecord`
--

DROP TABLE IF EXISTS `t_rescuerecord`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_rescuerecord` (
  `record_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '记录编号',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '上报人ID',
  `helper_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '接单志愿者ID（可空）',
  `pet_id` int DEFAULT NULL COMMENT '关联动物ID（可空）',
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '救助标题',
  `location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发现位置（存经纬度或地址）',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '情况说明',
  `status` int DEFAULT '0' COMMENT '状态：0-待接单，1-救助中，2-待确认，3-已完成，4-已关闭',
  `found_location_text` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '前端显示的位置文本',
  `need_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '需求类型',
  `photo_urls` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '救助图片链接（JSON数组）',
  `priority` tinyint DEFAULT '0' COMMENT '优先级：0-普通，1-紧急，2-非常紧急',
  `resolved_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '完成/关闭操作人ID',
  `animal_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '暂时使用的动物名字（未建档前）',
  `location_lat` decimal(10,7) DEFAULT NULL COMMENT '精确纬度',
  `location_lng` decimal(11,8) DEFAULT NULL COMMENT '精确经度',
  `updated_at` datetime DEFAULT NULL COMMENT '最后修改时间',
  `completed_at` datetime DEFAULT NULL COMMENT '救助完成或关闭的时间',
  `is_deleted` tinyint DEFAULT '0' COMMENT '软删除标记：0-未删除，1-已删除',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`record_id`),
  KEY `fk_rescue_user` (`user_id`),
  KEY `fk_rescue_helper` (`helper_id`),
  KEY `fk_rescue_pet` (`pet_id`),
  KEY `fk_rescue_resolved_by` (`resolved_by`),
  CONSTRAINT `fk_rescue_helper` FOREIGN KEY (`helper_id`) REFERENCES `t_user` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_rescue_pet` FOREIGN KEY (`pet_id`) REFERENCES `t_animal` (`pet_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_rescue_resolved_by` FOREIGN KEY (`resolved_by`) REFERENCES `t_user` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_rescue_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='救助记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_rescuerecord`
--

LOCK TABLES `t_rescuerecord` WRITE;
/*!40000 ALTER TABLE `t_rescuerecord` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_rescuerecord` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_user`
--

DROP TABLE IF EXISTS `t_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_user` (
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户唯一ID（微信OpenID）',
  `nickname` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户昵称',
  `avatarURL` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像URL',
  `role` int NOT NULL COMMENT '角色：1-普通用户，2-志愿者，3-管理员',
  `points` int DEFAULT '0' COMMENT '积分（所有用户都有）',
  `volunteer_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '志愿者编号（仅志愿者）',
  `admin_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '管理员工号（仅管理员）',
  `level` int DEFAULT '1' COMMENT '等级（仅志愿者有）',
  `phone_number` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手机号（预留）',
  `like_count` int DEFAULT '0' COMMENT '获赞总数',
  `follower_count` int DEFAULT '0' COMMENT '粉丝数',
  `following_count` int DEFAULT '0' COMMENT '关注数',
  `is_active` tinyint DEFAULT '1' COMMENT '账号是否激活：0-封禁，1-正常',
  `created_at` datetime DEFAULT NULL COMMENT '注册时间',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_user`
--

LOCK TABLES `t_user` WRITE;
/*!40000 ALTER TABLE `t_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `t_volunteer_application`
--

DROP TABLE IF EXISTS `t_volunteer_application`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_volunteer_application` (
  `application_id` int NOT NULL AUTO_INCREMENT COMMENT '申请ID',
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '申请人ID',
  `status` int DEFAULT '0' COMMENT '状态：0-待审核，1-通过，2-驳回',
  `apply_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '申请理由',
  `review_comment` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审核意见',
  `reviewed_by` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审核人ID',
  `reviewed_at` datetime DEFAULT NULL COMMENT '审核时间',
  `updated_at` datetime DEFAULT NULL COMMENT '最后修改时间',
  `created_at` datetime DEFAULT NULL COMMENT '申请时间',
  PRIMARY KEY (`application_id`),
  KEY `fk_volunteer_user` (`user_id`),
  KEY `fk_volunteer_reviewer` (`reviewed_by`),
  CONSTRAINT `fk_volunteer_reviewer` FOREIGN KEY (`reviewed_by`) REFERENCES `t_user` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_volunteer_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='志愿者申请表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `t_volunteer_application`
--

LOCK TABLES `t_volunteer_application` WRITE;
/*!40000 ALTER TABLE `t_volunteer_application` DISABLE KEYS */;
/*!40000 ALTER TABLE `t_volunteer_application` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-31  0:30:29
